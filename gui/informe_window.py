from __future__ import annotations
from datetime import datetime
from calendar import monthrange
import customtkinter as ctk
from tkinter import ttk, messagebox
from database.informe_db import (
    base_calculo,
    logica_caja_base,
    obtener_informe,
    buscar_id_real,
    eliminar_venta_y_restaurar_stock,  # 🎯 Importación modularizada actualizada
    obtener_detalle,
)
from core.logic_informe import primer_caja, sumar
from reports.informe_report import imprimir_informe
import gui.theme as T


class InformeWindow(ctk.CTkToplevel):
    """Ventana de filtros para generar informes de ventas."""

    def __init__(self, parent: ctk.CTk, jerarquia: str) -> None:
        super().__init__(parent)
        self.title("Informe de Ventas")
        self.geometry("700x460")
        self.resizable(False, False)
        self._jerarquia = jerarquia
        # 1. Hacemos que dependa directamente del padre y bloquee clics accidentales atrás
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
        
        # 2. Aseguramos el foco al final del ciclo de renderizado
        self.update_idletasks()
        self.lift()
        self.focus_force()

    def _build_ui(self) -> None:
        self.configure(fg_color=T.BG)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color=T.SIDEBAR_BG, corner_radius=0, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Informe de Ventas",
            font=T.F_H1, text_color=T.TEXT_ON_DARK,
        ).pack(side="left", padx=20, pady=12)

        # Formulario de filtros
        card = ctk.CTkFrame(self, fg_color=T.SURFACE, corner_radius=8)
        card.grid(row=1, column=0, sticky="ew", padx=20, pady=(16, 10))

        frame = ctk.CTkFrame(card, fg_color=T.SURFACE)
        frame.pack(fill="x", padx=20, pady=16)

        def _make_entry(fila, col, label):
            ctk.CTkLabel(
                frame, text=label, font=T.F_BODY, text_color=T.TEXT_MUTED, anchor="e",
            ).grid(row=fila, column=col, padx=(8, 4), pady=6, sticky="e")
            e = ctk.CTkEntry(
                frame, font=T.F_ENTRY, width=100, height=32,
                fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
            )
            e.grid(row=fila, column=col + 1, padx=(0, 16), pady=6)
            return e

        self._entry_hora_desde  = _make_entry(0, 0, "Hora desde (HH:MM):")
        self._entry_hora_hasta  = _make_entry(0, 2, "Hora hasta (HH:MM):")
        self._entry_dia_desde   = _make_entry(1, 0, "Día desde (DD):")
        self._entry_dia_hasta   = _make_entry(1, 2, "Día hasta (DD):")
        self._entry_mes_desde   = _make_entry(2, 0, "Mes desde (MM):")
        self._entry_mes_hasta   = _make_entry(2, 2, "Mes hasta (MM):")
        self._entry_anio_desde  = _make_entry(3, 0, "Año desde (YYYY):")
        self._entry_anio_hasta  = _make_entry(3, 2, "Año hasta (YYYY):")
        self._entry_vendedor    = _make_entry(4, 0, "Vendedor:")

        # Botón
        ctk.CTkButton(
            self, text="Generar Informe", command=self._generar,
            font=T.F_BTN, fg_color=T.SUCCESS, hover_color="#14803E",
            text_color=T.TEXT_ON_DARK, height=40, width=200, corner_radius=6,
        ).grid(row=2, column=0, pady=16)

    def _generar(self) -> None:
        hora_desde = self._entry_hora_desde.get().strip() or "00:00"
        hora_hasta = self._entry_hora_hasta.get().strip() or "23:59"
        dia_desde  = self._entry_dia_desde.get().strip()  or "01"
        dia_hasta  = self._entry_dia_hasta.get().strip()
        mes_desde  = self._entry_mes_desde.get().strip()  or "01"
        mes_hasta  = self._entry_mes_hasta.get().strip()  or "12"
        anio_desde = self._entry_anio_desde.get().strip() or "0001"
        anio_hasta = self._entry_anio_hasta.get().strip() or "9999"
        vendedor   = self._entry_vendedor.get().strip()

        try:
            # Último día real del mes/año "hasta" (28/29/30/31 según corresponda).
            ultimo_dia_hasta = monthrange(int(anio_hasta), int(mes_hasta))[1]
            # Si no se ingresa día, se toma el último del mes. Si se ingresa uno
            # mayor (ej. 31 en febrero), se acota al último día válido en lugar
            # de dar error: así "hasta fin de mes" no exige saber cuántos días tiene.
            dia_hasta_num = int(dia_hasta) if dia_hasta else ultimo_dia_hasta
            dia_hasta_num = min(dia_hasta_num, ultimo_dia_hasta)

            fecha_desde_dt = datetime(
                int(anio_desde), int(mes_desde), int(dia_desde),
                int(hora_desde[:2]), int(hora_desde[3:]), 0,
            )
            fecha_hasta_dt = datetime(
                int(anio_hasta), int(mes_hasta), dia_hasta_num,
                int(hora_hasta[:2]), int(hora_hasta[3:]), 59,
            )
        except Exception:
            messagebox.showerror("Error", "Fecha u hora inválida.", parent=self)
            return

        fecha_desde = fecha_desde_dt.strftime("%Y-%m-%d %H:%M:%S")
        fecha_hasta = fecha_hasta_dt.strftime("%Y-%m-%d %H:%M:%S")

        eventos = obtener_informe(fecha_desde, fecha_hasta, vendedor)
        if not eventos:
            messagebox.showinfo("Informe", "No hay movimientos en ese período.", parent=self)
            return

        InformeResultadosWindow(self, eventos, fecha_hasta, self._jerarquia)


