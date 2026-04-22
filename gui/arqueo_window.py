from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, ttk
from database.connection import get_db
from database.caja_db import obtener_caja_actual
from database.arqueo_db import insertar_arqueo
from reports.arqueo_report import imprimir_arqueos
from core.logic_arqueos import buscar


class ArqueoWindow(tk.Toplevel):
    """Ventana para registrar un arqueo de caja."""

    def __init__(self, parent: tk.Misc, usuario: str) -> None:
        super().__init__(parent)
        self.title("Arqueo de Caja")
        self.geometry("350x220")
        self.grab_set()

        self._usuario = usuario
        self._build_ui()

    def _build_ui(self) -> None:
        tk.Label(self, text="Caja real contada:", font=("Arial", 12)).pack(pady=10)
        self._entry_real = tk.Entry(self, font=("Arial", 12))
        self._entry_real.pack()
        self._entry_real.focus_set()

        frame_botones = tk.Frame(self)
        frame_botones.pack(pady=20)

        tk.Button(
            frame_botones, text="Confirmar", font=("Arial", 12), width=12,
            bg="#4CAF50", fg="white", command=self._guardar,
        ).pack(side="left", padx=10)

        tk.Button(
            frame_botones, text="Ver arqueos", font=("Arial", 12), width=12,
            bg="#2196F3", fg="white", command=self._ver_arqueos,
        ).pack(side="left", padx=10)

    def _guardar(self) -> None:
        try:
            caja_real = float(self._entry_real.get())
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido.", parent=self)
            return

        with get_db() as conn:
            caja_sis = obtener_caja_actual(conn)
            diferencia = caja_real - caja_sis
            insertar_arqueo(conn, self._usuario, caja_sis, caja_real, diferencia)

        messagebox.showinfo(
            "Arqueo registrado",
            f"Caja sistema: ${caja_sis:.2f}\n"
            f"Caja real: ${caja_real:.2f}\n"
            f"Diferencia:  ${diferencia:.2f}",
            parent=self,
        )
        self.destroy()

    def _ver_arqueos(self) -> None:
        ArqueoConsultaWindow(self)


class ArqueoConsultaWindow(tk.Toplevel):
    """Ventana para filtrar y consultar arqueos registrados."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("Consulta de Arqueos")
        self.geometry("750x480")
        self.grab_set()
        self._build_ui()

    def _build_ui(self) -> None:
        tk.Label(self, text="Filtrar Arqueos", font=("Arial", 16, "bold")).pack(pady=5)

        frame_filtros = tk.Frame(self)
        frame_filtros.pack(pady=5)

        tk.Label(frame_filtros, text="Desde (YYYY-MM-DD):").grid(row=0, column=0, padx=5)
        self._entry_desde = tk.Entry(frame_filtros, width=12)
        self._entry_desde.grid(row=0, column=1, padx=5)

        tk.Label(frame_filtros, text="Hasta (YYYY-MM-DD):").grid(row=0, column=2, padx=5)
        self._entry_hasta = tk.Entry(frame_filtros, width=12)
        self._entry_hasta.grid(row=0, column=3, padx=5)

        tk.Label(frame_filtros, text="Usuario:").grid(row=0, column=4, padx=5)
        self._entry_usuario = tk.Entry(frame_filtros, width=10)
        self._entry_usuario.grid(row=0, column=5, padx=5)

        frame_tabla = tk.Frame(self)
        frame_tabla.pack(fill="both", expand=True, pady=5)

        columnas = ("fecha", "usuario", "sistema", "real", "diferencia")
        self._tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        for col in columnas:
            self._tabla.heading(col, text=col.capitalize())
            self._tabla.column(col, width=130)
        self._tabla.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(frame_tabla, orient="vertical", command=self._tabla.yview)
        sb.pack(side="right", fill="y")
        self._tabla.configure(yscrollcommand=sb.set)

        self._label_totales = tk.Label(self, text="", font=("Arial", 12))
        self._label_totales.pack(pady=4)

        frame_botones = tk.Frame(self)
        frame_botones.pack(pady=10)

        tk.Button(
            frame_botones, text="Buscar", font=("Arial", 12), width=14,
            bg="#2196F3", fg="white", command=self._buscar,
        ).pack(side="left", padx=10)

        tk.Button(
            frame_botones, text="Imprimir arqueos", font=("Arial", 12), width=18,
            bg="#4CAF50", fg="white", command=lambda: imprimir_arqueos(self._tabla),
        ).pack(side="left", padx=10)

    def _buscar(self) -> None:
        buscar(
            self._tabla,
            self._entry_desde,
            self._entry_hasta,
            self._entry_usuario,
            self._label_totales,
        )


# ── Función de compatibilidad ─────────────────────────────────────────────────

def abrir_arqueo(usuario: str, parent: tk.Misc | None = None) -> None:
    ArqueoWindow(parent or tk._default_root, usuario)
