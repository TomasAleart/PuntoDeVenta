from __future__ import annotations
import tkinter as tk
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
from exceptions import (
    ProductoNoEncontrado,
    StockInsuficiente,
    StockBajoWarning,
    VentaError,
    PagoInsuficiente,
)


class MainWindow(tk.Tk):
    """Ventana principal del punto de venta."""

    def __init__(self, usuario: str, jerarquia: str) -> None:
        super().__init__()
        self.usuario = usuario
        self.jerarquia = jerarquia
        self._servicio = VentaService()

        self.title("Minimarket V&E")
        self.state("zoomed")
        self.config(bg="#f0f0f0")

        self._build_ui()
        CajaInicialWindow(self, usuario)

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_header()
        self._build_carrito()
        self._build_footer()

    def _build_header(self) -> None:
        frame_top = tk.Frame(self, bg="#f0f0f0", height=220)
        frame_top.pack(fill="x")
        frame_top.pack_propagate(False)
        frame_top.grid_columnconfigure(0, weight=1)
        frame_top.grid_columnconfigure(1, weight=2)
        frame_top.grid_columnconfigure(2, weight=1)

        # Columna izquierda: logo
        frame_left = tk.Frame(frame_top, bg="#f0f0f0")
        frame_left.grid(row=0, column=0, sticky="nw", padx=40, pady=20)
        tk.Label(frame_left, text="Minimarket V&E", font=("Arial", 26, "bold"), bg="#f0f0f0").pack(anchor="center")
        try:
            img = Image.open(resource_path("LOGO.JPG")).resize((150, 150))
            logo_tk = ImageTk.PhotoImage(img)
            lbl = tk.Label(frame_left, image=logo_tk, bg="#f0f0f0")
            lbl.image = logo_tk
            lbl.pack(anchor="center", pady=10)
        except Exception:
            pass

        # Columna central: código + info producto
        frame_mid = tk.Frame(frame_top, bg="#f0f0f0")
        frame_mid.grid(row=0, column=1, sticky="n", pady=20)
        self._entry_codigo = tk.Entry(frame_mid, font=("Arial", 22), width=18, justify="center")
        self._entry_codigo.pack(pady=(10, 10))
        self._entry_codigo.bind("<Return>", self._on_procesar_codigo)
        self._label_nombre = tk.Label(frame_mid, text="", font=("Arial", 16), bg="#f0f0f0")
        self._label_nombre.pack()
        self._label_precio = tk.Label(frame_mid, text="", font=("Arial", 22, "bold"), bg="#f0f0f0")
        self._label_precio.pack()

        # Columna derecha: usuario
        frame_right = tk.Frame(frame_top, bg="#f0f0f0")
        frame_right.grid(row=0, column=2, sticky="ne", padx=40, pady=30)
        tk.Label(
            frame_right,
            text=f"Usuario en uso: {self.usuario} ({self.jerarquia})",
            font=("Arial", 16, "bold"), bg="#f0f0f0", fg="#333",
        ).pack(anchor="e")

    def _build_carrito(self) -> None:
        frame = tk.Frame(self, bg="#f0f0f0")
        frame.pack(fill="both", expand=True)

        cols = ("Código", "Nombre", "Cantidad", "Precio Unit.", "Subtotal")
        self._lista = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            self._lista.heading(col, text=col)
            self._lista.column(col, anchor="center", width=200)
        self._lista.pack(fill="both", expand=True, padx=20, pady=10)

    def _build_footer(self) -> None:
        frame_bottom = tk.Frame(self, bg="#e8e8e8", height=220)
        frame_bottom.pack(fill="x")
        frame_bottom.pack_propagate(False)

        # Panel de totales
        frame_pago = tk.Frame(frame_bottom, bg="#e8e8e8")
        frame_pago.pack(side="left", padx=40, pady=20)

        self._label_total = tk.Label(
            frame_pago, text="Total: $0.00", font=("Arial", 24, "bold"), bg="#e8e8e8",
        )
        self._label_total.grid(row=0, column=0, columnspan=2, pady=10)

        tk.Label(frame_pago, text="Descuento (%):", font=("Arial", 16), bg="#e8e8e8").grid(row=1, column=0)
        self._entrada_descuento = tk.Entry(frame_pago, font=("Arial", 16), width=10)
        self._entrada_descuento.grid(row=1, column=1)
        self._entrada_descuento.bind("<Return>", self._on_actualizar_descuento)

        tk.Label(frame_pago, text="Pago:", font=("Arial", 16), bg="#e8e8e8").grid(row=2, column=0)
        self._entry_pago = tk.Entry(frame_pago, font=("Arial", 16), width=10)
        self._entry_pago.grid(row=2, column=1)
        self._entry_pago.bind("<Return>", self._on_calcular_vuelto)

        self._label_vuelto = tk.Label(
            frame_pago, text="", font=("Arial", 20, "bold"), bg="#e8e8e8", fg="blue",
        )
        self._label_vuelto.grid(row=3, column=0, columnspan=2, pady=10)

        # Botones
        frame_botones = tk.Frame(frame_bottom, bg="#e8e8e8")
        frame_botones.pack(side="right", padx=40)

        botones = [
            ("Nueva compra",    self._on_finalizar_compra,                          "#607D8B"),
            ("Imprimir Ticket", lambda: imprimir_ticket(self._servicio.carrito, self._entrada_descuento), "#607D8B"),
            ("Gestionar",       lambda: GestionWindow(self, self.jerarquia),        "#607D8B"),
            ("Arqueo de Caja",  lambda: ArqueoWindow(self, self.usuario),           "#607D8B"),
            ("Eliminar todo",   self._on_eliminar_todo,                             "#607D8B"),
            ("Eliminar 1",      self._on_eliminar_uno,                              "#607D8B"),
            ("Actualizar Caja", lambda: ActualizarCajaWindow(self, self.usuario),   "#607D8B"),
            ("Informe",         lambda: InformeWindow(self, self.jerarquia),        "#607D8B"),
        ]

        for i, (texto, comando, color) in enumerate(botones):
            tk.Button(
                frame_botones, text=texto, command=comando,
                font=("Arial", 14, "bold"), bg=color, fg="white", width=18, height=2,
            ).grid(row=i // 4, column=i % 4, padx=10, pady=10)

    # ── Renderizado ───────────────────────────────────────────────────────────

    def _render_carrito(self) -> None:
        for i in self._lista.get_children():
            self._lista.delete(i)

        for clave, item in self._servicio.carrito.items():
            if item.tipo == "unidad":
                cantidad_txt = str(item.cantidad)
                precio_txt = f"${item.precio_unitario:.2f}"
            else:
                cantidad_txt = f"{item.peso:.3f} kg"
                precio_txt = f"${item.precio_unitario:.2f} x kg"

            self._lista.insert(
                "", "end", iid=clave,
                values=(
                    item.codigo, item.nombre, cantidad_txt, precio_txt,
                    f"${item.subtotal:.2f} {item.promo or ''}",
                ),
            )

    def _render_total(self) -> None:
        total = self._servicio.total(self._descuento_pct())
        self._label_total.config(text=f"Total: ${total:.2f}")

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
            self._entry_codigo.delete(0, tk.END)
            self._entry_codigo.focus_set()
            self._label_nombre.config(text=producto.nombre, fg="black")
            self._label_precio.config(text=f"${producto.precio:.2f}")

            if aviso_bajo_stock:
                messagebox.showwarning("Advertencia", aviso_bajo_stock, parent=self)

        except ProductoNoEncontrado:
            self._label_nombre.config(text="Producto no encontrado", fg="red")
            self._label_precio.config(text="")
            self._entry_codigo.delete(0, tk.END)
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
            self._label_vuelto.config(
                text=f"VUELTO: ${vuelto:.2f}", fg="blue", font=("Arial", 18, "bold"),
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
        self._entry_pago.delete(0, tk.END)
        self._label_vuelto.config(text="")
        self._label_nombre.config(text="")
        self._label_precio.config(text="")
        self._entrada_descuento.delete(0, tk.END)
        self._entry_codigo.focus_set()
