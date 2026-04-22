from __future__ import annotations
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from database.informe_db import (
    base_calculo,
    logica_caja_base,
    obtener_informe,
    buscar_id_real,
    eliminar_detalle,
    obtener_detalle,
)
from core.logic_informe import primer_caja, sumar
from reports.informe_report import imprimir_informe


class InformeWindow(tk.Toplevel):
    """Ventana de filtros para generar informes de ventas."""

    def __init__(self, parent: tk.Misc, jerarquia: str) -> None:
        super().__init__(parent)
        self.title("Informe de Ventas Mensuales")
        self.geometry("650x390")

        self._jerarquia = jerarquia
        self._build_ui()

    def _build_ui(self) -> None:
        frame = tk.Frame(self)
        frame.pack(pady=20)

        campos = [
            ("Hora desde (HH:MM):", 0, 0), ("Hora hasta (HH:MM):", 0, 2),
            ("Día desde (DD):",      1, 0), ("Día hasta (DD):",      1, 2),
            ("Mes desde (MM):",      2, 0), ("Mes hasta (MM):",      2, 2),
            ("Año desde (YYYY):",    3, 0), ("Año hasta (YYYY):",    3, 2),
            ("Vendedor:",            4, 0),
        ]
        entries = {}
        for texto, fila, col in campos:
            clave = texto.split(" ")[0].lower() + "_" + texto.split(" ")[1].lower().rstrip(":")
            tk.Label(frame, text=texto, font=("Arial", 14)).grid(
                row=fila, column=col, padx=10, pady=10, sticky="e",
            )
            entry = tk.Entry(frame, font=("Arial", 14), width=8)
            entry.grid(row=fila, column=col + 1, padx=10, pady=5)
            entries[f"{fila}_{col}"] = entry

        # Asignamos las entradas por posición (fila, col)
        self._entry_hora_desde  = entries["0_0"]
        self._entry_hora_hasta  = entries["0_2"]
        self._entry_dia_desde   = entries["1_0"]
        self._entry_dia_hasta   = entries["1_2"]
        self._entry_mes_desde   = entries["2_0"]
        self._entry_mes_hasta   = entries["2_2"]
        self._entry_anio_desde  = entries["3_0"]
        self._entry_anio_hasta  = entries["3_2"]
        self._entry_vendedor    = entries["4_0"]

        tk.Button(
            self, text="Generar Informe", font=("Arial", 14),
            bg="#4CAF50", fg="white", command=self._generar,
        ).pack(pady=20)

    def _generar(self) -> None:
        hora_desde  = self._entry_hora_desde.get().strip()  or "00:00"
        hora_hasta  = self._entry_hora_hasta.get().strip()  or "23:59"
        dia_desde   = self._entry_dia_desde.get().strip()   or "01"
        dia_hasta   = self._entry_dia_hasta.get().strip()   or "31"
        mes_desde   = self._entry_mes_desde.get().strip()   or "01"
        mes_hasta   = self._entry_mes_hasta.get().strip()   or "12"
        anio_desde  = self._entry_anio_desde.get().strip()  or "0001"
        anio_hasta  = self._entry_anio_hasta.get().strip()  or "9999"
        vendedor    = self._entry_vendedor.get().strip()

        try:
            fecha_desde_dt = datetime(
                int(anio_desde), int(mes_desde), int(dia_desde),
                int(hora_desde[:2]), int(hora_desde[3:]), 0,
            )
            fecha_hasta_dt = datetime(
                int(anio_hasta), int(mes_hasta), int(dia_hasta),
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


class InformeResultadosWindow(tk.Toplevel):
    """Muestra los resultados de un informe generado."""

    def __init__(
        self,
        parent: tk.Misc,
        eventos: list,
        fecha_hasta: str,
        jerarquia: str,
    ) -> None:
        super().__init__(parent)
        self.title("Resultados del Informe")
        self.geometry("1050x500")

        self._jerarquia = jerarquia
        self._build_ui(eventos, fecha_hasta)

    def _build_ui(self, eventos: list, fecha_hasta: str) -> None:
        frame_tabla = tk.Frame(self)
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

        self._tree = ttk.Treeview(
            frame_tabla,
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

        sb = ttk.Scrollbar(frame_tabla, orient="vertical", command=self._tree.yview)
        sb.pack(side="right", fill="y")
        self._tree.configure(yscrollcommand=sb.set)

        caja_inicial_mostrada = primer_caja(eventos)
        row = base_calculo(fecha_hasta)
        fecha_base, caja_base = logica_caja_base(row, caja_inicial_mostrada)
        total_ventas, caja_final = sumar(eventos, fecha_base, caja_base, self._tree)

        frame_resumen = tk.Frame(self)
        frame_resumen.pack(pady=5)
        tk.Label(frame_resumen, text=f"CAJA INICIAL DEL PERÍODO: ${caja_inicial_mostrada:.2f}", font=("Arial", 14)).pack()
        tk.Label(frame_resumen, text=f"TOTAL VENTAS DEL PERÍODO: ${total_ventas:.2f}", font=("Arial", 14)).pack()
        tk.Label(frame_resumen, text=f"CAJA FINAL: ${caja_final:.2f}", font=("Arial", 16, "bold")).pack(pady=5)

        frame_botones = tk.Frame(self)
        frame_botones.pack(pady=15)

        tk.Button(
            frame_botones, text="Ver detalle", font=("Arial", 14), bg="#2196F3", fg="white",
            command=self._ver_detalle,
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            frame_botones, text="Imprimir Informe", font=("Arial", 14), bg="#4CAF50", fg="white",
            command=lambda: imprimir_informe(self._tree, total_ventas),
        ).grid(row=0, column=1, padx=10)

        tk.Button(
            frame_botones, text="Eliminar Venta", font=("Arial", 14), bg="#E53935", fg="white",
            command=self._eliminar_venta,
        ).grid(row=0, column=2, padx=10)

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
            "Confirmar",
            "¿Seguro que desea eliminar esta venta?\nEsta acción no se puede deshacer.",
            parent=self,
        ):
            return

        row = buscar_id_real(fecha)
        if not row:
            messagebox.showerror("Error", "No se pudo encontrar la venta.", parent=self)
            return

        eliminar_detalle(row[0])
        self._tree.delete(seleccion[0])
        messagebox.showinfo("Éxito", "Venta eliminada correctamente.", parent=self)


class DetalleVentaWindow(tk.Toplevel):
    """Muestra el detalle de líneas de una venta."""

    def __init__(self, parent: tk.Misc, fecha: str, row: tuple) -> None:
        super().__init__(parent)
        self.title("Detalle de Venta")
        self.geometry("1200x450")
        self.minsize(950, 450)

        id_venta, total = row
        self._build_ui(fecha, id_venta, float(total))

    def _build_ui(self, fecha: str, id_venta: int, total: float) -> None:
        tk.Label(self, text=f"Fecha: {fecha}", font=("Arial", 14)).pack(pady=5)
        tk.Label(self, text=f"Total: ${total:.2f}", font=("Arial", 14, "bold")).pack(pady=5)

        tree = ttk.Treeview(
            self,
            columns=("codigo", "nombre", "cantidad", "precio", "subtotal", "promo"),
            show="headings",
        )
        tree.pack(fill="both", expand=True)

        for col, texto, kwargs in [
            ("codigo",   "Código",   {}),
            ("nombre",   "Nombre",   {}),
            ("cantidad", "Cantidad", {"anchor": "center"}),
            ("precio",   "Precio",   {"anchor": "e"}),
            ("subtotal", "Subtotal", {"anchor": "e"}),
            ("promo",    "Promo",    {"width": 130}),
        ]:
            tree.heading(col, text=texto)
            tree.column(col, **kwargs)

        for codigo, nombre, cantidad, peso, precio_unit, subtotal, promo in obtener_detalle(id_venta):
            if peso is not None:
                cantidad_txt = f"{peso:.3f} kg"
                precio_txt = f"${precio_unit:.2f} x kg"
            else:
                cantidad_txt = str(int(cantidad))
                precio_txt = f"${precio_unit:.2f}"

            tree.insert(
                "", "end",
                values=(codigo, nombre, cantidad_txt, precio_txt, f"${subtotal:.2f}", promo or ""),
            )


# ── Función de compatibilidad ─────────────────────────────────────────────────

def abrir_informe(jerarquia: str, parent: tk.Misc | None = None) -> None:
    InformeWindow(parent or tk._default_root, jerarquia)
