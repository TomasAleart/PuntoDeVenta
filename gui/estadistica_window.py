import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# 🔌 Conexión real con tu capa de negocio
from core.reporte_service import obtener_top_productos

class EstadisticaWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Estadísticas de Ventas")
        self.geometry("800x600")
        
        # Centrar la ventana respecto a la principal si es posible
        self.transient(parent)
        self.grab_set() # Bloquea la ventana principal
        
        self.canvas = None
        self.lbl_sin_datos = None # Guardamos referencia para el estado vacío
        
        self._setup_ui()
        self._actualizar_grafico("mes") # Filtro por defecto al abrir

    def _setup_ui(self):
        # 1. Panel Superior de Filtros
        frame_filtros = ctk.CTkFrame(self, height=60)
        # 🛠️ CORRECCIÓN: Se cambió 'top=20' por 'pady=20' ya que 'top' no existe en .pack()
        frame_filtros.pack(fill="x", padx=20, pady=20, side="top")
        
        label = ctk.CTkLabel(frame_filtros, text="Filtrar Período:", font=("Arial", 14, "bold"))
        label.pack(side="left", padx=15, pady=15)
        
        self.selector_periodo = ctk.CTkSegmentedButton(
            frame_filtros, 
            values=["Semana", "Mes", "Año", "Histórico"],
            command=self._on_cambio_filtro
        )
        self.selector_periodo.set("Mes")
        self.selector_periodo.pack(side="left", padx=10, pady=15)

        # 2. Contenedor para el Gráfico
        self.frame_grafico = ctk.CTkFrame(self)
        self.frame_grafico.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _on_cambio_filtro(self, value: str):
        mapeo = {"Semana": "semana", "Mes": "mes", "Año": "anio", "Histórico": "historico"}
        self._actualizar_grafico(mapeo[value])

    def _actualizar_grafico(self, filtro: str):
        # Limpiamos gráficos o mensajes anteriores
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
            
        if self.lbl_sin_datos:
            self.lbl_sin_datos.destroy()
            self.lbl_sin_datos = None

        # 1. 📊 Obtención de DATOS REALES desde la Base de Datos
        datos = obtener_top_productos(filtro)
        
        # Manejo de Estado Vacío: si el negocio no vendió nada en ese tiempo
        if not datos:
            self.lbl_sin_datos = ctk.CTkLabel(
                self.frame_grafico, 
                text="❌ No se registraron ventas en el período seleccionado.",
                font=("Arial", 14, "italic")
            )
            self.lbl_sin_datos.pack(expand=True)
            return

        productos = [item[0] for item in datos]
        cantidades = [item[1] for item in datos]

        # 2. Configuración de Matplotlib integrada a la estética oscura (#242424)
        fig, ax = plt.subplots(figsize=(6, 4), facecolor="#242424")
        ax.set_facecolor("#242424")
        
        # Color azul profesional para las barras
        bars = ax.barh(productos, cantidades, color="#1D4ED8")
        
        # Estética de ejes limpios (Estilo Minimalista)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#FFFFFF')
        ax.spines['bottom'].set_color('#FFFFFF')
        ax.tick_params(colors='#FFFFFF', labelsize=11)
        ax.set_title("Top 10 Productos Más Vendidos", color="#FFFFFF", fontsize=15, pad=20, fontweight="bold")
        ax.invert_yaxis() # Mantiene el producto #1 arriba

        # 3. Renderizado dinámico de etiquetas de valor al final de cada barra
        for bar in bars:
            width = bar.get_width()
            # Formateo inteligente: si es entero muestra sin decimales (unidades), si es flotante muestra 3 decimales (kilos)
            texto_cantidad = f"{int(width)}" if width % 1 == 0 else f"{width:.3f} kg"
            
            ax.text(
                width + (max(cantidades) * 0.01), # Separación proporcional al tamaño total
                bar.get_y() + bar.get_height()/2, 
                texto_cantidad, 
                va='center', 
                ha='left', 
                color='white', 
                fontsize=10,
                fontweight="bold"
            )

        plt.tight_layout()

        # 4. Embeber el Canvas de Matplotlib en la UI de CustomTkinter
        self.canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)
        
        # Liberamos memoria del objeto gráfico
        plt.close(fig)