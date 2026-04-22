from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from database.promos_db import refrescar, guardar_promo, eliminar_promo, editar_promo


class PromosWindow(tk.Toplevel):
    """Ventana para gestionar promociones de productos."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("Gestión de Promociones")
        self.state("zoomed")
        self._build_ui()

    def _build_ui(self) -> None:
        tk.Label(self, text="GESTIÓN DE PROMOCIONES", font=("Arial", 18, "bold")).pack(pady=10)

        # ── Tabla ──────────────────────────────────────────────────────────────
        frame_tabla = tk.Frame(self)
        frame_tabla.pack(fill="both", expand=True)

        cols = ("id", "codigo", "tipo", "cantidad_min", "precio_promo", "descuento", "activa")
        self._tabla = ttk.Treeview(frame_tabla, columns=cols, show="headings")
        for col in cols:
            self._tabla.heading(col, text=col.capitalize())
            self._tabla.column(col, width=120)
        self._tabla.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(frame_tabla, orient="vertical", command=self._tabla.yview)
        sb.pack(side="right", fill="y")
        self._tabla.configure(yscrollcommand=sb.set)

        # ── Formulario ──────────────────────────────────────────────────────────
        frame_form = tk.LabelFrame(
            self, text="Agregar / Editar promoción", font=("Arial", 12), padx=10, pady=10,
        )
        frame_form.pack(fill="x", padx=10, pady=10)

        labels = [
            "Código producto", "Tipo", "Cantidad mín.",
            "Precio promo", "Descuento (%)", "Activa (1/0)",
        ]
        entries = []
        for i, label in enumerate(labels):
            tk.Label(frame_form, text=label, font=("Arial", 12)).grid(row=0, column=i)
            entry = tk.Entry(frame_form, font=("Arial", 12), width=12)
            entry.grid(row=1, column=i, padx=5)
            entries.append(entry)

        (self._entry_codigo, self._entry_tipo, self._entry_cant,
         self._entry_precio, self._entry_desc, self._entry_activa) = entries

        self._tabla.bind("<<TreeviewSelect>>", self._cargar_campos)

        # ── Botones ────────────────────────────────────────────────────────────
        frame_botones = tk.Frame(frame_form)
        frame_botones.grid(row=2, column=0, columnspan=6, pady=10)

        tk.Button(
            frame_botones, text="Guardar", font=("Arial", 14), bg="#4CAF50", fg="white",
            command=self._guardar,
        ).pack(side="left", padx=15)

        tk.Button(
            frame_botones, text="Editar", font=("Arial", 14), bg="#FF9800", fg="white",
            command=self._editar,
        ).pack(side="left", padx=15)

        tk.Button(
            frame_botones, text="Eliminar", font=("Arial", 14), bg="#E53935", fg="white",
            command=lambda: eliminar_promo(self._tabla),
        ).pack(side="left", padx=15)

        refrescar(self._tabla)

    def _cargar_campos(self, event: object = None) -> None:
        sel = self._tabla.selection()
        if not sel:
            return
        row = self._tabla.item(sel[0])["values"]
        for entry, value in zip(
            [self._entry_codigo, self._entry_tipo, self._entry_cant,
             self._entry_precio, self._entry_desc, self._entry_activa],
            row[1:],
        ):
            entry.delete(0, tk.END)
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

def abrir_gestion_promos(parent: tk.Misc | None = None) -> None:
    PromosWindow(parent or tk._default_root)
