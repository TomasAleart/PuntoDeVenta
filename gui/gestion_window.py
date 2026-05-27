from __future__ import annotations
import customtkinter as ctk
from tkinter import ttk, messagebox
import difflib
from database.productos_db import (
    eliminar_producto,
    agregar_producto,
    ajustar_precio,
    ajustar_precioKg,
    ajustar_stock,
    obtener_producto_por_codigo,
    obtener_productos,
)
from database.login_db import agregar_usuario, eliminar_usuario_por_nombre, obtener_usuario
from gui.promos_window import PromosWindow
import gui.theme as T
from exceptions import ProductoNoEncontrado, ProductoExistente, UsuarioExistente


def _section(parent, title: str) -> ctk.CTkFrame:
    """Crea un bloque de sección con título y frame de contenido."""
    wrapper = ctk.CTkFrame(parent, fg_color=T.SURFACE, corner_radius=8)
    ctk.CTkLabel(
        wrapper, text=title, font=T.F_H2,
        text_color=T.TEXT_MUTED, anchor="w",
    ).pack(fill="x", padx=14, pady=(10, 0))
    ctk.CTkFrame(wrapper, fg_color=T.BORDER, height=1).pack(fill="x", padx=10, pady=(4, 8))
    content = ctk.CTkFrame(wrapper, fg_color=T.SURFACE)
    content.pack(fill="x", padx=14, pady=(0, 12))
    return content


