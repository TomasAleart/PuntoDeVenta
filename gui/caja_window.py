from __future__ import annotations
import customtkinter as ctk
from tkinter import messagebox
from database.caja_db import insertar_caja_inicial, actualizar_caja_db
import gui.theme as T


class CajaInicialWindow(ctk.CTkToplevel):
    """Diálogo modal que solicita el monto inicial de caja al iniciar sesión."""

    def __init__(self, parent: ctk.CTk, usuario: str) -> None:
        super().__init__(parent)
        self.title("Caja Inicial")
        self.geometry("340x200")
        self.resizable(False, False)
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self._usuario = usuario
        self._build_ui()
        self.wait_window()

    def _build_ui(self) -> None:
        self.configure(fg_color=T.BG)

        header = ctk.CTkFrame(self, fg_color=T.SIDEBAR_BG, corner_radius=0, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Caja Inicial",
            font=T.F_H1, text_color=T.TEXT_ON_DARK,
        ).pack(side="left", padx=20, pady=12)

        body = ctk.CTkFrame(self, fg_color=T.BG)
        body.pack(fill="both", expand=True, padx=28, pady=18)

        ctk.CTkLabel(
            body, text="Ingrese el monto inicial de caja ($):",
            font=T.F_BODY_B, text_color=T.TEXT, anchor="w",
        ).pack(fill="x")
        self._entry = ctk.CTkEntry(
            body, font=T.F_ENTRY, height=38,
            fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
        )
        self._entry.pack(fill="x", pady=(4, 14))
        self._entry.focus()
        self._entry.bind("<Return>", lambda e: self._guardar())

        ctk.CTkButton(
            body, text="Aceptar", command=self._guardar,
            font=T.F_BTN, fg_color=T.SUCCESS, hover_color="#14803E",
            text_color=T.TEXT_ON_DARK, height=38, corner_radius=6,
        ).pack(fill="x")

    def _guardar(self) -> None:
        try:
            monto = float(self._entry.get())
        except ValueError:
            messagebox.showerror("Error", "El monto inicial de caja debe ser un número válido.", parent=self)
            return
        insertar_caja_inicial(monto, self._usuario)
        self.destroy()


class ActualizarCajaWindow(ctk.CTkToplevel):
    """Diálogo para sumar o restar un monto a la caja actual."""

    def __init__(self, parent: ctk.CTk, usuario: str) -> None:
        super().__init__(parent)
        self.title("Actualizar Caja")
        self.geometry("340x240")
        self.resizable(False, False)
        self.grab_set()

        self._usuario = usuario
        self._build_ui()

    def _build_ui(self) -> None:
        self.configure(fg_color=T.BG)

        header = ctk.CTkFrame(self, fg_color=T.SIDEBAR_BG, corner_radius=0, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Actualizar Caja",
            font=T.F_H1, text_color=T.TEXT_ON_DARK,
        ).pack(side="left", padx=20, pady=12)

        body = ctk.CTkFrame(self, fg_color=T.BG)
        body.pack(fill="both", expand=True, padx=28, pady=18)

        ctk.CTkLabel(
            body, text="Monto (positivo suma / negativo resta):",
            font=T.F_BODY_B, text_color=T.TEXT, anchor="w",
        ).pack(fill="x")
        self._entry = ctk.CTkEntry(
            body, font=T.F_ENTRY, height=38,
            placeholder_text="Ej: 500 o -200",
            fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
        )
        self._entry.pack(fill="x", pady=(4, 14))
        self._entry.focus()
        self._entry.bind("<Return>", lambda e: self._guardar())

        ctk.CTkButton(
            body, text="Confirmar", command=self._guardar,
            font=T.F_BTN, fg_color=T.SUCCESS, hover_color="#14803E",
            text_color=T.TEXT_ON_DARK, height=38, corner_radius=6,
        ).pack(fill="x")

    def _guardar(self) -> None:
        try:
            monto = float(self._entry.get())
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido.", parent=self)
            return
        caja_actual, caja_nueva = actualizar_caja_db(monto, self._usuario)
        messagebox.showinfo(
            "Caja actualizada",
            f"Caja anterior: ${caja_actual:.2f}\nCaja nueva:    ${caja_nueva:.2f}",
            parent=self,
        )
        self.destroy()


# ── Funciones de compatibilidad ───────────────────────────────────────────────

def preguntar_caja_inicial(usuario: str, parent: ctk.CTk) -> None:
    CajaInicialWindow(parent, usuario)


def actualizar_caja(usuario: str, parent: ctk.CTk) -> None:
    ActualizarCajaWindow(parent, usuario)
