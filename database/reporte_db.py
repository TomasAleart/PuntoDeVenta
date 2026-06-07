# 🔌 Importamos tu context manager centralizado
from database.connection import get_db

def consultar_top_productos(fecha_limite: str) -> list[tuple[str, float]]:
    """Ejecuta la consulta utilizando la conexión centralizada en AppData 
    para traer el Top 10 de productos más vendidos.
    """
    query = """
        SELECT 
            vd.nombre, 
            SUM(CASE WHEN vd.peso > 0 THEN vd.peso ELSE vd.cantidad END) as total_vendido
        FROM ventas_detalle vd
        JOIN ventas v ON vd.id_venta = v.id
        WHERE v.fecha >= ?
        GROUP BY vd.codigo, vd.nombre
        ORDER BY total_vendido DESC
        LIMIT 10;
    """

    # Usamos tu arquitectura para asegurar que lea la DB correcta en AppData
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (fecha_limite,))
        resultados = cursor.fetchall()
        
    return resultados