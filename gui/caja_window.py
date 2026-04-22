from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from database.caja_db import insertar_caja_inicial, actualizar_caja_db


class CajaInicialWindow(tk.Toplevel):
    """Diálogo modal que solicita el monto inicial de caja al iniciar sesión."""

    def __init__(self, parent: tk.Misc, usuario: str) -> None:
        super().__init__(parent)
        self.title("Caja Inicial")
        self.geometry("300x150")
        self.grab_set()
        self.transient(parent)
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self._usuario = usuario
        self._build_ui()
        self.wait_window()

    def _build_ui(self) -> None:
        tk.Label(self, text="Ingrese el monto inicial de caja:", font=("Arial", 12)).pack(pady=10)
        self._entry = tk.Entry(self, font=("Arial", 12))
        self._entry.pack()
        self._entry.focus_set()
        tk.Button(self, text="Aceptar", command=self._guardar, font=("Arial", 12)).pack(pady=10)
        self._entry.bind("<Return>", lambda e: self._guardar())

    def _guardar(self) -> None:
        try:
            monto = float(self._entry.get())
        except ValueError:
            messagebox.showerror("Error", "El monto inicial de caja debe ser un número válido.", parent=self)
            return
        insertar_caja_inicial(monto, self._usuario)
        self.destroy()


class ActualizarCajaWindow(tk.Toplevel):
    """Diálogo para sumar o restar un monto a la caja actual."""

    def __init__(self, parent: tk.Misc, usuario: str) -> None:
        super().__init__(parent)
        self.title("Actualizar Caja")
        self.geometry("300x220")
        self.grab_set()

        self._usuario = usuario
        self._build_ui()

    def _build_ui(self) -> None:
        tk.Label(self, text="Monto (+ suma / - resta)", font=("Arial", 12)).pack(pady=10)
        self._entry = tk.Entry(self, font=("Arial", 12))
        self._entry.pack()
        self._entry.focus_set()
        tk.Button(
            self, text="Confirmar", font=("Arial", 12), bg="#4CAF50", fg="white",
            command=self._guardar,
        ).pack(pady=15)
        self._entry.bind("<Return>", lambda e: self._guardar())

    def _guardar(self) -> None:
        try:
            monto = float(self._entry.get())
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido.", parent=self)
            return
        caja_actual, caja_nueva = actualizar_caja_db(monto, self._usuario)
        messagebox.showinfo(
            "Caja actualizada",
            f"Caja anterior: ${caja_actual:.2f}\nCaja nueva: ${caja_nueva:.2f}",
            parent=self,
        )
        self.destroy()


# ── Funciones de compatibilidad ───────────────────────────────────────────────

def preguntar_caja_inicial(usuario: str, parent: tk.Misc) -> None:
    CajaInicialWindow(parent, usuario)


def actualizar_caja(usuario: str, parent: tk.Misc) -> None:
    ActualizarCajaWindow(parent, usuario)
