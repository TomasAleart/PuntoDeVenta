from __future__ import annotations
import tkinter as tk
from core.logic_login import validar_login


class LoginWindow(tk.Tk):
    """Ventana raíz de inicio de sesión."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Inicio de Sesión")
        self.geometry("350x220")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self) -> None:
        tk.Label(self, text="Usuario:", font=("Arial", 14)).pack(pady=5)
        self._entry_user = tk.Entry(self, font=("Arial", 14))
        self._entry_user.pack()

        tk.Label(self, text="Contraseña:", font=("Arial", 14)).pack(pady=5)
        self._entry_pass = tk.Entry(self, font=("Arial", 14), show="*")
        self._entry_pass.pack()

        self._label_error = tk.Label(self, text="", fg="red", font=("Arial", 12))
        self._label_error.pack()

        tk.Button(
            self, text="Ingresar", font=("Arial", 14), bg="#4CAF50", fg="white",
            command=self._login,
        ).pack(pady=10)

        self._entry_pass.bind("<Return>", lambda e: self._login())

    def _login(self) -> None:
        fila = validar_login(self._entry_user.get(), self._entry_pass.get())
        if fila:
            _id, usuario, _contra, jerarquia = fila
            self.destroy()
            from gui.main_window import MainWindow
            MainWindow(usuario, jerarquia).mainloop()
        else:
            self._label_error.config(text="Usuario o contraseña incorrectos")


# ── Función de compatibilidad ─────────────────────────────────────────────────

def abrir_login() -> None:
    LoginWindow().mainloop()
