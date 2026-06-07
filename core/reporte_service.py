from datetime import datetime, timedelta
from database.reporte_db import consultar_top_productos

def obtener_top_productos(filtro: str) -> list[tuple[str, float]]:
    """Lógica de negocio: Calcula la fecha de inicio según el filtro 
    y delega la consulta a la capa de datos.
    """
    ahora = datetime.now()
    
    if filtro == "semana":
        fecha_inicio = ahora - timedelta(days=7)
    elif filtro == "mes":
        fecha_inicio = ahora - timedelta(days=30)
    elif filtro == "anio":
        fecha_inicio = ahora - timedelta(days=365)
    else:
        fecha_inicio = datetime(2000, 1, 1) # Histórico completo

    # Convertimos a string con el formato que entiende SQLite
    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d %H:%M:%S")

    # Delegamos la responsabilidad de tocar la DB al repositorio
    return consultar_top_productos(fecha_inicio_str)