class InformeResultadosWindow(ctk.CTkToplevel):
    """Muestra los resultados de un informe generado."""

    def __init__(self, parent: ctk.CTk, eventos: list, fecha_hasta: str, jerarquia: str) -> None:
        super().__init__(parent)
        self.title("Resultados del Informe")
        self.geometry("1080x540")
        self._jerarquia = jerarquia
        # 1. Forzar el foco y hacerla modal sobre la ventana de filtros
        self.grab_set()
        self.focus_force()
        
        # 2. Construir la interfaz
        self._build_ui(eventos, fecha_hasta)

    def _build_ui(self, eventos: list, fecha_hasta: str) -> None:
        self.configure(fg_color=T.BG)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color=T.SIDEBAR_BG, corner_radius=0, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Resultados del Informe",
            font=T.F_H1, text_color=T.TEXT_ON_DARK,
        ).pack(side="left", padx=20, pady=12)

        # Tabla
        tframe = ctk.CTkFrame(self, fg_color=T.SURFACE, corner_radius=8)
        tframe.grid(row=1, column=0, sticky="nsew", padx=16, pady=(12, 6))

        inner = ctk.CTkFrame(tframe, fg_color=T.SURFACE)
        inner.pack(fill="both", expand=True, padx=10, pady=10)

        self._tree = ttk.Treeview(
            inner,
            columns=("fecha", "tipo", "detalle", "usuario", "importe"),
            show="headings",
        )
        for col, texto in [
            ("fecha", "Fecha"), ("tipo", "Tipo"), ("detalle", "Detalle"),
            ("usuario", "Usuario"), ("importe", "Importe $"),
        ]:
            self._tree.heading(col, text=texto)
        self._tree.column("importe", anchor="e")
        self._tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(inner, orient="vertical", command=self._tree.yview)
        sb.pack(side="right", fill="y")
        self._tree.configure(yscrollcommand=sb.set)
        T.tag_rows(self._tree)

        caja_inicial_mostrada = primer_caja(eventos)
        row = base_calculo(fecha_hasta)
        fecha_base, caja_base = logica_caja_base(row, caja_inicial_mostrada)
        total_ventas, caja_final = sumar(eventos, fecha_base, caja_base, self._tree)

        # Resumen
        resumen = ctk.CTkFrame(self, fg_color=T.SURFACE, corner_radius=8)
        resumen.grid(row=2, column=0, sticky="ew", padx=16, pady=4)

        inner_r = ctk.CTkFrame(resumen, fg_color=T.SURFACE)
        inner_r.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(inner_r,
            text=f"Caja inicial del período: ${caja_inicial_mostrada:.2f}",
            font=T.F_BODY, text_color=T.TEXT_MUTED,
        ).pack(side="left", padx=(0, 24))
        ctk.CTkLabel(inner_r,
            text=f"Total ventas: ${total_ventas:.2f}",
            font=T.F_BODY_B, text_color=T.TEXT,
        ).pack(side="left", padx=(0, 24))
        ctk.CTkLabel(inner_r,
            text=f"Caja final: ${caja_final:.2f}",
            font=T.F_H1, text_color=T.SUCCESS,
        ).pack(side="left")

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color=T.BG)
        btn_frame.grid(row=3, column=0, pady=12)

        ctk.CTkButton(
            btn_frame, text="Ver detalle", command=self._ver_detalle,
            font=T.F_BTN, fg_color=T.PRIMARY, hover_color="#1D4ED8",
            text_color=T.TEXT_ON_DARK, height=38, width=130, corner_radius=6,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="Imprimir Informe",
            command=lambda: imprimir_informe(self._tree, total_ventas),
            font=T.F_BTN, fg_color=T.NEUTRAL, hover_color="#3A4A5E",
            text_color=T.TEXT_ON_DARK, height=38, width=150, corner_radius=6,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="Eliminar Venta", command=self._eliminar_venta,
            font=T.F_BTN, fg_color=T.DANGER, hover_color="#B91C1C",
            text_color=T.TEXT_ON_DARK, height=38, width=140, corner_radius=6,
        ).pack(side="left", padx=8)

    def _ver_detalle(self) -> None:
        seleccion = self._tree.selection()
        if not seleccion:
            messagebox.showerror("Error", "Seleccione una venta para ver el detalle.", parent=self)
            return

        fecha, tipo, *_ = self._tree.item(seleccion[0])["values"]
        if tipo != "VENTA":
            messagebox.showwarning(
                "Atención",
                "Solo se puede ver el detalle de una venta.\n"
                "Los movimientos de caja no tienen detalle.",
                parent=self,
            )
            return

        row = buscar_id_real(fecha)
        if not row:
            messagebox.showerror("Error", "No se pudo encontrar la venta.", parent=self)
            return

        DetalleVentaWindow(self, fecha, row)

    def _eliminar_venta(self) -> None:
        """Manejador seguro de eliminación de ventas con reincorporación de stock."""
        if self._jerarquia != "admin":
            messagebox.showerror(
                "Permiso denegado",
                "Solo un usuario con jerarquía ADMIN puede eliminar ventas.",
                parent=self,
            )
            return

        seleccion = self._tree.selection()
        if not seleccion:
            messagebox.showerror("Error", "Seleccione una venta para eliminar.", parent=self)
            return

        fecha, tipo, *_ = self._tree.item(seleccion[0])["values"]
        if tipo != "VENTA":
            messagebox.showwarning(
                "Atención",
                "No se pueden eliminar movimientos de caja.\nSolo se pueden eliminar ventas.",
                parent=self,
            )
            return

        if not messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Seguro que desea eliminar la venta del {fecha}?\n\n"
            "Esta acción reincorporará los productos al stock de forma automática.",
            parent=self,
        ):
            return

        row = buscar_id_real(fecha)
        if not row:
            messagebox.showerror("Error", "No se pudo encontrar la venta.", parent=self)
            return

        id_venta = row[0]
        
        # 🎯 DELEGACIÓN ABSOLUTA AL BACKEND TRANSACCIONAL
        if eliminar_venta_y_restaurar_stock(id_venta):
            self._tree.delete(seleccion[0])
            messagebox.showinfo(
                "Éxito", 
                "Venta eliminada correctamente y stock restaurado en el inventario.\n\n"
                "Nota: Para refrescar los totales de caja del resumen, vuelva a generar el informe.", 
                parent=self
            )
        else:
            messagebox.showerror(
                "Error", 
                "No se pudo completar la operación debido a un problema interno de la base de datos.", 
                parent=self
            )


