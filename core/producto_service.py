# Importamos la función que acabamos de escribir en la capa de datos
from database.productos_db import buscar_productos_por_termino

def obtener_sugerencias_busqueda(termino: str) -> list[tuple[str, str]]:
    """Lógica de negocio para el autocompletado de productos.
    
    Recibe el texto que escribe el usuario, puede aplicar filtros o 
    reglas adicionales, y delega la búsqueda a la base de datos.
    """
    # Aquí podrías en un futuro limpiar caracteres extraños, 
    # forzar minúsculas o filtrar productos discontinuados.
    return buscar_productos_por_termino(termino)