from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from database.connection import get_db
from database.caja_db import obtener_caja_actual
from database.arqueo_db import insertar_arqueo
from reports.arqueo_report import imprimir_arqueos
from core.logic_arqueos import buscar
import gui.theme as T


class ArqueoWindow(ctk.CTkToplevel):
    """Ventana para registrar un arqueo de caja."""

    def __init__(self, parent: ctk.CTk, usuario: str) -> None:
        super().__init__(parent)
        self.title("Arqueo de Caja")
        self.geometry("380x260")
        self.resizable(False, False)
        self.grab_set()
        self._usuario = usuario
        self._build_ui()

    def _build_ui(self) -> None:
        self.configure(fg_color=T.BG)

        # Header
        header = ctk.CTkFrame(self, fg_color=T.SIDEBAR_BG, corner_radius=0, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Arqueo de Caja",
            font=T.F_H1, text_color=T.TEXT_ON_DARK,
        ).pack(side="left", padx=20, pady=12)

        body = ctk.CTkFrame(self, fg_color=T.BG)
        body.pack(fill="both", expand=True, padx=28, pady=20)

        ctk.CTkLabel(
            body, text="Caja real contada ($):",
            font=T.F_BODY_B, text_color=T.TEXT, anchor="w",
        ).pack(fill="x")
        self._entry_real = ctk.CTkEntry(
            body, font=T.F_ENTRY, height=38,
            fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT,
        )
        self._entry_real.pack(fill="x", pady=(4, 16))
        self._entry_real.focus()

        btn_frame = ctk.CTkFrame(body, fg_color=T.BG)
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame, text="Confirmar", command=self._guardar,
            font=T.F_BTN, fg_color=T.SUCCESS, hover_color="#14803E",
            text_color=T.TEXT_ON_DARK, height=38, width=130, corner_radius=6,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame, text="Ver arqueos", command=self._ver_arqueos,
            font=T.F_BTN, fg_color=T.PRIMARY, hover_color="#1D4ED8",
            text_color=T.TEXT_ON_DARK, height=38, width=130, corner_radius=6,
        ).pack(side="left")

    def _guardar(self) -> None:
        try:
            caja_real = float(self._entry_real.get())
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido.", parent=self)
            return

        with get_db() as conn:
            caja_sis   = obtener_caja_actual(conn)
            diferencia = caja_real - caja_sis
            insertar_arqueo(conn, self._usuario, caja_sis, caja_real, diferencia)

        messagebox.showinfo(
            "Arqueo registrado",
            f"Caja sistema: ${caja_sis:.2f}\n"
            f"Caja real:    ${caja_real:.2f}\n"
            f"Diferencia:   ${diferencia:.2f}",
            parent=self,
        )
        self.destroy()

    def _ver_arqueos(self) -> None:
        ArqueoConsultaWindow(self)


class ArqueoConsultaWindow(ctk.CTkToplevel):
    """Ventana para filtrar y consultar arqueos registrados."""

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Consulta de Arqueos")
        self.geometry("780x520")
        self.grab_set()
        self._build_ui()

    def _build_ui(self) -> None:
        self.configure(fg_color=T.BG)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color=T.SIDEBAR_BG, corner_radius=0, height=50)
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="Filtrar Arqueos",
            font=T.F_H1, text_color=T.TEXT_ON_DARK,
        ).pack(side="left", padx=20, pady=12)

        # Filtros
        filtros = ctk.CTkFrame(self, fg_color=T.SURFACE, corner_radius=8)
        filtros.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 6))

        inner = ctk.CTkFrame(filtros, fg_color=T.SURFACE)
        inner.pack(fill="x", padx=14, pady=10)

        campos = [
            ("Desde (YYYY-MM-DD):", "_entry_desde", 12),
            ("Hasta (YYYY-MM-DD):", "_entry_hasta", 12),
            ("Usuario:",            "_entry_usuario", 10),
        ]
        for col, (label, attr, w) in enumerate(campos):
            ctk.CTkLabel(inner, text=label, font=T.F_BODY, text_color=T.TEXT_MUTED).grid(
                row=0, column=col * 2, padx=(0, 4), sticky="e")
            e = ctk.CTkEntry(inner, font=T.F_ENTRY, width=w * 13, height=32,
                             fg_color=T.SURFACE, border_color=T.BORDER, text_color=T.TEXT)
            e.grid(row=0, column=col * 2 + 1, padx=(0, 16))
            setattr(self, attr, e)

        # Tabla
        tframe = ctk.CTkFrame(self, fg_color=T.SURFACE, corner_radius=8)
        tframe.grid(row=2, column=0, sticky="nsew", padx=16, pady=6)

        inner_t = ctk.CTkFrame(tframe, fg_color=T.SURFACE)
        inner_t.pack(fill="both", expand=True, padx=10, pady=10)

        columnas = ("fecha", "usuario", "sistema", "real", "diferencia")
        self._tabla = ttk.Treeview(inner_t, columns=columnas, show="headings")
        for col in columnas:
            self._tabla.heading(col, text=col.capitalize())
            self._tabla.column(col, width=140, anchor="center")
        self._tabla.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(inner_t, orient="vertical", command=self._tabla.yview)
        sb.pack(side="right", fill="y")
        self._tabla.configure(yscrollcommand=sb.set)
        T.tag_rows(self._tabla)

        # tk.Label porque logic_arqueos.py llama .config() (no .configure())
        self._label_totales = tk.Label(
            self, text="", font=T.F_BODY_B, fg=T.TEXT, bg=T.BG,
        )
        self._label_totales.grid(row=3, column=0, pady=(4, 0))

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color=T.BG)
        btn_frame.grid(row=4, column=0, pady=12)

        ctk.CTkButton(
            btn_frame, text="Buscar", command=self._buscar,
            font=T.F_BTN, fg_color=T.PRIMARY, hover_color="#1D4ED8",
            text_color=T.TEXT_ON_DARK, height=38, width=120, corner_radius=6,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="Imprimir arqueos",
            command=lambda: imprimir_arqueos(self._tabla),
            font=T.F_BTN, fg_color=T.SUCCESS, hover_color="#14803E",
            text_color=T.TEXT_ON_DARK, height=38, width=160, corner_radius=6,
        ).pack(side="left", padx=8)

    def _buscar(self) -> None:
        buscar(
            self._tabla,
            self._entry_desde,
            self._entry_hasta,
            self._entry_usuario,
            self._label_totales,
        )


# ── Función de compatibilidad ─────────────────────────────────────────────────

def abrir_arqueo(usuario: str, parent: ctk.CTk | None = None) -> None:
    import tkinter as tk
    ArqueoWindow(parent or tk._default_root, usuario)
