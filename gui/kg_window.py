from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from core.validar import aceptar


class KgWindow(tk.Toplevel):
    """Diálogo modal para ingresar el peso de un producto por kilo."""

    def __init__(self, parent: tk.Misc, precio_kg: float, codigo: str) -> None:
        super().__init__(parent)
        self.title("Ingreso de Kilos")
        self.geometry("350x220")
        self.resizable(False, False)

        self.result: tuple[float, float] | None = None
        self._precio_kg = precio_kg
        self._codigo = codigo
        self._resultado: dict = {}

        self._build_ui()
        self.grab_set()
        self.wait_window()

        if self._resultado:
            self.result = (self._resultado["peso"], self._resultado["subtotal"])

    def _build_ui(self) -> None:
        tk.Label(self, text="Peso (kg):", font=("Arial", 14)).pack(pady=5)
        self._entry_kg = tk.Entry(self, font=("Arial", 14))
        self._entry_kg.pack()
        self._entry_kg.focus_set()
        tk.Button(self, text="Aceptar", font=("Arial", 14), command=self._aceptar).pack(pady=20)
        self._entry_kg.bind("<Return>", lambda e: self._aceptar())

    def _aceptar(self) -> None:
        try:
            aceptar(self._entry_kg, self, self._precio_kg, self._resultado)
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)
