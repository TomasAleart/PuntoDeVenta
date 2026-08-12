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
    # Argumentos que deben ir al CTkEntry interno, no al CTkFrame contenedor.
    _ENTRY_KWARGS = (
        "fg_color", "text_color", "font", "border_color",
        "border_width", "corner_radius", "placeholder_text",
        "placeholder_text_color", "justify",
    )

    def __init__(self, master, on_select_callback, **kwargs) -> None:
        # Separamos los kwargs de estilo del Entry de los del Frame.
        self._entry_kwargs = {
            k: kwargs.pop(k) for k in self._ENTRY_KWARGS if k in kwargs
        }
        # El ancho lo controlamos nosotros: se aplica al Entry y al panel de sugerencias.
        self._width = kwargs.pop("width", 280)
        super().__init__(master, width=self._width, fg_color="transparent", **kwargs)

        self.on_select_callback = on_select_callback
        
        # Estado interno para las sugerencias
        self._ignore_next_focus_out = False # Para evitar que se oculte al hacer clic en sugerencia

        self._build_ui()
    
    def _build_ui(self) -> None:
        # El Entry principal donde el usuario escribe.
        # Valores por defecto; los kwargs pasados por el llamante los sobrescriben.
        entry_opts = dict(
            justify="center",
            placeholder_text="Ingrese código...",
            fg_color=T.SURFACE, text_color=T.TEXT,
            border_color=T.BORDER,
            width=self._width,
            height=44,
        )
        entry_opts.update(self._entry_kwargs)  # kwargs de inicialización al Entry interno
        self.entry_widget = ctk.CTkEntry(self, **entry_opts)
        # El Entry pide su ancho (self._width); el frame se ajusta a él.
        self.entry_widget.pack(fill="x", expand=True)
        self.entry_widget.bind("<KeyRelease>", self._on_keyrelease)
        self.entry_widget.bind("<FocusOut>", self._on_focus_out)
        # Enter tiene su propio manejador: funciona haya o no panel de sugerencias visible.
        self.entry_widget.bind("<Return>", self._on_return)
        
        # Frame flotante para las sugerencias (inicialmente oculto).
        # Su master es la VENTANA de nivel superior para que flote por encima de
        # todo (carrito incluido) y NO quede recortado por el frame contenedor.
        self._overlay_master = self.winfo_toplevel()
        # Altura calculada para mostrar ~3 opciones; el resto se ve al hacer scroll.
        # Cada botón mide 30px de alto + 2px de pady => 32px por fila.
        self._alto_fila = 32
        self._filas_visibles = 3
        self._frame_sugerencias = ctk.CTkScrollableFrame(
            self._overlay_master,
            width=self._width, # Mismo ancho que el campo de código
            height=self._alto_fila * self._filas_visibles,
            fg_color="#2B2B2B",
            corner_radius=6
        )
        self._frame_sugerencias.place_forget()

    def _on_return(self, event: object = None) -> str:
        """Procesa Enter: elige la sugerencia resaltada, o envía el texto tal cual.

        Funciona SIEMPRE, esté o no visible el panel de sugerencias (indispensable
        para códigos exactos / lectores de código de barras que terminan en Enter).
        """
        panel_visible = bool(self._frame_sugerencias.winfo_manager())
        index_actual = getattr(self, "_index_sugerencia_actual", -1)

        if panel_visible and index_actual != -1:
            codigo_sel = self._sugerencias_actuales[index_actual][0]
            self._seleccionar_sugerencia(codigo_sel)
        else:
            texto = self.entry_widget.get().strip()
            self._frame_sugerencias.place_forget()
            if texto:
                self.on_select_callback(texto)
        return "break"  # Evita que el evento se propague y re-dispare KeyRelease

    def _on_keyrelease(self, event: object) -> None:
        """Se ejecuta cada vez que el usuario escribe o interactúa con el teclado en el campo."""

        # Enter se maneja en _on_return; acá lo ignoramos para no re-consultar la BD.
        if event.keysym == "Return":
            return

        # INTERCEPTAR NAVEGACIÓN POR TECLADO (Solo si el panel de sugerencias está abierto)
        if event.keysym in ("Up", "Down", "Escape") and self._frame_sugerencias.winfo_manager():
            cant_sugerencias = len(self._botones_sugerencias)
            if cant_sugerencias == 0:
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
        # Aseguramos que quede por encima del resto de los widgets.
        self._frame_sugerencias.lift()
    
    def _actualizar_resaltado_sugerencias(self) -> None:
        """Cambia visualmente el botón seleccionado por teclado y desplaza el scrollbar
        para que la opción resaltada quede siempre visible dentro del panel."""
        for idx, btn in enumerate(self._botones_sugerencias):
            btn.configure(fg_color="#3A4A5E" if idx == self._index_sugerencia_actual else "transparent")

        self._asegurar_visible(self._index_sugerencia_actual)

    def _asegurar_visible(self, idx: int) -> None:
        """Desplaza el canvas del panel para que la fila `idx` entre en la ventana visible."""
        cant_totales = len(self._botones_sugerencias)
        if cant_totales == 0 or idx < 0:
            return

        # El canvas interno de CTkScrollableFrame se llama _parent_canvas.
        canvas = getattr(self._frame_sugerencias, "_parent_canvas", None)
        if canvas is None:
            return

        # Fracción visible actual (arriba, abajo) del contenido total.
        try:
            top, bottom = canvas.yview()
        except Exception:
            return

        vista = bottom - top                 # porción visible (aprox. filas_visibles/total)
        fila = idx / cant_totales            # borde superior de la fila resaltada
        fila_fin = (idx + 1) / cant_totales  # borde inferior de la fila resaltada

        if fila < top:
            # La fila quedó por encima: la llevamos al tope de la vista.
            canvas.yview_moveto(fila)
        elif fila_fin > bottom:
            # La fila quedó por debajo: la llevamos al fondo de la vista.
            canvas.yview_moveto(max(0.0, fila_fin - vista))

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
