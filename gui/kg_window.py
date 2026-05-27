from __future__ import annotations
import customtkinter as ctk
from tkinter import messagebox
from core.validar import aceptar
import gui.theme as T


class KgWindow(ctk.CTkToplevel):
    """Diálogo modal para ingresar el peso de un producto por kilo."""

    def __init__(self, parent: ctk.CTk, precio_kg: float, codigo: str) -> None:
        super().__init__(parent)
        self.title("Ingreso de Kilos")
        self.geometry("360x240")
        self.resizable(False, False)

        self.result: tuple[float, float] | None = None
        self._precio_kg = precio_kg
        self._codigo    = codigo
        self._resultado: dict = {}

        self._build_ui()
        self.grab_set()
        self.wait_window()

        if self._resultado:
            self.result = (self._resultado["peso"], self._resultado["subtotal"])

    def _build_ui(self) -> None:
        self.configure(fg_color=T.BG)

        header = ctk.CTkFrame(self, fg_color=T.SIDEBAR_BG, corner_radius=0, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Ingreso de Kilos",
            font=T.F_H1, text_color=T.TEXT_ON_DARK,
        ).pack(side="left", padx=20, pady=12)

        body = ctk.CTkFrame(self, fg_color=T.BG)
        body.pack(fill="both", expand=True, padx=32, pady=22)

        ctk.CTkLabel(
            body, text="Peso (kg):", font=T.F_BODY_B, text_color=T.TEXT, anchor="w",
        ).pack(fill="x")
        self._entry_kg = ctk.CTkEntry(
            body, font=T.F_ENTRY_LG, height=44,
            placeholder_text="0.000",
            fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
            justify="center",
        )
        self._entry_kg.pack(fill="x", pady=(4, 16))
        self._entry_kg.focus()
        self._entry_kg.bind("<Return>", lambda e: self._aceptar())

        ctk.CTkButton(
            body, text="Aceptar", command=self._aceptar,
            font=T.F_BTN, fg_color=T.SUCCESS, hover_color="#14803E",
            text_color=T.TEXT_ON_DARK, height=40, corner_radius=6,
        ).pack(fill="x")

    def _aceptar(self) -> None:
        try:
            aceptar(self._entry_kg, self, self._precio_kg, self._resultado)
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)
