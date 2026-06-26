import customtkinter as ctk
import tkinter as tk # Necesario para tk.END, tk.NORMAL, tk.DISABLED
import time # Para el retardo de FocusOut

from core.producto_service import obtener_sugerencias_busqueda
import gui.theme as T

class AutoCompleteEntry(ctk.CTkFrame):
    """
    Un widget de entrada de texto personalizado con funcionalidad de autocompletado
    para buscar productos y mostrar sugerencias.
    """
    def __init__(self, master, on_select_callback, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.on_select_callback = on_select_callback
        
        # Estado interno para las sugerencias
        self._sugerencias_actuales = []
        self._botones_sugerencias = []
        self._index_sugerencia_actual = -1
        self._ignore_next_focus_out = False # Para evitar que se oculte al hacer clic en sugerencia

        self._build_ui()
    
    def _build_ui(self) -> None:
        # El Entry principal donde el usuario escribe
        self.entry_widget = ctk.CTkEntry(
            self, 
            justify="center",
            placeholder_text="Ingrese código...",
            fg_color=T.SURFACE, text_color=T.TEXT,
            border_color=T.BORDER, 
            height=44,
            **self._kwargs # Pasa los kwargs de inicialización al Entry interno
        )
        self.entry_widget.pack(fill="x", expand=True) # Asegura que tome el tamaño del frame padre
        self.entry_widget.bind("<KeyRelease>", self._on_keyrelease)
        self.entry_widget.bind("<FocusOut>", self._on_focus_out)
        self.entry_widget.bind("<Return>", lambda e: self._on_keyrelease(e)) # Necesario para procesar Enter si no hay sugerencias
        
        # Frame flotante para las sugerencias (inicialmente oculto)
        self._frame_sugerencias = ctk.CTkScrollableFrame(
            self.master, # ¡Importante! El master de las sugerencias es el master de la MainWindow, no 'self'
            width=self.entry_widget.cget("width"), # Usa el ancho del Entry como referencia
            height=180,
            fg_color="#2B2B2B", 
            corner_radius=6
        )
        self._frame_sugerencias.place_forget()

    def _on_keyrelease(self, event: object) -> None:
        """Se ejecuta cada vez que el usuario escribe o interactúa con el teclado en el campo."""
        
        # INTERCEPTAR NAVEGACIÓN POR TECLADO (Solo si el panel de sugerencias está abierto)
        if event.keysym in ("Up", "Down", "Return", "Escape") and self._frame_sugerencias.winfo_manager():
            cant_sugerencias = len(self._botones_sugerencias)
            if cant_sugerencias == 0:
                if event.keysym == "Return":
                    # Si no hay sugerencias, pero se presiona Enter, se comporta como si se hubiera introducido un código
                    self.on_select_callback(self.entry_widget.get().strip())
                return

            if event.keysym == "Down":
                self._index_sugerencia_actual = (self._index_sugerencia_actual + 1) % cant_sugerencias
                self._actualizar_resaltado_sugerencias()
            
            elif event.keysym == "Up":
                if self._index_sugerencia_actual <= 0:
                    self._index_sugerencia_actual = cant_sugerencias - 1
                else:
                    self._index_sugerencia_actual -= 1
                self._actualizar_resaltado_sugerencias()
            
            elif event.keysym == "Return":
                if self._index_sugerencia_actual != -1:
                    codigo_sel = self._sugerencias_actuales[self._index_sugerencia_actual][0]
                    self._seleccionar_sugerencia(codigo_sel)
                else:
                    # Si se presiona Enter y no hay sugerencia resaltada, procesa el texto actual
                    self.on_select_callback(self.entry_widget.get().strip())
            
            elif event.keysym == "Escape":
                self._frame_sugerencias.place_forget()
                
            return # Cortamos la ejecución acá para que no vuelva a consultar la Base de Datos

        # 2. LÓGICA DE TIPEO NORMAL (Si escribe letras o borra)
        texto = self.entry_widget.get().strip()

        if len(texto) < 2:
            self._frame_sugerencias.place_forget()
            return

        sugerencias = obtener_sugerencias_busqueda(texto)

        # Limpiamos los botones anteriores
        for child in self._frame_sugerencias.winfo_children():
            child.destroy()

        if not sugerencias:
            self._frame_sugerencias.place_forget()
            return

        # Guardamos los estados actuales en la instancia para poder navegar por índice
        self._sugerencias_actuales = sugerencias
        self._botones_sugerencias = []
        self._index_sugerencia_actual = -1 # -1 significa que nada está seleccionado aún

        # Poblamos el panel con las nuevas sugerencias encontradas
        for codigo, nombre in sugerencias:
            btn = ctk.CTkButton(
                self._frame_sugerencias,
                text=nombre,
                anchor="w",
                fg_color="transparent",
                text_color="#FFFFFF",
                hover_color="#3A4A5E",  # Tu gris azulado de la sidebar
                height=30,
                command=lambda c=codigo: self._seleccionar_sugerencia(c)
            )
            btn.pack(fill="x", padx=2, pady=1)
            self._botones_sugerencias.append(btn) # Guardamos la referencia del botón

        # Posicionamiento automático inteligente
        # Usamos self.entry_widget para referenciar su posición, ya que el AutocompleteEntry es su padre
        self._frame_sugerencias.place(
            in_=self.entry_widget,
            relx=0.5,
            rely=1.0,
            x=0,
            y=4,
            anchor="n"
        )
    
    def _actualizar_resaltado_sugerencias(self) -> None:
        """Cambia visualmente el botón seleccionado por teclado y desplaza el scrollbar."""
        for idx, btn in enumerate(self._botones_sugerencias):
            if idx == self._index_sugerencia_actual:
                btn.configure(fg_color="#3A4A5E")
                
                try:
                    cant_totales = len(self._botones_sugerencias)
                    if cant_totales > 0:
                        posicion_fraccion = idx / cant_totales
                        self._frame_sugerencias._canvas.yview_moveto(max(0.0, posicion_fraccion - 0.1))
                except Exception:
                    pass
            else:
                btn.configure(fg_color="transparent")

    def _seleccionar_sugerencia(self, codigo: str) -> None:
        """Inserta el código del producto seleccionado y dispara el callback del padre."""
        self._ignore_next_focus_out = True # Evita que FocusOut oculte las sugerencias inmediatamente
        self.entry_widget.delete(0, tk.END)
        self.entry_widget.insert(0, codigo)
        self._frame_sugerencias.place_forget()
        
        # Ejecutar el callback del padre
        self.on_select_callback(codigo)
        self.master.after(100, lambda: setattr(self, '_ignore_next_focus_out', False)) # Resetear después de un tiempo
    
    def _on_focus_out(self, event) -> None:
        # Si el foco va al frame de sugerencias o a un botón de sugerencia, no ocultar
        if self._ignore_next_focus_out:
            return

        # Para asegurar que se oculte incluso si el foco va a otro widget
        # Usamos after para dar tiempo al clic en el botón de sugerencia
        self.master.after(200, self._ocultar_sugerencias_seguro)

    def _ocultar_sugerencias_seguro(self) -> None:
        """Oculta de forma segura el frame si cambia el foco de la aplicación."""
        if self._frame_sugerencias.winfo_exists() and not self._ignore_next_focus_out:
            self._frame_sugerencias.place_forget()

    def get(self) -> str:
        """Obtiene el texto actual del entry."""
        return self.entry_widget.get().strip()

    def clear(self) -> None:
        """Limpia el entry."""
        self.entry_widget.delete(0, tk.END)

    def focus(self) -> None:
        """Pone el foco en el entry."""
        self.entry_widget.focus_set()
