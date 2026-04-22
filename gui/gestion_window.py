from __future__ import annotations
import tkinter as tk
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
from exceptions import ProductoNoEncontrado, ProductoExistente, UsuarioExistente


class GestionWindow(tk.Toplevel):
    """Ventana de gestión de stock, precios y usuarios."""

    def __init__(self, parent: tk.Misc, jerarquia: str) -> None:
        super().__init__(parent)
        self.state("zoomed")
        self.title("Gestión de Stock y Precios")
        self.geometry("780x600")

        self._jerarquia = jerarquia
        self._build_ui()

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        tk.Label(self, text="GESTIÓN DE STOCK Y PRECIOS", font=("Arial", 16, "bold")).pack(pady=10)
        self._build_tabla()
        self._build_busqueda()
        self._build_actualizar()
        self._build_agregar_producto()
        self._build_usuarios()

    def _build_tabla(self) -> None:
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)

        columnas = ("codigo", "nombre", "precio", "precio x kg", "stock")
        self._tabla = ttk.Treeview(frame, columns=columnas, show="headings", height=14)
        for col in columnas:
            self._tabla.heading(col, text=col.capitalize())
            self._tabla.column(col, width=150)
        self._tabla.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        sb = ttk.Scrollbar(frame, orient="vertical", command=self._tabla.yview)
        sb.pack(side="right", fill="y")
        self._tabla.configure(yscrollcommand=sb.set)

        self._refrescar()

    def _build_busqueda(self) -> None:
        frame = tk.Frame(self)
        frame.pack(fill="x", padx=10)

        tk.Label(frame, text="Buscar:", font=("Arial", 12)).pack(side="left")
        self._entry_buscar = tk.Entry(frame, font=("Arial", 12), width=30)
        self._entry_buscar.pack(side="right", padx=5)
        self._entry_buscar.bind("<KeyRelease>", self._buscar)
        self._entry_buscar.bind("<Return>", self._buscar)

    def _build_actualizar(self) -> None:
        frame = tk.LabelFrame(
            self, text="Actualizar producto existente", font=("Arial", 12), padx=10, pady=10,
        )
        frame.pack(fill="x", padx=10, pady=5)

        tk.Label(frame, text="Código:", font=("Arial", 12)).grid(row=0, column=0)
        self._entry_cod_upd = tk.Entry(frame, font=("Arial", 12))
        self._entry_cod_upd.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Nuevo precio:", font=("Arial", 12)).grid(row=0, column=2)
        self._entry_precio_upd = tk.Entry(frame, font=("Arial", 12), width=10)
        self._entry_precio_upd.grid(row=0, column=3, padx=5)

        tk.Label(frame, text="Editar stock:", font=("Arial", 12)).grid(row=0, column=4)
        self._entry_stock_upd = tk.Entry(frame, font=("Arial", 12), width=10)
        self._entry_stock_upd.grid(row=0, column=5, padx=5)

        tk.Label(frame, text="Nuevo Precio X Kg:", font=("Arial", 12)).grid(row=0, column=6)
        self._entry_precio_kg_upd = tk.Entry(frame, font=("Arial", 12), width=10)
        self._entry_precio_kg_upd.grid(row=0, column=7, padx=5)

        tk.Button(
            frame, text="Actualizar", font=("Arial", 12), bg="#2196F3", fg="white",
            command=self._actualizar,
        ).grid(row=0, column=8, padx=10)

    def _build_agregar_producto(self) -> None:
        frame = tk.LabelFrame(
            self, text="Agregar/Eliminar producto", font=("Arial", 12), padx=10, pady=10,
        )
        frame.pack(fill="x", padx=10, pady=10)

        for i in range(12):
            frame.columnconfigure(i, weight=1)

        tk.Label(frame, text="Código:", font=("Arial", 12)).grid(row=0, column=0)
        self._entry_cod_new = tk.Entry(frame, font=("Arial", 12))
        self._entry_cod_new.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Nombre:", font=("Arial", 12)).grid(row=0, column=2)
        self._entry_nom_new = tk.Entry(frame, font=("Arial", 12))
        self._entry_nom_new.grid(row=0, column=3, padx=5)

        tk.Label(frame, text="Precio:", font=("Arial", 12)).grid(row=1, column=0)
        self._entry_precio_new = tk.Entry(frame, font=("Arial", 12))
        self._entry_precio_new.grid(row=1, column=1, padx=5)

        tk.Label(frame, text="Stock:", font=("Arial", 12)).grid(row=1, column=2)
        self._entry_stock_new = tk.Entry(frame, font=("Arial", 12))
        self._entry_stock_new.grid(row=1, column=3, padx=5)

        tk.Label(frame, text="Precio Kilo:", font=("Arial", 12)).grid(row=2, column=0)
        self._entry_precio_kg_new = tk.Entry(frame, font=("Arial", 12))
        self._entry_precio_kg_new.grid(row=2, column=1, padx=5)

        tk.Label(frame, text="Eliminar código:", font=("Arial", 12)).grid(row=0, column=4, padx=5)
        self._entry_eliminar_cod = tk.Entry(frame, font=("Arial", 12), width=12)
        self._entry_eliminar_cod.grid(row=0, column=5, padx=5)

        tk.Button(
            frame, text="Agregar producto", font=("Arial", 12), bg="#2196F3", fg="white",
            command=self._agregar_producto,
        ).grid(row=2, column=3, pady=10)

        tk.Button(
            frame, text="Eliminar", font=("Arial", 12),
            command=self._eliminar_producto,
        ).grid(row=2, column=5, padx=10)

        tk.Button(
            frame, text="Gestionar Promociones", font=("Arial", 12),
            bg="#2196F3", fg="white",
            command=lambda: PromosWindow(self),
        ).grid(row=1, column=9)

    def _build_usuarios(self) -> None:
        frame = tk.LabelFrame(
            self, text="Agregar nuevo usuario", font=("Arial", 12), padx=10, pady=10,
        )
        frame.pack(fill="x", padx=10, pady=10)

        if self._jerarquia == "admin":
            tk.Label(frame, text="Eliminar usuario:", font=("Arial", 12)).grid(row=0, column=6, padx=5)
            self._entry_user_delete = tk.Entry(frame, font=("Arial", 12))
            self._entry_user_delete.grid(row=0, column=7, padx=5)
            tk.Button(
                frame, text="Eliminar", font=("Arial", 12),
                command=self._eliminar_usuario,
            ).grid(row=2, column=7, padx=5)

        tk.Label(frame, text="Nombre:", font=("Arial", 12)).grid(row=0, column=0)
        self._entry_nomb_new = tk.Entry(frame, font=("Arial", 12))
        self._entry_nomb_new.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Contraseña:", font=("Arial", 12)).grid(row=0, column=2)
        self._entry_contra_new = tk.Entry(frame, font=("Arial", 12))
        self._entry_contra_new.grid(row=0, column=3, padx=5)

        tk.Label(frame, text="Jerarquia:", font=("Arial", 12)).grid(row=1, column=0)
        self._entry_jerar_new = tk.Entry(frame, font=("Arial", 12))
        self._entry_jerar_new.grid(row=1, column=1, padx=5)

        tk.Button(
            frame, text="Agregar usuario", font=("Arial", 12), bg="#2196F3", fg="white",
            command=self._agregar_usuario,
        ).grid(row=2, column=2, pady=10)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _refrescar(self) -> None:
        self._tabla.delete(*self._tabla.get_children())
        for prod in obtener_productos():
            self._tabla.insert("", "end", values=prod)

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
        for _, prod in filtrados:
            self._tabla.insert("", "end", values=prod)

    def _actualizar(self) -> None:
        codigo = self._entry_cod_upd.get().strip()
        nuevo_precio = self._entry_precio_upd.get().strip()
        nuevo_stock = self._entry_stock_upd.get().strip()
        nuevo_precio_kg = self._entry_precio_kg_upd.get().strip()

        if not codigo:
            messagebox.showwarning("Atención", "Ingrese un código de producto.", parent=self)
            return

        try:
            precio_val = float(nuevo_precio) if nuevo_precio else None
            stock_val = int(nuevo_stock) if nuevo_stock else None
            precio_kg_val = float(nuevo_precio_kg) if nuevo_precio_kg else None
        except ValueError:
            messagebox.showerror("Error", "Valores inválidos.", parent=self)
            return

        if precio_val is None and stock_val is None and precio_kg_val is None:
            messagebox.showwarning("Atención", "Ingrese al menos un valor a actualizar.", parent=self)
            return

        try:
            if stock_val is not None:
                if self._jerarquia == "admin":
                    ajustar_stock(codigo, nuevo_stock)
                    messagebox.showinfo("Éxito", "Stock actualizado correctamente.", parent=self)
                else:
                    messagebox.showwarning("Atención", "No tienes permisos para editar el stock.", parent=self)
                    return

            if precio_val is not None:
                ajustar_precio(codigo, nuevo_precio)
                messagebox.showinfo("Éxito", "Precio actualizado correctamente.", parent=self)

            if precio_kg_val is not None:
                ajustar_precioKg(codigo, nuevo_precio_kg)
                messagebox.showinfo("Éxito", "Precio X Kg actualizado correctamente.", parent=self)

        except ProductoNoEncontrado as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        self._refrescar()
        for entry in (self._entry_cod_upd, self._entry_precio_upd,
                      self._entry_stock_upd, self._entry_precio_kg_upd):
            entry.delete(0, tk.END)

    def _agregar_producto(self) -> None:
        cod = self._entry_cod_new.get().strip()
        nom = self._entry_nom_new.get().strip()
        pre_str = self._entry_precio_new.get().strip()
        preKg_str = self._entry_precio_kg_new.get().strip()
        stk_str = self._entry_stock_new.get().strip()

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
            agregar_producto(cod, nom, pre, stk, preKg_str)
        except ProductoExistente as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        messagebox.showinfo("Éxito", f"Producto '{nom}' agregado correctamente.", parent=self)
        self._refrescar()
        for entry in (self._entry_cod_new, self._entry_nom_new, self._entry_precio_new,
                      self._entry_stock_new, self._entry_precio_kg_new):
            entry.delete(0, tk.END)

    def _eliminar_producto(self) -> None:
        codigo = self._entry_eliminar_cod.get().strip()
        if not codigo:
            messagebox.showerror("Error", "Debe ingresar un código.", parent=self)
            return

        if not obtener_producto_por_codigo(codigo):
            messagebox.showerror("Error", "El producto no existe.", parent=self)
            return

        eliminar_producto(codigo)
        messagebox.showinfo("Éxito", "Producto eliminado correctamente.", parent=self)
        self._refrescar()
        self._entry_eliminar_cod.delete(0, tk.END)

    def _agregar_usuario(self) -> None:
        nom = self._entry_nomb_new.get().strip()
        contra = self._entry_contra_new.get().strip()
        jerar = self._entry_jerar_new.get().strip()

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
        self._refrescar()
        for entry in (self._entry_nomb_new, self._entry_contra_new, self._entry_jerar_new):
            entry.delete(0, tk.END)

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
        self._entry_user_delete.delete(0, tk.END)
        messagebox.showinfo("Éxito", "Usuario eliminado correctamente.", parent=self)


# ── Función de compatibilidad ─────────────────────────────────────────────────

def abrir_gestion_stock(jerarquia: str, parent: tk.Misc) -> None:
    GestionWindow(parent, jerarquia)
