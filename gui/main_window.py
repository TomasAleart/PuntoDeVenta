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
from exceptions import (
    ProductoNoEncontrado,
    StockInsuficiente,
    StockBajoWarning,
    VentaError,
    PagoInsuficiente,
)
from gui.modificar_item_window import ModificarItemWindow

# ── Constantes de sidebar ──────────────────────────────────────────────────────
_SW_COLLAPSED = 62
_SW_EXPANDED  = 224
_ANIM_STEP    = 14
_ANIM_MS      = 8
_COLLAPSE_MS  = 90


class MainWindow(ctk.CTk):
    """Ventana principal del punto de venta."""

    def __init__(self, usuario: str, jerarquia: str) -> None:
        super().__init__()
        self.usuario   = usuario
        self.jerarquia = jerarquia
        self._servicio = VentaService()

        self._modificadores_carrito: dict[str, dict[str, float]] = {}
        self.title("Minimarket V&E")
        
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

    @property
    def _btn_data(self):
        return [
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
            ("📈", "Estadísticas",    T.NEUTRAL, "#3A4A5E",
             lambda: EstadisticaWindow(self)),
            ("🖨", "Imprimir Ticket", T.NEUTRAL, "#3A4A5E",
             lambda: imprimir_ticket(self._servicio.carrito, self._entrada_descuento))
        ]

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._sidebar_w = _SW_COLLAPSED  # ancho rastreado — no usamos winfo_width()

        # Columna izquierda: sidebar colapsable
        self._sidebar = ctk.CTkFrame(
            self, fg_color=T.SIDEBAR_BG,
            width=_SW_COLLAPSED, corner_radius=0,
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Columna derecha: contenido (expande libremente)
        self._content = ctk.CTkFrame(self, fg_color=T.BG, corner_radius=0)
        self._content.pack(side="right", fill="both", expand=True)

        self._build_sidebar()
        self._build_search()
        self._build_carrito()
        self._build_pago()

    def _build_sidebar(self) -> None:
        # Logo / nombre
        self._lbl_logo = ctk.CTkLabel(
            self._sidebar, text="V&E",
            font=T.F_APP_TITLE, text_color=T.TEXT_ON_DARK,
        )
        self._lbl_logo.pack(pady=(22, 2))

        self._lbl_user = ctk.CTkLabel(
            self._sidebar, text=self.usuario,
            font=T.F_SMALL, text_color=T.SUBTEXT_DARK,
        )
        self._lbl_user.pack(pady=(0, 2))

        ctk.CTkFrame(
            self._sidebar, fg_color=T.SIDEBAR_HOV, height=1,
        ).pack(fill="x", padx=10, pady=10)

        # ── ESPACIADOR SUPERIOR ──────────────────────────────────────────
        # Creamos un frame invisible para empujar los botones hacia abajo
        # Ajustá el 'height' (por ejemplo a 60, 70 u 80) para alinearlo con el carrito
        espaciador_sidebar = ctk.CTkFrame(self._sidebar, height=37, fg_color="transparent")
        espaciador_sidebar.pack(fill="x")
        # ─────────────────────────────────────────────────────────────────

        # Botones
        self._sidebar_btns: list[ctk.CTkButton] = []
        for icon, _label, color, hover, cmd in self._btn_data:
            btn = ctk.CTkButton(
                self._sidebar,
                text=icon, command=cmd,
                fg_color=color, hover_color=hover,
                text_color=T.TEXT_ON_DARK,
                font=T.F_BTN_SIDE,
                anchor="center", height=44, corner_radius=6,
            )
            btn.pack(fill="x", padx=8, pady=3)
            self._sidebar_btns.append(btn)

        # Bind hover en el frame y en cada botón
        self._sidebar.bind("<Enter>", self._on_sidebar_enter)
        self._sidebar.bind("<Leave>", self._on_sidebar_leave)
        for btn in self._sidebar_btns:
            btn.bind("<Enter>", self._on_sidebar_enter)
            btn.bind("<Leave>", self._on_sidebar_leave)

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

        self._entry_codigo = ctk.CTkEntry(
            mid, font=T.F_ENTRY_LG, width=280, justify="center",
            placeholder_text="Ingrese código...",
            fg_color=T.SURFACE, text_color=T.TEXT,
            border_color=T.BORDER, height=44,
        )
        self._entry_codigo.pack(pady=(0, 8))
        self._entry_codigo.bind("<Return>", self._on_procesar_codigo)

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
            img = Image.open(resource_path("LOGO.JPG")).resize((90, 90))
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
        frame.grid_rowconfigure(1, weight=0)
        frame.grid_columnconfigure(0, weight=1)

        # Treeview en row 0 expandible
        tree_wrap = ctk.CTkFrame(frame, fg_color=T.BG, corner_radius=0)
        tree_wrap.grid(row=0, column=0, sticky="nsew")

        cols = ("Código", "Nombre", "Cantidad", "Precio Unit.", "Subtotal")
        self._lista = ttk.Treeview(tree_wrap, columns=cols, show="headings")
        widths = {"Código": 90, "Nombre": 0, "Cantidad": 100, "Precio Unit.": 130, "Subtotal": 160}
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
        # Al final de la configuración de tu Treeview del carrito:
        self._lista.bind("<Double-1>", self._on_carrito_double_click)
        T.tag_rows(self._lista)

    def _build_pago(self) -> None:
        # Separador
        ctk.CTkFrame(
            self._content, fg_color=T.BORDER, height=1, corner_radius=0,
        ).pack(fill="x", padx=16)

        frame_bottom = ctk.CTkFrame(
            self._content, fg_color=T.SURFACE, corner_radius=0, height=170,
        )
        frame_bottom.pack(fill="x", padx=16, pady=(0, 12))
        frame_bottom.pack_propagate(False)

        # Panel izquierdo: totales y campos de entrada
        pago = ctk.CTkFrame(frame_bottom, fg_color=T.SURFACE)
        pago.pack(side="left", padx=28, pady=14, fill = "x", expand=True)
        pago.grid_columnconfigure(2, weight=1)

        # ── FILA 0: DESCUENTO ──
        fuente_labels = (T.F_BODY[0], 16, "bold")

        # ── FILA 0: DESCUENTO ──
        ctk.CTkLabel(
            pago, text="Descuento (%):", font=fuente_labels,text_color=T.TEXT_MUTED, anchor="e",
        ).grid(row=0, column=0, sticky="e", padx=(0, 10), pady=4) # Aumenté un toque el padx a 10
        
        self._entrada_descuento = ctk.CTkEntry(
            pago, font=T.F_ENTRY, width=130, height=40,
            fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
        )
        self._entrada_descuento.grid(row=0, column=1, pady=4)
        self._entrada_descuento.bind("<Return>", self._on_actualizar_descuento)

        # ── FILA 1: PAGO ──
        ctk.CTkLabel(
            pago, text="Pago ($):", font=fuente_labels,text_color=T.TEXT_MUTED, anchor="e",
        ).grid(row=1, column=0, sticky="e", padx=(0, 10), pady=4)
        
        self._entry_pago = ctk.CTkEntry(
            pago, font=T.F_ENTRY, width=130, height=40,
            fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
        )
        self._entry_pago.grid(row=1, column=1, pady=4)
        self._entry_pago.bind("<Return>", self._on_calcular_vuelto)

        # ── FILA 2: VUELTO ──
        # También le podés aplicar la fuente nueva al vuelto si querés que se lea mejor
        self._label_vuelto = ctk.CTkLabel(
            pago, text="", font=fuente_labels, text_color=T.SUCCESS,
        )
        self._label_vuelto.grid(row=2, column=0, columnspan=2, pady=(6, 0), sticky="w")

        fuente_total_grande = (T.F_TOTAL[0], 28, "bold") 

        self._label_total = ctk.CTkLabel(
            pago, text="Total: $0.00", font=fuente_total_grande,text_color=T.TEXT,
        )
        self._label_total.grid(row=0, column=2, rowspan=2, padx=(50, 20), sticky="ns")

        acciones_bottom = ctk.CTkFrame(frame_bottom, fg_color=T.SURFACE)
        acciones_bottom.pack(side="right", padx=28, pady=14, fill="y")

        # Botones de acción 
        self._btn_eliminar_todo = ctk.CTkButton(
            acciones_bottom, text="✕  Eliminar Todo", command=self._on_eliminar_todo,
            font=T.F_BTN, fg_color=T.DANGER, hover_color="#B91C1C",
            text_color=T.TEXT_ON_DARK, height=45, width=180, corner_radius=6,
        )

        self._btn_eliminar_uno = ctk.CTkButton(
            acciones_bottom, text="✂  Eliminar 1", command=self._on_eliminar_uno,
            font=T.F_BTN, fg_color=T.WARNING, hover_color="#B45309",
            text_color=T.TEXT_ON_DARK, height=45, width=180, corner_radius=6,
        )

        self._btn_nueva_compra = ctk.CTkButton(
            acciones_bottom, text="Nueva compra", command=self._on_finalizar_compra,
            font=T.F_BTN, fg_color=T.PRIMARY, hover_color="#1D4ED8",
            text_color=T.TEXT_ON_DARK, height=45, width=180, corner_radius=6,
        )

        # Se ubica al fondo (abajo) del contenedor de acciones usando pack
        self._btn_eliminar_todo.pack(side="left", pady=(7, 15), padx=15)
        self._btn_eliminar_uno.pack(side="left", pady=(7, 15), padx=15)
        self._btn_nueva_compra.pack(side="left", pady=(7, 15), padx=15)
    # ── Sidebar: animación hover ──────────────────────────────────────────────

    def _on_sidebar_enter(self, event=None) -> None:
        if hasattr(self, "_collapse_after"):
            self.after_cancel(self._collapse_after)
            del self._collapse_after
        self._set_sidebar_labels(expanded=True)
        self._animate_sidebar(_SW_EXPANDED)

    def _on_sidebar_leave(self, event=None) -> None:
        if not hasattr(self, "_collapse_after"):
            self._collapse_after = self.after(_COLLAPSE_MS, self._check_collapse)

    def _check_collapse(self) -> None:
        if hasattr(self, "_collapse_after"):
            del self._collapse_after
        px, py = self.winfo_pointerxy()
        sx = self._sidebar.winfo_rootx()
        sy = self._sidebar.winfo_rooty()
        inside = (sx <= px < sx + self._sidebar.winfo_width() and
                  sy <= py < sy + self._sidebar.winfo_height())
        if not inside:
            self._set_sidebar_labels(expanded=False)
            self._animate_sidebar(_SW_COLLAPSED)

    def _animate_sidebar(self, target: int) -> None:
        if hasattr(self, "_anim_after"):
            self.after_cancel(self._anim_after)
        current = self._sidebar_w  # valor rastreado, nunca winfo_width()
        if current == target:
            return
        step = _ANIM_STEP if target > current else -_ANIM_STEP
        next_w = current + step
        if (step > 0 and next_w > target) or (step < 0 and next_w < target):
            next_w = target
        self._sidebar_w = next_w
        self._sidebar.configure(width=next_w)
        if next_w != target:
            self._anim_after = self.after(_ANIM_MS, lambda: self._animate_sidebar(target))

    def _set_sidebar_labels(self, expanded: bool) -> None:
        for btn, (icon, label, *_) in zip(self._sidebar_btns, self._btn_data):
            if expanded:
                btn.configure(text=f"{icon}  {label}", anchor="w")
            else:
                btn.configure(text=icon, anchor="center")

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
                ),
            )

    def _render_total(self) -> None:
        total = self._servicio.total(self._descuento_pct())
        self._label_total.configure(text=f"Total: ${total:.2f}")

    def _descuento_pct(self) -> float:
        try:
            return max(0.0, min(float(self._entrada_descuento.get()), 100.0))
        except ValueError:
            return 0.0

    # ── Handlers de eventos ───────────────────────────────────────────────────

    def _on_procesar_codigo(self, event: object = None) -> None:
        codigo = self._entry_codigo.get().strip()
        if not codigo:
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
            self._entry_codigo.delete(0, "end")
            self._entry_codigo.focus()
            self._label_nombre.configure(text=producto.nombre, text_color=T.TEXT_ON_DARK)
            self._label_precio.configure(text=f"${producto.precio:.2f}")

            if aviso_bajo_stock:
                messagebox.showwarning("Advertencia", aviso_bajo_stock, parent=self)

        except ProductoNoEncontrado:
            self._label_nombre.configure(text="Producto no encontrado", text_color="#FCA5A5")
            self._label_precio.configure(text="")
            self._entry_codigo.delete(0, "end")
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
        try:
            self._servicio.finalizar(self.usuario, self._descuento_pct())
        except VentaError as e:
            messagebox.showwarning("Atención", str(e), parent=self)
            return
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
        self._entry_codigo.focus()

    def _on_carrito_double_click(self, event) -> None:
        """Mapea la fila seleccionada y abre el editor interactuando con el servicio."""
        selection = self._lista.selection()
        if not selection:
            return  # Clic en zona vacía del Treeview
        
        # La clave del diccionario del servicio coincide exactamente con el iid de Tkinter
        clave_carrito = selection[0] 
        
        try:
            # 🏢 Capa lógica: Le pedimos el objeto de negocio al servicio
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
            self._servicio.modificar_item(
                clave=clave_carrito,
                nueva_cantidad=nuevos_valores["cantidad"],
                descuento=nuevos_valores["descuento"],
                recargo=nuevos_valores["recargo"]
            )
            
            # 2. 🎨 Refrescamos TODA la pantalla de forma consistente
            self._render_carrito()  # Vuelve a dibujar el Treeview con los subtotales actualizados y promos
            self._render_total()    # 🌟 CORRECCIÓN: Llama a tu función real que actualiza self._label_total

        except Exception as e:
            # Es buena práctica meter un messagebox acá por si falla algo en la lógica del negocio
            messagebox.showerror("Error", f"No se pudo actualizar el ítem: {e}", parent=self)