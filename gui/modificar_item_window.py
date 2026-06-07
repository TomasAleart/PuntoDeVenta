from __future__ import annotations
import customtkinter as ctk
from tkinter import messagebox
import gui.theme as T

class ModificarItemWindow(ctk.CTkToplevel):
    """Ventana modal flotante para editar la línea seleccionada del carrito."""

    def __init__(self, parent: ctk.CTk, item_data: dict, on_guardar: callable) -> None:
        super().__init__(parent)
        self.parent = parent
        self.item_data = item_data
        self.on_guardar = on_guardar

        # Configuración de la ventana contenedora
        self.title("Modificar Ítem")
        self.geometry("380x400")
        self.configure(fg_color=T.BG)  # Hegemonía de color de fondo
        self.resizable(False, False)

        # Comportamiento Modal Estricto
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
        
        # Forzar el foco inicial en el campo de cantidad
        self._entry_cantidad.focus_set()
        self.after(100, lambda: self._entry_cantidad.select_range(0, "end"))

    def _build_ui(self) -> None:
        # Cabecera con el nombre del producto
        lbl_producto = ctk.CTkLabel(
            self, text=self.item_data["nombre"][:28],
            font=(T.F_BODY_B[0], 18, "bold"), text_color=T.TEXT
        )
        lbl_producto.pack(pady=(20, 15), padx=20)

        # Contenedor del Formulario (superficie contrastante)
        form_frame = ctk.CTkFrame(self, fg_color=T.SURFACE, border_color=T.BORDER, border_width=1)
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # Configuración de rejilla del formulario
        form_frame.grid_columnconfigure(1, weight=1)

        # 1. Campo: Cantidad / Peso
        ctk.CTkLabel(form_frame, text="Cantidad / Peso:", font=T.F_BODY, text_color=T.TEXT_MUTED).grid(row=0, column=0, padx=15, pady=15, sticky="w")
        self._entry_cantidad = ctk.CTkEntry(form_frame, font=T.F_ENTRY, fg_color=T.BG, border_color=T.BORDER, text_color=T.TEXT, height=35)
        self._entry_cantidad.grid(row=0, column=1, padx=15, pady=15, sticky="ew")
        self._entry_cantidad.insert(0, str(self.item_data["cantidad"]))
        self._entry_cantidad.bind("<FocusIn>", lambda e: self._seleccionar_todo(self._entry_cantidad))

        # 2. Campo: Descuento (%)
        ctk.CTkLabel(form_frame, text="Descuento (%):", font=T.F_BODY, text_color=T.TEXT_MUTED).grid(row=1, column=0, padx=15, pady=15, sticky="w")
        self._entry_descuento = ctk.CTkEntry(form_frame, font=T.F_ENTRY, fg_color=T.BG, border_color=T.BORDER, text_color=T.TEXT, height=35)
        self._entry_descuento.grid(row=1, column=1, padx=15, pady=15, sticky="ew")
        self._entry_descuento.insert(0, str(self.item_data["descuento"]))
        self._entry_descuento.bind("<FocusIn>", lambda e: self._seleccionar_todo(self._entry_descuento))

        # 3. Campo: Recargo (%)
        ctk.CTkLabel(form_frame, text="Recargo (%):", font=T.F_BODY, text_color=T.TEXT_MUTED).grid(row=2, column=0, padx=15, pady=15, sticky="w")
        self._entry_recargo = ctk.CTkEntry(form_frame, font=T.F_ENTRY, fg_color=T.BG, border_color=T.BORDER, text_color=T.TEXT, height=35)
        self._entry_recargo.grid(row=2, column=2, padx=15, pady=15, sticky="ew") if False else self._entry_recargo.grid(row=2, column=1, padx=15, pady=15, sticky="ew")
        self._entry_recargo.insert(0, str(self.item_data["recargo"]))
        self._entry_recargo.bind("<FocusIn>", lambda e: self._seleccionar_todo(self._entry_recargo))

        # Bind del Enter para guardar rápido
        self._entry_cantidad.bind("<Return>", lambda e: self._on_guardar_click())
        self._entry_descuento.bind("<Return>", lambda e: self._on_guardar_click())
        self._entry_recargo.bind("<Return>", lambda e: self._on_guardar_click())

        # Contenedor de Botones de Acción
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        btn_cancelar = ctk.CTkButton(
            btn_frame, text="Cancelar", command=self.destroy,
            fg_color=T.NEUTRAL, hover_color="#4B5563", text_color=T.TEXT_ON_DARK, height=40
        )
        btn_cancelar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_guardar = ctk.CTkButton(
            btn_frame, text="Confirmar", command=self._on_guardar_click,
            fg_color=T.PRIMARY, hover_color="#1D4ED8", text_color=T.TEXT_ON_DARK, height=40
        )
        btn_guardar.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _seleccionar_todo(self, entry: ctk.CTkEntry) -> None:
        """UX Fix: Sombrea todo el texto del campo para sobreescribir sin borrar a mano."""
        self.after(50, lambda: entry.select_range(0, "end"))

    def _on_guardar_click(self) -> None:
        try:
            cantidad = float(self._entry_cantidad.get().strip())
            descuento = float(self._entry_descuento.get().strip())
            recargo = float(self._entry_recargo.get().strip())

            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a cero.")
            if not (0 <= descuento <= 100) or not (0 <= recargo <= 100):
                raise ValueError("Los porcentajes deben estar entre 0 y 100.")

            # Devolvemos el diccionario limpio al callback de la MainWindow
            nuevos_valores = {
                "cantidad": cantidad,
                "descuento": descuento,
                "recargo": recargo
            }
            self.on_guardar(nuevos_valores)
            self.destroy()

        except ValueError as e:
            messagebox.showerror("Datos Inválidos", f"Verifique los campos: {e}", parent=self)