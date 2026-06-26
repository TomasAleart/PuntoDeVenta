from __future__ import annotations
import customtkinter as ctk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from database.connection import resource_path
from database.productos_db import buscar_producto
from core.venta_service import VentaService                             
from gui.kg_window import KgWindow
from gui.arqueo_window import ArqueoWindow
from gui.caja_window import CajaInicialWindow, ActualizarCajaWindow
from gui.gestion_window import GestionWindow
from gui.promos_window import PromosWindow
from gui.ticket_window import imprimir_ticket
from gui.informe_window import InformeWindow
from gui.estadistica_window import EstadisticaWindow
import gui.theme as T
from gui.widgets.autocomplete_entry import AutoCompleteEntry
from gui.widgets.sidebar import Sidebar # Nueva importación
from exceptions import (
    ProductoNoEncontrado,
    StockInsuficiente,
    StockBajoWarning,
    VentaError,
    PagoInsuficiente,
)
from gui.modificar_item_window import ModificarItemWindow


class MainWindow(ctk.CTk):
    """Ventana principal del punto de venta."""

    def __init__(self, usuario: str, jerarquia: str) -> None:
        super().__init__()
        self.usuario   = usuario
        self.jerarquia = jerarquia
        self._servicio = VentaService()

        self._modificadores_carrito: dict[str, dict[str, float]] = {}
        self.title("Minimarket V&E")
        

        # 📝 VARIABLES PARA VENTA LIBRE / MANUAL
        self.var_libre_desc = ctk.StringVar()
        self.var_libre_monto = ctk.StringVar()

        # 1. Configurar la UI normalmente (sin tocar el estado de la ventana)
        T.setup_treeview_style(self)
        self._build_ui()
        
        # 2. Dejar que la ventana se dibuje en paz. 
        # A los 200ms, cuando ya existe para Windows, la maximizamos y abrimos la caja.
        self.after(200, self._arrancar_interfaz)

    def _arrancar_interfaz(self) -> None:
        """Ejecuta el comportamiento visual una vez que la ventana ya está asentada."""
        self.state("zoomed")  # Al ejecutarse acá, Windows NO la minimiza
        self.lift()           # La trae al frente
        self.focus_force()    # Le da el foco del teclado
        
        # Ahora sí, con la Main Window gigante y fija, clavamos la caja arriba
        CajaInicialWindow(self, self.usuario)

    # ── Datos del sidebar ─────────────────────────────────────────────────────

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Columna izquierda: sidebar colapsable
        self._sidebar = Sidebar(
            self,
            usuario=self.usuario,
            jerarquia=self.jerarquia,
            btn_data=[
                ("⚙",  "Gestionar",       T.NEUTRAL, "#3A4A5E",
                 lambda: GestionWindow(self, self.jerarquia)),
                ("🏷", "Promociones",     T.NEUTRAL, "#3A4A5E",
                 lambda: PromosWindow(self)),
                ("💰", "Arqueo de Caja",  T.NEUTRAL, "#3A4A5E",
                 lambda: ArqueoWindow(self, self.usuario)),
                ("📦", "Actualizar Caja", T.NEUTRAL, "#3A4A5E",
                 lambda: ActualizarCajaWindow(self, self.usuario)),
                ("📊", "Informe",         T.NEUTRAL, "#3A4A5E",
                 lambda: InformeWindow(self, self.jerarquia)),
    #            ("📈", "Estadísticas",    T.NEUTRAL, "#3A4A5E",
    #             lambda: EstadisticaWindow(self)),
                ("🖨", "Imprimir Ticket", T.NEUTRAL, "#3A4A5E",
                 lambda: imprimir_ticket(self._servicio.carrito, self._entrada_descuento))
            ],
            width=_SW_COLLAPSED # Pasa el ancho inicial, el Sidebar lo gestiona internamente
        )

        # Columna derecha: contenido (expande libremente)
        self._content = ctk.CTkFrame(self, fg_color=T.BG, corner_radius=0)
        self._content.pack(side="right", fill="both", expand=True)

        self._build_sidebar()
        self._build_search()
        self._build_carrito()
        self._build_pago()

    def _build_search(self) -> None:
        frame = ctk.CTkFrame(
            self._content, fg_color=T.SIDEBAR_BG,
            height=140, corner_radius=0,
        )
        frame.pack(fill="x")
        frame.pack_propagate(False)
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Centro: campo de código
        mid = ctk.CTkFrame(frame, fg_color=T.SIDEBAR_BG)
        mid.grid(row=0, column=1, sticky="n", pady=18)

        self._autocomplete_entry = AutoCompleteEntry(
            mid,
            on_select_callback=self._on_procesar_codigo_desde_autocomplete,
            font=T.F_ENTRY_LG, width=280,
            fg_color=T.SURFACE, text_color=T.TEXT,
            border_color=T.BORDER, height=44,
        )
        self._autocomplete_entry.pack(pady=(0, 8))

        self._label_nombre = ctk.CTkLabel(
            mid, text="", font=T.F_ENTRY,
            text_color=T.TEXT_ON_DARK,
        )
        self._label_nombre.pack()

        self._label_precio = ctk.CTkLabel(
            mid, text="", font=T.F_PRICE,
            text_color=T.TEXT_ON_DARK,
        )
        self._label_precio.pack()

        # Derecha: usuario
        right = ctk.CTkFrame(frame, fg_color=T.SIDEBAR_BG)
        right.grid(row=0, column=2, sticky="ne", padx=28, pady=20)

        ctk.CTkLabel(
            right, text=f"Usuario: {self.usuario}",
            font=T.F_BODY_B, text_color=T.TEXT_ON_DARK,
        ).pack(anchor="e")
        ctk.CTkLabel(
            right, text=f"({self.jerarquia})",
            font=T.F_SMALL, text_color=T.SUBTEXT_DARK,
        ).pack(anchor="e")

        # Izquierda: logo
        left = ctk.CTkFrame(frame, fg_color=T.SIDEBAR_BG)
        left.grid(row=0, column=0, sticky="nw", padx=28, pady=20)
        try:
            img = Image.open(resource_path("../LOGO.jpg")).resize((90, 90))
            logo_tk = ImageTk.PhotoImage(img)
            lbl = ctk.CTkLabel(left, image=logo_tk, text="")
            lbl.image = logo_tk
            lbl.pack()
        except Exception:
            ctk.CTkLabel(
                left, text="🛒", font=("Segoe UI Emoji", 40),
                text_color=T.TEXT_ON_DARK,
            ).pack()

    def _build_carrito(self) -> None:
        frame = ctk.CTkFrame(self._content, fg_color=T.BG, corner_radius=0)
        frame.pack(fill="both", expand=True, padx=16, pady=(12, 0))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        tree_wrap = ctk.CTkFrame(frame, fg_color=T.BG, corner_radius=0)
        tree_wrap.grid(row=0, column=0, sticky="nsew")

        # 💡 AGREGAMOS LA COLUMNA "Acción" AL FINAL
        cols = ("Código", "Nombre", "Cantidad", "Precio Unit.", "Subtotal", "Acción")
        self._lista = ttk.Treeview(tree_wrap, columns=cols, show="headings")
        
        widths = {"Código": 90, "Nombre": 0, "Cantidad": 100, "Precio Unit.": 130, "Subtotal": 160, "Acción": 90}
        
        for col in cols:
            self._lista.heading(col, text=col)
            w = widths[col]
            if w:
                self._lista.column(col, anchor="center", width=w, minwidth=60)
            else:
                self._lista.column(col, anchor="w", stretch=True, minwidth=140)

        sb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self._lista.yview)
        self._lista.configure(yscrollcommand=sb.set)
        self._lista.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        # Binds de interacción
        self._lista.bind("<Double-1>", self._on_carrito_double_click)
        self._lista.bind("<ButtonRelease-1>", self._on_carrito_click) # 💡 NUEVO BIND PARA DETECTAR EL CLIC EN EL "X"
        T.tag_rows(self._lista)

    def _build_pago(self) -> None:
        # Separador superior
        ctk.CTkFrame(
            self._content, fg_color=T.BORDER, height=1, corner_radius=0,
        ).pack(fill="x", padx=16)

        # Contenedor principal de la sección inferior
        frame_bottom = ctk.CTkFrame(
            self._content, fg_color=T.SURFACE, corner_radius=0, height=220,
        )
        frame_bottom.pack(fill="x", padx=16, pady=(0, 12))
        frame_bottom.pack_propagate(False)

        # ── 📐 REGLA DE SIMETRÍA: 4 Columnas con el mismo ancho exacto ──
        for col in range(4):
            frame_bottom.grid_columnconfigure(col, weight=1, uniform="columna_baja")
        
        # Centrado vertical de las filas principales
        frame_bottom.grid_rowconfigure(0, weight=1)
        frame_bottom.grid_rowconfigure(1, weight=1)

        fuente_labels = (T.F_BODY[0], 15, "bold")


        # ── 📦 COLUMNA 0: DESCUENTO Y PAGO (Cierres) ──
        col_cierre = ctk.CTkFrame(frame_bottom, fg_color="transparent")
        col_cierre.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=20, pady=20)
        col_cierre.grid_columnconfigure(1, weight=1)

        # Descuento
        ctk.CTkLabel(col_cierre, text="Desc. (%):", font=fuente_labels, text_color=T.TEXT_MUTED, anchor="e").grid(row=0, column=0, sticky="e", padx=(0, 10), pady=6)
        self._entrada_descuento = ctk.CTkEntry(col_cierre, font=T.F_ENTRY, height=40, fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT)
        self._entrada_descuento.grid(row=0, column=1, sticky="ew", pady=6)
        self._entrada_descuento.bind("<Return>", self._on_actualizar_descuento)

        # Pago
        ctk.CTkLabel(col_cierre, text="Pago ($):", font=fuente_labels, text_color=T.TEXT_MUTED, anchor="e").grid(row=1, column=0, sticky="e", padx=(0, 10), pady=6)
        self._entry_pago = ctk.CTkEntry(col_cierre, font=T.F_ENTRY, height=40, fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT)
        self._entry_pago.grid(row=1, column=1, sticky="ew", pady=6)
        self._entry_pago.bind("<Return>", self._on_calcular_vuelto)

        # Vuelto
        self._label_vuelto = ctk.CTkLabel(col_cierre, text="", font=(T.F_BODY[0], 14, "bold"), text_color=T.SUCCESS, anchor="w")
        self._label_vuelto.grid(row=2, column=1, sticky="w", pady=(2, 0))


        # ── 📦 COLUMNA 1: EL TOTAL CENTRADO GIGANTE (MÁS GRANDE NOW 🚀) ──
        col_total = ctk.CTkFrame(frame_bottom, fg_color="transparent")
        col_total.grid(row=0, column=1, rowspan=2, sticky="nsew", pady=20)
        
        # Subimos de 44 a 54 para que domine por completo el centro del panel
        fuente_total_imponente = (T.F_TOTAL[0], 38, "bold")
        self._label_total = ctk.CTkLabel(
            col_total, text="Total: $0.00", 
            font=fuente_total_imponente, 
            text_color=T.TEXT, anchor="center"
        )
        self._label_total.pack(expand=True, fill="both")


        # ── 📦 COLUMNA 2: CAMPOS DE PRODUCTO LIBRE ──
        col_libre = ctk.CTkFrame(frame_bottom, fg_color="transparent")
        col_libre.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=20, pady=20)
        col_libre.grid_columnconfigure(1, weight=1)

        # Descripción Libre
        ctk.CTkLabel(col_libre, text="Desc. Libre:", font=fuente_labels, text_color=T.TEXT_MUTED, anchor="e").grid(row=0, column=0, sticky="e", padx=(0, 10), pady=6)
        self._entry_libre_desc = ctk.CTkEntry(col_libre, font=T.F_ENTRY, height=40, textvariable=self.var_libre_desc, fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT)
        self._entry_libre_desc.grid(row=0, column=1, sticky="ew", pady=6)

        # Monto Libre
        ctk.CTkLabel(col_libre, text="Monto ($):", font=fuente_labels, text_color=T.TEXT_MUTED, anchor="e").grid(row=1, column=0, sticky="e", padx=(0, 10), pady=6)
        self._entry_libre_monto = ctk.CTkEntry(col_libre, font=T.F_ENTRY, height=40, textvariable=self.var_libre_monto, fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT)
        self._entry_libre_monto.grid(row=1, column=1, sticky="ew", pady=6)

        # Botón + Agregar
        self._btn_agregar_libre = ctk.CTkButton(
            col_libre, text="+ Agregar Producto", command=self._on_agregar_item_libre,
            font=T.F_BTN, fg_color="#10B981", hover_color="#059669",
            text_color=T.TEXT_ON_DARK, height=38, corner_radius=6,
        )
        self._btn_agregar_libre.grid(row=2, column=1, sticky="ew", pady=(4, 0))


        # ── 📦 COLUMNA 3: BOTÓN DE NUEVA COMPRA (MÁS CHICO ⚙️) ──
        col_finalizar = ctk.CTkFrame(frame_bottom, fg_color="transparent")
        col_finalizar.grid(row=0, column=3, rowspan=2, sticky="nsew", padx=20, pady=20)
        
        # Bajamos la fuente de los botones estándar a una un poco más chica (ej. 14) 
        # y reducimos la altura a 80 para que no sea un bloque tan invasivo.
        fuente_btn_chico = (T.F_BTN[0], 14, "bold")

        self._btn_nueva_compra = ctk.CTkButton(
            col_finalizar, text="✓ Finalizar Venta", command=self._on_finalizar_compra,
            font=fuente_btn_chico, fg_color=T.PRIMARY, hover_color="#1D4ED8",
            text_color=T.TEXT_ON_DARK, height=50, corner_radius=6,
        )

        self._btn_nueva_compra.pack(expand=True, fill="x", pady=6)

    # ── Renderizado ───────────────────────────────────────────────────────────

    def _render_carrito(self) -> None:
        for i in self._lista.get_children():
            self._lista.delete(i)

        for idx, (clave, item) in enumerate(self._servicio.carrito.items()):
            if item.tipo == "unidad":
                cantidad_txt = str(item.cantidad)
                precio_txt   = f"${item.precio_unitario:.2f}"
            else:
                cantidad_txt = f"{item.peso:.3f} kg"
                precio_txt   = f"${item.precio_unitario:.2f} x kg"

            tag = "odd" if idx % 2 else "even"
            self._lista.insert(
                "", "end", iid=clave, tags=(tag,),
                values=(
                    item.codigo, item.nombre, cantidad_txt, precio_txt,
                    f"${item.subtotal:.2f} {item.promo or ''}",
                    "✕ Quitar"  # 💡 Texto que simula el botón de borrado en la fila
                ),
            )

    def _on_carrito_click(self, event) -> None:
        """Detecta si el usuario hizo clic específicamente en la columna 'Acción' para borrar."""
        region = self._lista.identify_region(event.x, event.y)
        if region == "cell":
            column = self._lista.identify_column(event.x)
            item_id = self._lista.identify_row(event.y)
            
            # La columna "Acción" es la #6 en el Treeview
            if column == "#6" and item_id:
                try:
                    # Ejecutamos tu lógica existente de eliminar completo para esa fila
                    self._servicio.eliminar_completo(item_id)
                    self._render_carrito()
                    self._render_total()
                except Exception as e:
                    messagebox.showwarning("Atención", str(e), parent=self)

    def _render_total(self) -> None:
        total = self._servicio.total(self._descuento_pct())
        self._label_total.configure(text=f"Total: ${total:.2f}")

    def _descuento_pct(self) -> float:
        try:
            return max(0.0, min(float(self._entrada_descuento.get()), 100.0))
        except ValueError:
            return 0.0

    # ── Handlers de eventos ───────────────────────────────────────────────────

    def _on_procesar_codigo_desde_autocomplete(self, codigo: str) -> None:
        if not codigo: # Por si el callback se dispara con un string vacío
            return

        try:
            producto = buscar_producto(codigo)
            if not producto:
                raise ProductoNoEncontrado(codigo)

            aviso_bajo_stock: str | None = None

            if producto.es_por_peso:
                win = KgWindow(self, producto.precio_kg_float, codigo)
                if win.result is None:
                    return
                peso, _ = win.result
                try:
                    self._servicio.agregar_kg(producto, peso)
                except StockBajoWarning as e:
                    aviso_bajo_stock = str(e)
            else:
                try:
                    self._servicio.agregar_unidad(producto)
                except StockBajoWarning as e:
                    aviso_bajo_stock = str(e)

            self._render_carrito()
            self._render_total()
            self._autocomplete_entry.clear()
            self._autocomplete_entry.focus()
            self._label_nombre.configure(text=producto.nombre, text_color=T.TEXT_ON_DARK)
            self._label_precio.configure(text=f"${producto.precio:.2f}")

            if aviso_bajo_stock:
                messagebox.showwarning("Advertencia", aviso_bajo_stock, parent=self)

        except ProductoNoEncontrado:
            self._label_nombre.configure(text="Producto no encontrado", text_color="#FCA5A5")
            self._label_precio.configure(text="")
            self._autocomplete_entry.clear() # Limpia el campo si no se encuentra el producto
        except StockInsuficiente as e:
            messagebox.showwarning("Sin stock", str(e), parent=self)

    def _on_actualizar_descuento(self, event: object = None) -> None:
        self._render_total()

    def _on_calcular_vuelto(self, event: object = None) -> None:
        try:
            vuelto = self._servicio.calcular_vuelto(
                self._entry_pago.get(), self._descuento_pct(),
            )
            self._render_total()
            self._label_vuelto.configure(
                text=f"VUELTO: ${vuelto:.2f}",
                text_color=T.SUCCESS, font=T.F_VUELTO,
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)
        except PagoInsuficiente as e:
            messagebox.showwarning("Atención", str(e), parent=self)

    def _on_finalizar_compra(self) -> None:
        # 1. Validar el pago antes de finalizar la venta
        try:
            pago_str = self._entry_pago.get()
            descuento_pct = self._descuento_pct()
            
            # Intentar calcular el vuelto para validar el pago
            # Esto lanzará ValueError o PagoInsuficiente si hay un problema
            vuelto = self._servicio.calcular_vuelto(pago_str, descuento_pct)
            
            # Si el cálculo del vuelto es exitoso, actualizamos la UI con el vuelto
            self._label_vuelto.configure(
                text=f"VUELTO: ${vuelto:.2f}",
                text_color=T.SUCCESS, font=T.F_VUELTO,
            )
            
            # Si el pago es válido, se procede a finalizar la venta
            self._servicio.finalizar(self.usuario, descuento_pct)
            
        except ValueError as e:
            messagebox.showerror("Error de Pago", str(e), parent=self)
            return
        except PagoInsuficiente as e:
            messagebox.showwarning("Atención", str(e), parent=self)
            return
        except (VentaError, StockInsuficiente) as e: # Excepciones de negocio ya existentes
            messagebox.showwarning("Atención", str(e), parent=self)
            return
        
        # Si todas las validaciones son correctas y la venta se finaliza
        self._limpiar_pantalla()

    def _on_eliminar_uno(self) -> None:
        seleccion = self._lista.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un producto para eliminar.", parent=self)
            return
        try:
            self._servicio.eliminar_uno(seleccion[0])
        except VentaError as e:
            messagebox.showwarning("Atención", str(e), parent=self)
            return
        self._render_carrito()
        self._render_total()

    def _on_eliminar_todo(self) -> None:
        seleccion = self._lista.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un producto para eliminar.", parent=self)
            return
        try:
            self._servicio.eliminar_completo(seleccion[0])
        except VentaError as e:
            messagebox.showwarning("Atención", str(e), parent=self)
            return
        self._render_carrito()
        self._render_total()
    def _limpiar_pantalla(self) -> None:
        self._servicio.limpiar()
        self._render_carrito()
        self._render_total()
        self._entry_pago.delete(0, "end")
        self._label_vuelto.configure(text="")
        self._label_nombre.configure(text="")
        self._label_precio.configure(text="")
        self._entrada_descuento.delete(0, "end")
        self._autocomplete_entry.focus()

    def _on_carrito_double_click(self, event) -> None:
        """Mapea la fila seleccionada y abre el editor interactuando con el servicio."""
        selection = self._lista.selection()
        if not selection:
            return  # Clic en zona vacía del Treeview
        
        # La clave del diccionario del servicio coincide exactamente con el iid de Tkinter
        clave_carrito = selection[0] 
        
        try:
            # Capa lógica: Le pedimos el objeto de negocio al servicio
            item_negocio = self._servicio.obtener_item(clave_carrito)
            
            # Mapeamos los datos limpios para la interfaz flotante
            item_data = {
                "clave": clave_carrito,
                "nombre": item_negocio.nombre,
                "cantidad": item_negocio.cantidad if item_negocio.tipo == "unidad" else item_negocio.peso,
                "descuento": getattr(item_negocio, "descuento", 0.0),
                "recargo": getattr(item_negocio, "recargo", 0.0)
            }
            
            from gui.modificar_item_window import ModificarItemWindow
            
            # Abrimos la ventana pasándole el callback modular
            ModificarItemWindow(
                parent=self, 
                item_data=item_data, 
                on_guardar=lambda nuevos_valores: self._actualizar_item_carrito(clave_carrito, nuevos_valores)
            )
        except Exception as e:
            # Podés usar tu sistema de alertas visuales habitual acá
            print(f"Error al intentar modificar el ítem: {e}")

    def _actualizar_item_carrito(self, clave_carrito: str, nuevos_valores: dict) -> None:
        """Pura UI: Envía las modificaciones al servicio y refresca la pantalla."""
        try:
            # 1. 🏢 Mandamos a la capa lógica a procesar la matemática del negocio
            # La función modificar_item ahora puede retornar None si el ítem fue eliminado (cantidad 0)
            item_modificado = self._servicio.modificar_item(
                clave=clave_carrito,
                nueva_cantidad=nuevos_valores["cantidad"],
                descuento=nuevos_valores["descuento"],
                recargo=nuevos_valores["recargo"]
            )
            
            # 2. 🎨 Refrescamos TODA la pantalla de forma consistente
            self._render_carrito()  # Vuelve a dibujar el Treeview con los subtotales actualizados y promos
            self._render_total()    # Llama a tu función real que actualiza self._label_total

        except (StockInsuficiente, VentaError) as e: # Capturamos las excepciones específicas que puede lanzar VentaService
            messagebox.showwarning("Atención", str(e), parent=self)
        except Exception as e:
            # Captura cualquier otro error inesperado
            messagebox.showerror("Error", f"No se pudo actualizar el ítem: {e}", parent=self)

