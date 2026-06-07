from __future__ import annotations
import customtkinter as ctk
from tkinter import ttk
from database.promos_db import refrescar, guardar_promo, eliminar_promo, editar_promo
import gui.theme as T


class PromosWindow(ctk.CTkToplevel):
    """Ventana para gestionar promociones de productos."""

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Gestión de Promociones")
        # Hacemos que se comporte de forma robusta al frente
        self.grab_set() 
        self.focus_force()
        
        self.state("zoomed")  # Conserva tu maximizado
        self._build_ui()

    def _build_ui(self) -> None:
        self.configure(fg_color=T.BG)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color=T.SIDEBAR_BG, corner_radius=0, height=56)
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="GESTIÓN DE PROMOCIONES",
            font=T.F_H1, text_color=T.TEXT_ON_DARK,
        ).pack(side="left", padx=24, pady=16)

        # Tabla
        tframe = ctk.CTkFrame(self, fg_color=T.SURFACE, corner_radius=8)
        tframe.grid(row=1, column=0, sticky="nsew", padx=16, pady=(12, 6))

        inner = ctk.CTkFrame(tframe, fg_color=T.SURFACE)
        inner.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("id", "codigo", "tipo", "cantidad_min", "precio_promo", "descuento", "activa")
        self._tabla = ttk.Treeview(inner, columns=cols, show="headings")
        for col in cols:
            self._tabla.heading(col, text=col.capitalize())
            self._tabla.column(col, width=120, anchor="center")
        self._tabla.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(inner, orient="vertical", command=self._tabla.yview)
        sb.pack(side="right", fill="y")
        self._tabla.configure(yscrollcommand=sb.set)
        T.tag_rows(self._tabla)
        self._tabla.bind("<<TreeviewSelect>>", self._cargar_campos)

        # Formulario
        form_card = ctk.CTkFrame(self, fg_color=T.SURFACE, corner_radius=8)
        form_card.grid(row=2, column=0, sticky="ew", padx=16, pady=6)

        ctk.CTkLabel(
            form_card, text="Agregar / Editar promoción",
            font=T.F_H2, text_color=T.TEXT_MUTED, anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 0))
        ctk.CTkFrame(form_card, fg_color=T.BORDER, height=1).pack(fill="x", padx=10, pady=(4, 8))

        form = ctk.CTkFrame(form_card, fg_color=T.SURFACE)
        form.pack(fill="x", padx=14, pady=(0, 10))

        labels = [
            "Código producto", "Tipo", "Cantidad mín.",
            "Precio promo", "Descuento (%)", "Activa (1/0)",
        ]
        self._entries: list[ctk.CTkEntry] = []
        for i, label in enumerate(labels):
            ctk.CTkLabel(form, text=label, font=T.F_BODY, text_color=T.TEXT_MUTED).grid(
                row=0, column=i, padx=(0 if i else 0, 0), pady=(0, 4))
            e = ctk.CTkEntry(
                form, font=T.F_ENTRY, width=120, height=32,
                fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
            )
            e.grid(row=1, column=i, padx=(0, 8))
            self._entries.append(e)

        (self._entry_codigo, self._entry_tipo, self._entry_cant,
         self._entry_precio, self._entry_desc, self._entry_activa) = self._entries

        # Botones del formulario
        btn_frame = ctk.CTkFrame(form_card, fg_color=T.SURFACE)
        btn_frame.pack(pady=(0, 12))

        ctk.CTkButton(
            btn_frame, text="Guardar", command=self._guardar,
            font=T.F_BTN, fg_color=T.SUCCESS, hover_color="#14803E",
            text_color=T.TEXT_ON_DARK, height=36, width=110, corner_radius=6,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame, text="Editar", command=self._editar,
            font=T.F_BTN, fg_color=T.WARNING, hover_color="#B45309",
            text_color=T.TEXT_ON_DARK, height=36, width=110, corner_radius=6,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame, text="Eliminar",
            command=lambda: eliminar_promo(self._tabla),
            font=T.F_BTN, fg_color=T.DANGER, hover_color="#B91C1C",
            text_color=T.TEXT_ON_DARK, height=36, width=110, corner_radius=6,
        ).pack(side="left", padx=10)

        refrescar(self._tabla)

    def _cargar_campos(self, event: object = None) -> None:
        sel = self._tabla.selection()
        if not sel:
            return
        row = self._tabla.item(sel[0])["values"]
        for entry, value in zip(self._entries, row[1:]):
            entry.delete(0, "end")
            entry.insert(0, value)

    def _guardar(self) -> None:
        guardar_promo(
            self._tabla,
            self._entry_codigo, self._entry_tipo, self._entry_cant,
            self._entry_precio, self._entry_desc, self._entry_activa,
        )

    def _editar(self) -> None:
        editar_promo(
            self._tabla,
            self._entry_codigo, self._entry_tipo, self._entry_cant,
            self._entry_precio, self._entry_desc, self._entry_activa,
        )


# ── Función de compatibilidad ─────────────────────────────────────────────────

def abrir_gestion_promos(parent: ctk.CTk | None = None) -> None:
    import tkinter as tk
    PromosWindow(parent or tk._default_root)
