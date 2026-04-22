from __future__ import annotations
from database.connection import get_db


def obtener_informe(fecha_desde: str, fecha_hasta: str, vendedor: str = "") -> list[tuple]:
    query = """
        SELECT fecha, 'VENTA', 'Venta', vendedor, total
        FROM ventas
        WHERE fecha BETWEEN ? AND ?
    """
    params: list[str] = [fecha_desde, fecha_hasta]

    if vendedor:
        query += " AND vendedor = ?"
        params.append(vendedor)

    query += """
        UNION ALL
        SELECT fecha_inicio, 'CAJA',
            CASE
                WHEN tipo='INICIAL' THEN 'Caja inicial del sistema'
                ELSE 'Movimiento de caja'
            END,
            usuario,
            CASE
                WHEN tipo='INICIAL' THEN caja_inicial
                ELSE (caja_final - caja_inicial)
            END
        FROM caja
        WHERE fecha_inicio BETWEEN ? AND ?
        ORDER BY fecha
    """
    params.extend([fecha_desde, fecha_hasta])

    with get_db() as conn:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchall()


def obtener_caja_inicial(fecha: str) -> float:
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT caja_inicial FROM ventas WHERE fecha = ? LIMIT 1",
            (fecha,),
        )
        row = c.fetchone()
    return float(row[0]) if row else 0.0


def base_calculo(fecha_hasta: str) -> tuple | None:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT fecha_inicio, caja_inicial
            FROM caja
            WHERE tipo='INICIAL'
            AND fecha_inicio <= ?
            ORDER BY fecha_inicio DESC
            LIMIT 1
        """, (fecha_hasta,))
        return c.fetchone()


def logica_caja_base(row: tuple | None, caja_inicial_mostrada: float) -> tuple[str | None, float]:
    if row:
        fecha_base, caja_base = row
    else:
        fecha_base = None
        caja_base = caja_inicial_mostrada
    return fecha_base, caja_base


def buscar_id_real(fecha: str) -> tuple | None:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, total
            FROM ventas
            WHERE fecha = ?
            LIMIT 1
        """, (fecha,))
        return c.fetchone()


def obtener_detalle(id_venta: int) -> list[tuple]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT codigo, nombre, cantidad, peso, precio_unitario, subtotal, promo
            FROM ventas_detalle
            WHERE id_venta = ?
        """, (id_venta,))
        return c.fetchall()


def eliminar_detalle(id_venta: int) -> None:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM ventas_detalle WHERE id_venta = ?", (id_venta,))
        c.execute("DELETE FROM ventas WHERE id = ?", (id_venta,))
