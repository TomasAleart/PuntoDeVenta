from __future__ import annotations
import customtkinter as ctk
from core.logic_login import validar_login
import gui.theme as T


class LoginWindow(ctk.CTk):
    """Ventana raíz de inicio de sesión."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Inicio de Sesión — Minimarket V&E")
        self.geometry("440x400")
        self.resizable(False, False)
        T.setup_treeview_style(self)
        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header oscuro ─────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=T.SIDEBAR_BG, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            header, text="Minimarket V&E",
            font=T.F_APP_TITLE, text_color=T.TEXT_ON_DARK,
        ).pack(pady=(28, 4))
        ctk.CTkLabel(
            header, text="Sistema de Punto de Venta",
            font=T.F_SMALL, text_color=T.SUBTEXT_DARK,
        ).pack(pady=(0, 20))

        # ── Card blanco con formulario ─────────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=T.SURFACE, corner_radius=0)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(card, fg_color=T.SURFACE)
        inner.pack(expand=True, padx=50, pady=30)

        ctk.CTkLabel(
            inner, text="Usuario", font=T.F_BODY_B, text_color=T.TEXT, anchor="w",
        ).pack(fill="x")
        self._entry_user = ctk.CTkEntry(
            inner, font=T.F_ENTRY, placeholder_text="Ingrese su usuario",
            height=40, border_color=T.BORDER, fg_color=T.SURFACE, text_color=T.TEXT,
        )
        self._entry_user.pack(fill="x", pady=(4, 14))

        ctk.CTkLabel(
            inner, text="Contraseña", font=T.F_BODY_B, text_color=T.TEXT, anchor="w",
        ).pack(fill="x")
        self._entry_pass = ctk.CTkEntry(
            inner, font=T.F_ENTRY, placeholder_text="Ingrese su contraseña",
            show="*", height=40, border_color=T.BORDER,
            fg_color=T.SURFACE, text_color=T.TEXT,
        )
        self._entry_pass.pack(fill="x", pady=(4, 8))

        self._label_error = ctk.CTkLabel(
            inner, text="", font=T.F_SMALL, text_color=T.DANGER,
        )
        self._label_error.pack(pady=(0, 10))

        ctk.CTkButton(
            inner, text="Ingresar", command=self._login,
            font=T.F_BTN, fg_color=T.SUCCESS, hover_color="#14803E",
            text_color=T.TEXT_ON_DARK, height=42, corner_radius=8,
        ).pack(fill="x")

        self._entry_pass.bind("<Return>", lambda e: self._login())
        self._entry_user.bind("<Return>", lambda e: self._entry_pass.focus())

    def _login(self) -> None:
        fila = validar_login(self._entry_user.get(), self._entry_pass.get())
        if fila:
            _id, usuario, _contra, jerarquia = fila
            self.destroy()
            from gui.main_window import MainWindow
            MainWindow(usuario, jerarquia).mainloop()
        else:
            self._label_error.configure(text="Usuario o contraseña incorrectos")


# ── Función de compatibilidad ─────────────────────────────────────────────────

def abrir_login() -> None:
    LoginWindow().mainloop()