class GestionWindow(ctk.CTkToplevel):
    """Ventana de gestión de stock, precios y usuarios."""

    def __init__(self, parent: ctk.CTk, jerarquia: str) -> None:
        super().__init__(parent)
        self.state("zoomed")
        self.title("Gestión de Stock y Precios")
        self._jerarquia = jerarquia
        self._build_ui()

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color=T.SIDEBAR_BG, corner_radius=0, height=56)
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="GESTIÓN DE STOCK Y PRECIOS",
            font=T.F_H1, text_color=T.TEXT_ON_DARK,
        ).pack(side="left", padx=24, pady=16)

        # Cuerpo con scroll
        scroll = ctk.CTkScrollableFrame(self, fg_color=T.BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        self._build_tabla(scroll)
        self._build_busqueda(scroll)
        self._build_actualizar(scroll)
        self._build_agregar_producto(scroll)
        self._build_usuarios(scroll)

    def _build_tabla(self, parent) -> None:
        frame = ctk.CTkFrame(parent, fg_color=T.SURFACE, corner_radius=8)
        frame.pack(fill="both", expand=True, padx=16, pady=(12, 6))

        tframe = ctk.CTkFrame(frame, fg_color=T.SURFACE)
        tframe.pack(fill="both", expand=True, padx=10, pady=10)

        columnas = ("codigo", "nombre", "precio", "precio x kg", "stock")
        self._tabla = ttk.Treeview(tframe, columns=columnas, show="headings", height=12)
        for col in columnas:
            self._tabla.heading(col, text=col.capitalize())
            self._tabla.column(col, width=150, anchor="center")
        self._tabla.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(tframe, orient="vertical", command=self._tabla.yview)
        sb.pack(side="right", fill="y")
        self._tabla.configure(yscrollcommand=sb.set)

        T.tag_rows(self._tabla)
        self._refrescar()

    def _build_busqueda(self, parent) -> None:
        frame = ctk.CTkFrame(parent, fg_color=T.SURFACE, corner_radius=8)
        frame.pack(fill="x", padx=16, pady=6)

        inner = ctk.CTkFrame(frame, fg_color=T.SURFACE)
        inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(inner, text="Buscar:", font=T.F_BODY_B, text_color=T.TEXT).pack(side="left", padx=(0, 8))
        self._entry_buscar = ctk.CTkEntry(
            inner, font=T.F_ENTRY, width=320, height=34,
            placeholder_text="Código o nombre del producto...",
            fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
        )
        self._entry_buscar.pack(side="left")
        self._entry_buscar.bind("<KeyRelease>", self._buscar)
        self._entry_buscar.bind("<Return>", self._buscar)

    def _build_actualizar(self, parent) -> None:
        content = _section(parent, "Actualizar producto existente")

        fields = [
            ("Código",          "_entry_cod_upd",       8),
            ("Nuevo precio",    "_entry_precio_upd",    8),
            ("Stock",           "_entry_stock_upd",     8),
            ("Precio x Kg",     "_entry_precio_kg_upd", 8),
        ]
        for col, (label, attr, w) in enumerate(fields):
            ctk.CTkLabel(content, text=label + ":", font=T.F_BODY, text_color=T.TEXT_MUTED).grid(
                row=0, column=col * 2, padx=(8 if col else 0, 4), sticky="e")
            entry = ctk.CTkEntry(
                content, font=T.F_ENTRY, width=w * 14, height=32,
                fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
            )
            entry.grid(row=0, column=col * 2 + 1, padx=(0, 12))
            setattr(self, attr, entry)

        ctk.CTkButton(
            content, text="Actualizar", command=self._actualizar,
            font=T.F_BTN, fg_color=T.PRIMARY, hover_color="#1D4ED8",
            text_color=T.TEXT_ON_DARK, height=34, width=110, corner_radius=6,
        ).grid(row=0, column=8, padx=(4, 0))

    def _build_agregar_producto(self, parent) -> None:
        content = _section(parent, "Agregar / Eliminar producto")

        row0 = [
            ("Código",   "_entry_cod_new",    10),
            ("Nombre",   "_entry_nom_new",    14),
        ]
        row1 = [
            ("Precio",   "_entry_precio_new", 10),
            ("Stock",    "_entry_stock_new",  8),
            ("Precio Kg","_entry_precio_kg_new", 8),
        ]

        for col, (label, attr, w) in enumerate(row0):
            ctk.CTkLabel(content, text=label + ":", font=T.F_BODY, text_color=T.TEXT_MUTED).grid(
                row=0, column=col * 2, padx=(0, 4), sticky="e")
            e = ctk.CTkEntry(content, font=T.F_ENTRY, width=w * 14, height=32,
                             fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT)
            e.grid(row=0, column=col * 2 + 1, padx=(0, 12))
            setattr(self, attr, e)

        for col, (label, attr, w) in enumerate(row1):
            ctk.CTkLabel(content, text=label + ":", font=T.F_BODY, text_color=T.TEXT_MUTED).grid(
                row=1, column=col * 2, padx=(0, 4), pady=(8, 0), sticky="e")
            e = ctk.CTkEntry(content, font=T.F_ENTRY, width=w * 14, height=32,
                             fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT)
            e.grid(row=1, column=col * 2 + 1, padx=(0, 12), pady=(8, 0))
            setattr(self, attr, e)

        # Fila de acciones
        btn_frame = ctk.CTkFrame(content, fg_color=T.SURFACE)
        btn_frame.grid(row=2, column=0, columnspan=8, pady=(10, 0), sticky="w")

        ctk.CTkButton(
            btn_frame, text="Agregar producto", command=self._agregar_producto,
            font=T.F_BTN, fg_color=T.SUCCESS, hover_color="#14803E",
            text_color=T.TEXT_ON_DARK, height=34, width=150, corner_radius=6,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(btn_frame, text="Eliminar código:", font=T.F_BODY, text_color=T.TEXT_MUTED).pack(side="left", padx=(0, 6))
        self._entry_eliminar_cod = ctk.CTkEntry(
            btn_frame, font=T.F_ENTRY, width=120, height=34,
            fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
        )
        self._entry_eliminar_cod.pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_frame, text="Eliminar", command=self._eliminar_producto,
            font=T.F_BTN, fg_color=T.DANGER, hover_color="#B91C1C",
            text_color=T.TEXT_ON_DARK, height=34, width=90, corner_radius=6,
        ).pack(side="left", padx=(0, 20))

        ctk.CTkButton(
            btn_frame, text="Gestionar Promociones", command=lambda: PromosWindow(self),
            font=T.F_BTN, fg_color=T.NEUTRAL, hover_color="#3A4A5E",
            text_color=T.TEXT_ON_DARK, height=34, width=180, corner_radius=6,
        ).pack(side="left")

    def _build_usuarios(self, parent) -> None:
        content = _section(parent, "Agregar nuevo usuario")

        fields_r0 = [("Nombre", "_entry_nomb_new", 12), ("Contraseña", "_entry_contra_new", 12)]
        fields_r1 = [("Jerarquía", "_entry_jerar_new", 12)]

        for col, (label, attr, w) in enumerate(fields_r0):
            ctk.CTkLabel(content, text=label + ":", font=T.F_BODY, text_color=T.TEXT_MUTED).grid(
                row=0, column=col * 2, padx=(0, 4), sticky="e")
            e = ctk.CTkEntry(content, font=T.F_ENTRY, width=w * 13, height=32,
                             fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT)
            e.grid(row=0, column=col * 2 + 1, padx=(0, 12))
            setattr(self, attr, e)

        for col, (label, attr, w) in enumerate(fields_r1):
            ctk.CTkLabel(content, text=label + ":", font=T.F_BODY, text_color=T.TEXT_MUTED).grid(
                row=1, column=col * 2, padx=(0, 4), pady=(8, 0), sticky="e")
            e = ctk.CTkEntry(content, font=T.F_ENTRY, width=w * 13, height=32,
                             fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT)
            e.grid(row=1, column=col * 2 + 1, padx=(0, 12), pady=(8, 0))
            setattr(self, attr, e)

        btn_frame = ctk.CTkFrame(content, fg_color=T.SURFACE)
        btn_frame.grid(row=2, column=0, columnspan=6, pady=(10, 0), sticky="w")

        ctk.CTkButton(
            btn_frame, text="Agregar usuario", command=self._agregar_usuario,
            font=T.F_BTN, fg_color=T.PRIMARY, hover_color="#1D4ED8",
            text_color=T.TEXT_ON_DARK, height=34, width=150, corner_radius=6,
        ).pack(side="left", padx=(0, 20))

        if self._jerarquia == "admin":
            ctk.CTkLabel(btn_frame, text="Eliminar usuario:", font=T.F_BODY, text_color=T.TEXT_MUTED).pack(side="left", padx=(0, 6))
            self._entry_user_delete = ctk.CTkEntry(
                btn_frame, font=T.F_ENTRY, width=140, height=34,
                fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
            )
            self._entry_user_delete.pack(side="left", padx=(0, 8))
            ctk.CTkButton(
                btn_frame, text="Eliminar", command=self._eliminar_usuario,
                font=T.F_BTN, fg_color=T.DANGER, hover_color="#B91C1C",
                text_color=T.TEXT_ON_DARK, height=34, width=90, corner_radius=6,
            ).pack(side="left")

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _refrescar(self) -> None:
        self._tabla.delete(*self._tabla.get_children())
        for idx, prod in enumerate(obtener_productos()):
            tag = "odd" if idx % 2 else "even"
            self._tabla.insert("", "end", values=prod, tags=(tag,))

    def _buscar(self, event: object = None) -> None:
        texto = self._entry_buscar.get().strip().lower()
        if not texto:
            self._refrescar()
            return

        productos = obtener_productos()
        filtrados = []
        for prod in productos:
            codigo, nombre, *_ = prod
            campo = f"{codigo} {nombre}".lower()
            if texto in campo:
                score = difflib.SequenceMatcher(None, texto, campo).ratio()
                filtrados.append((score, prod))

        filtrados.sort(key=lambda x: x[0], reverse=True)
        self._tabla.delete(*self._tabla.get_children())
        for idx, (_, prod) in enumerate(filtrados):
            tag = "odd" if idx % 2 else "even"
            self._tabla.insert("", "end", values=prod, tags=(tag,))

    def _actualizar(self) -> None:
        codigo        = self._entry_cod_upd.get().strip()
        nuevo_precio  = self._entry_precio_upd.get().strip()
        nuevo_stock   = self._entry_stock_upd.get().strip()
        nuevo_precio_kg = self._entry_precio_kg_upd.get().strip()

        if not codigo:
            messagebox.showwarning("Atención", "Ingrese un código de producto.", parent=self)
            return

        try:
            precio_val    = float(nuevo_precio)    if nuevo_precio    else None
            stock_val     = int(nuevo_stock)       if nuevo_stock     else None
            precio_kg_val = float(nuevo_precio_kg) if nuevo_precio_kg else None
        except ValueError:
            messagebox.showerror("Error", "Valores inválidos.", parent=self)
            return

        if precio_val is None and stock_val is None and precio_kg_val is None:
            messagebox.showwarning("Atención", "Ingrese al menos un valor a actualizar.", parent=self)
            return

        logros: list[str] = []
        try:
            if stock_val is not None:
                if self._jerarquia == "admin":
                    ajustar_stock(codigo, nuevo_stock)
                    logros.append("Stock actualizado")
                else:
                    messagebox.showwarning("Atención", "No tienes permisos para editar el stock.", parent=self)
                    return

            if precio_val is not None:
                ajustar_precio(codigo, nuevo_precio)
                logros.append("Precio actualizado")

            if precio_kg_val is not None:
                ajustar_precioKg(codigo, nuevo_precio_kg)
                logros.append("Precio x Kg actualizado")

        except ProductoNoEncontrado as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        if logros:
            messagebox.showinfo("Éxito", " · ".join(logros) + ".", parent=self)

        self._refrescar()
        for entry in (self._entry_cod_upd, self._entry_precio_upd,
                      self._entry_stock_upd, self._entry_precio_kg_upd):
            entry.delete(0, "end")

    def _agregar_producto(self) -> None:
        cod      = self._entry_cod_new.get().strip()
        nom      = self._entry_nom_new.get().strip()
        pre_str  = self._entry_precio_new.get().strip()
        preKg    = self._entry_precio_kg_new.get().strip()
        stk_str  = self._entry_stock_new.get().strip()

        if not cod or not nom or not pre_str or not stk_str:
            messagebox.showwarning("Atención", "Complete todos los campos.", parent=self)
            return

        try:
            pre = float(pre_str)
            stk = int(stk_str)
        except ValueError:
            messagebox.showerror("Error", "Precio o stock no válidos.", parent=self)
            return

        try:
            agregar_producto(cod, nom, pre, stk, preKg)
        except ProductoExistente as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        messagebox.showinfo("Éxito", f"Producto '{nom}' agregado correctamente.", parent=self)
        self._refrescar()
        for entry in (self._entry_cod_new, self._entry_nom_new, self._entry_precio_new,
                      self._entry_stock_new, self._entry_precio_kg_new):
            entry.delete(0, "end")

    def _eliminar_producto(self) -> None:
        codigo = self._entry_eliminar_cod.get().strip()
        if not codigo:
            messagebox.showerror("Error", "Debe ingresar un código.", parent=self)
            return

        if not obtener_producto_por_codigo(codigo):
            messagebox.showerror("Error", "El producto no existe.", parent=self)
            return

        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar el producto con código '{codigo}'?\nEsta acción no se puede deshacer.",
            parent=self,
        ):
            return

        eliminar_producto(codigo)
        messagebox.showinfo("Éxito", "Producto eliminado correctamente.", parent=self)
        self._refrescar()
        self._entry_eliminar_cod.delete(0, "end")

    def _agregar_usuario(self) -> None:
        nom    = self._entry_nomb_new.get().strip()
        contra = self._entry_contra_new.get().strip()
        jerar  = self._entry_jerar_new.get().strip()

        if not nom or not contra or not jerar:
            messagebox.showwarning("Atención", "Complete todos los campos.", parent=self)
            return

        if self._jerarquia != "admin":
            messagebox.showwarning("Atención", "No tienes permisos para agregar usuarios.", parent=self)
            return

        try:
            agregar_usuario(nom, contra, jerar)
        except UsuarioExistente as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        messagebox.showinfo("Éxito", f"Usuario '{nom}' agregado correctamente.", parent=self)
        for entry in (self._entry_nomb_new, self._entry_contra_new, self._entry_jerar_new):
            entry.delete(0, "end")

    def _eliminar_usuario(self) -> None:
        nombre = self._entry_user_delete.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Debe ingresar un nombre para eliminar.", parent=self)
            return

        if nombre == "admin":
            messagebox.showerror(
                "Error", "No puedes eliminar al usuario administrador principal.", parent=self,
            )
            return

        if not obtener_usuario(nombre):
            messagebox.showerror("Error", "El usuario no existe.", parent=self)
            return

        eliminar_usuario_por_nombre(nombre)
        self._entry_user_delete.delete(0, "end")
        messagebox.showinfo("Éxito", "Usuario eliminado correctamente.", parent=self)


# ── Función de compatibilidad ─────────────────────────────────────────────────

def abrir_gestion_stock(jerarquia: str, parent: ctk.CTk) -> None:
    GestionWindow(parent, jerarquia)