class DetalleVentaWindow(ctk.CTkToplevel):
    """Muestra el detalle de líneas de una venta."""

    def __init__(self, parent: ctk.CTk, fecha: str, row: tuple) -> None:
        super().__init__(parent)
        self.title("Detalle de Venta")
        self.geometry("1200x480")
        self.minsize(960, 480)

        id_venta, total = row
        self._build_ui(fecha, id_venta, float(total))

    def _build_ui(self, fecha: str, id_venta: int, total: float) -> None:
        self.configure(fg_color=T.BG)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header con datos de la venta
        header = ctk.CTkFrame(self, fg_color=T.SIDEBAR_BG, corner_radius=0, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text=f"Venta del {fecha}  ·  Total: ${total:.2f}",
            font=T.F_H1, text_color=T.TEXT_ON_DARK,
        ).pack(side="left", padx=20, pady=12)

        # Tabla
        tframe = ctk.CTkFrame(self, fg_color=T.SURFACE, corner_radius=8)
        tframe.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)

        inner = ctk.CTkFrame(tframe, fg_color=T.SURFACE)
        inner.pack(fill="both", expand=True, padx=10, pady=10)

        tree = ttk.Treeview(
            inner,
            columns=("codigo", "nombre", "cantidad", "precio", "subtotal", "promo"),
            show="headings",
        )

        # 🎯 CONFIGURACIÓN: Todo al centro (Títulos y Datos)
        columnas_config = [
            ("codigo",   "Código",   {"anchor": "center", "width": 140}),
            ("nombre",   "Nombre",   {"anchor": "center", "width": 320}),
            ("cantidad", "Cantidad", {"anchor": "center", "width": 120}),
            ("precio",   "Precio",   {"anchor": "center", "width": 140}),
            ("subtotal", "Subtotal", {"anchor": "center", "width": 140}),
            ("promo",    "Promo",    {"anchor": "center", "width": 130}),
        ]

        for col, texto, kwargs in columnas_config:
            tree.column(col, **kwargs)
            tree.heading(col, text=texto, anchor="center")
            
        tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(inner, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)
        T.tag_rows(tree)

        # RECORRIDO DE DATOS CON FILTRO DE PESO
        for idx, (codigo, nombre, cantidad, peso, precio_unit, subtotal, promo) in enumerate(
            obtener_detalle(id_venta)
        ):
            if peso and peso > 0:
                cantidad_txt = f"{peso:.3f} kg"
                precio_txt   = f"${precio_unit:.2f} x kg"
            else:
                cantidad_txt = str(int(cantidad))
                precio_txt   = f"${precio_unit:.2f}"

            tag = "odd" if idx % 2 else "even"
            tree.insert(
                "", "end", tags=(tag,),
                values=(codigo, nombre, cantidad_txt, precio_txt, f"${subtotal:.2f}", promo or ""),
            )


# ── Función de compatibilidad ─────────────────────────────────────────────────

def abrir_informe(jerarquia: str, parent: ctk.CTk | None = None) -> None:
    import tkinter as tk
    InformeWindow(parent or tk._default_root, jerarquia)