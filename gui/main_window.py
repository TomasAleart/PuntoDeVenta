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
from gui.ticket_window import imprimir_ticket
from gui.informe_window import InformeWindow
import gui.theme as T
from exceptions import (
    ProductoNoEncontrado,
    StockInsuficiente,
    StockBajoWarning,
    VentaError,
    PagoInsuficiente,
)

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

        self.title("Minimarket V&E")
        self.state("zoomed")

        T.setup_treeview_style(self)
        self._build_ui()
        CajaInicialWindow(self, usuario)

    # ── Datos del sidebar ─────────────────────────────────────────────────────

    @property
    def _btn_data(self):
        return [
            ("🛒", "Nueva compra",    T.SUCCESS, "#14803E", self._on_finalizar_compra),
            ("🖨", "Imprimir Ticket", T.NEUTRAL, "#3A4A5E",
             lambda: imprimir_ticket(self._servicio.carrito, self._entrada_descuento)),
            ("⚙",  "Gestionar",       T.PRIMARY, "#1D4ED8",
             lambda: GestionWindow(self, self.jerarquia)),
            ("💰", "Arqueo de Caja",  T.NEUTRAL, "#3A4A5E",
             lambda: ArqueoWindow(self, self.usuario)),
            ("✕",  "Eliminar Todo",   T.DANGER,  "#B91C1C", self._on_eliminar_todo),
            ("✂",  "Eliminar 1",      T.WARNING, "#B45309", self._on_eliminar_uno),
            ("📦", "Actualizar Caja", T.NEUTRAL, "#3A4A5E",
             lambda: ActualizarCajaWindow(self, self.usuario)),
            ("📊", "Informe",         T.PRIMARY, "#1D4ED8",
             lambda: InformeWindow(self, self.jerarquia)),
        ]

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
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

        cols = ("Código", "Nombre", "Cantidad", "Precio Unit.", "Subtotal")
        self._lista = ttk.Treeview(frame, columns=cols, show="headings")
        widths = {"Código": 90, "Nombre": 0, "Cantidad": 100, "Precio Unit.": 130, "Subtotal": 160}
        for col in cols:
            self._lista.heading(col, text=col)
            w = widths[col]
            if w:
                self._lista.column(col, anchor="center", width=w, minwidth=60)
            else:
                self._lista.column(col, anchor="w", stretch=True, minwidth=140)

        sb = ttk.Scrollbar(frame, orient="vertical", command=self._lista.yview)
        self._lista.configure(yscrollcommand=sb.set)
        self._lista.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

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

        # Panel izquierdo: totales
        pago = ctk.CTkFrame(frame_bottom, fg_color=T.SURFACE)
        pago.pack(side="left", padx=28, pady=14)

        self._label_total = ctk.CTkLabel(
            pago, text="Total: $0.00", font=T.F_TOTAL, text_color=T.TEXT,
        )
        self._label_total.grid(row=0, column=0, columnspan=2, pady=(0, 8))

        ctk.CTkLabel(
            pago, text="Descuento (%):", font=T.F_BODY,
            text_color=T.TEXT_MUTED, anchor="e",
        ).grid(row=1, column=0, sticky="e", padx=(0, 8))
        self._entrada_descuento = ctk.CTkEntry(
            pago, font=T.F_ENTRY, width=90, height=34,
            fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
        )
        self._entrada_descuento.grid(row=1, column=1)
        self._entrada_descuento.bind("<Return>", self._on_actualizar_descuento)

        ctk.CTkLabel(
            pago, text="Pago ($):", font=T.F_BODY,
            text_color=T.TEXT_MUTED, anchor="e",
        ).grid(row=2, column=0, sticky="e", padx=(0, 8), pady=(6, 0))
        self._entry_pago = ctk.CTkEntry(
            pago, font=T.F_ENTRY, width=90, height=34,
            fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
        )
        self._entry_pago.grid(row=2, column=1, pady=(6, 0))
        self._entry_pago.bind("<Return>", self._on_calcular_vuelto)

        self._label_vuelto = ctk.CTkLabel(
            pago, text="", font=T.F_VUELTO, text_color=T.SUCCESS,
        )
        self._label_vuelto.grid(row=3, column=0, columnspan=2, pady=(8, 0))

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
        current = self._sidebar.winfo_width()
        if current == target:
            return
        step = _ANIM_STEP if target > current else -_ANIM_STEP
        next_w = current + step
        if (step > 0 and next_w > target) or (step < 0 and next_w < target):
            next_w = target
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
                self._servicio.agregar_kg(producto, peso)
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
