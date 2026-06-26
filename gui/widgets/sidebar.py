import customtkinter as ctk
from PIL import Image, ImageTk # Para el logo de la sidebar
from database.connection import resource_path # Para cargar el logo
import gui.theme as T

# ── Constantes de sidebar (se moverán desde main_window.py) ──────────────────
_SW_COLLAPSED = 62
_SW_EXPANDED  = 224
_ANIM_STEP    = 14
_ANIM_MS      = 8
_COLLAPSE_MS  = 90

class Sidebar(ctk.CTkFrame):
    """
    Widget de barra lateral colapsable que contiene el logo, información de usuario
    y botones de navegación.
    """
    def __init__(self, master, usuario: str, jerarquia: str, btn_data: list, **kwargs) -> None:
        super().__init__(master, fg_color=T.SIDEBAR_BG, corner_radius=0, **kwargs)
        
        self.usuario = usuario
        self.jerarquia = jerarquia
        self.btn_data = btn_data # Datos de los botones para la sidebar
        
        self._sidebar_w = _SW_COLLAPSED # Ancho actual de la sidebar
        self._sidebar_btns: list[ctk.CTkButton] = [] # Referencias a los botones
        
        self._build_ui()
        self._bind_events()
        
    def _build_ui(self) -> None:
        self.pack(side="left", fill="y")
        self.pack_propagate(False) # Evita que se encoja
        self.configure(width=self._sidebar_w) # Establece el ancho inicial

        # Logo / nombre
        self._lbl_logo = ctk.CTkLabel(
            self, text="V&E",
            font=T.F_APP_TITLE, text_color=T.TEXT_ON_DARK,
        )
        self._lbl_logo.pack(pady=(22, 2))

        self._lbl_user = ctk.CTkLabel(
            self, text=self.usuario,
            font=T.F_SMALL, text_color=T.SUBTEXT_DARK,
        )
        self._lbl_user.pack(pady=(0, 2))

        ctk.CTkFrame(
            self, fg_color=T.SIDEBAR_HOV, height=1,
        ).pack(fill="x", padx=10, pady=10)

        # Espaciador superior para alinear botones
        espaciador_sidebar = ctk.CTkFrame(self, height=37, fg_color="transparent")
        espaciador_sidebar.pack(fill="x")

        # Botones de navegación
        for icon, _label, color, hover, cmd in self.btn_data:
            btn = ctk.CTkButton(
                self,
                text=icon, command=cmd,
                fg_color=color, hover_color=hover,
                text_color=T.TEXT_ON_DARK,
                font=T.F_BTN_SIDE,
                anchor="center", height=44, corner_radius=6,
            )
            btn.pack(fill="x", padx=8, pady=3)
            self._sidebar_btns.append(btn)

    def _bind_events(self) -> None:
        # Bind hover en el frame y en cada botón
        self.bind("<Enter>", self._on_sidebar_enter)
        self.bind("<Leave>", self._on_sidebar_leave)
        for btn in self._sidebar_btns:
            btn.bind("<Enter>", self._on_sidebar_enter)
            btn.bind("<Leave>", self._on_sidebar_leave)

    def _on_sidebar_enter(self, event=None) -> None:
        """Expande la sidebar cuando el mouse entra."""
        if hasattr(self, "_collapse_after"):
            self.master.after_cancel(self._collapse_after)
            del self._collapse_after
        self._set_sidebar_labels(expanded=True)
        self._animate_sidebar(_SW_EXPANDED)

    def _on_sidebar_leave(self, event=None) -> None:
        """Inicia el temporizador para colapsar la sidebar cuando el mouse sale."""
        if not hasattr(self, "_collapse_after"):
            self._collapse_after = self.master.after(_COLLAPSE_MS, self._check_collapse)

    def _check_collapse(self) -> None:
        """Verifica si el mouse realmente salió de la sidebar antes de colapsar."""
        if hasattr(self, "_collapse_after"):
            del self._collapse_after
        
        # Obtiene la posición actual del puntero del mouse
        px, py = self.winfo_pointerxy()
        # Obtiene las coordenadas de la esquina superior izquierda de la sidebar
        sx = self.winfo_rootx()
        sy = self.winfo_rooty()
        
        # Verifica si el puntero está dentro de los límites de la sidebar
        inside = (sx <= px < sx + self.winfo_width() and
                  sy <= py < sy + self.winfo_height())
        
        if not inside:
            self._set_sidebar_labels(expanded=False)
            self._animate_sidebar(_SW_COLLAPSED)

    def _animate_sidebar(self, target: int) -> None:
        """Anima la sidebar para expandirse o colapsarse suavemente."""
        if hasattr(self, "_anim_after"):
            self.master.after_cancel(self._anim_after)
        
        current = self._sidebar_w # Usamos el ancho rastreado, no winfo_width()
        if current == target:
            return # Ya está en el ancho objetivo

        step = _ANIM_STEP if target > current else -_ANIM_STEP
        next_w = current + step

        # Asegura que no nos pasemos del objetivo
        if (step > 0 and next_w > target) or (step < 0 and next_w < target):
            next_w = target
        
        self._sidebar_w = next_w
        self.configure(width=next_w) # Aplica el nuevo ancho al frame
        
        if next_w != target:
            # Si no hemos llegado al objetivo, programamos la siguiente iteración
            self._anim_after = self.master.after(_ANIM_MS, lambda: self._animate_sidebar(target))

    def _set_sidebar_labels(self, expanded: bool) -> None:
        """Actualiza el texto de los botones (icono o icono + etiqueta)."""
        for btn, (icon, label, *_) in zip(self._sidebar_btns, self.btn_data):
            if expanded:
                btn.configure(text=f"{icon}  {label}", anchor="w")
            else:
                btn.configure(text=icon, anchor="center")
