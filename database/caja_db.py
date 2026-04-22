from __future__ import annotations
import sqlite3
from datetime import datetime
from database.connection import get_db


def insertar_caja_inicial(monto: float, usuario_actual: str) -> None:
    with get_db() as conn:
        conn.cursor().execute("""
            INSERT INTO caja (fecha_inicio, caja_inicial, caja_final, usuario, tipo)
            VALUES (?, ?, ?, ?, 'INICIAL')
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            monto,
            monto,
            usuario_actual,
        ))


def obtener_caja_actual(conn: sqlite3.Connection) -> float:
    """Calcula el saldo actual de caja reutilizando una conexión abierta."""
    c = conn.cursor()

    c.execute("""
        SELECT fecha_inicio, caja_final
        FROM caja
        ORDER BY fecha_inicio DESC
        LIMIT 1
    """)
    ultima_caja = c.fetchone()

    if not ultima_caja:
        return 0.0

    fecha_caja, caja_base = ultima_caja

    c.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM ventas
        WHERE fecha > ?
    """, (fecha_caja,))

    total_ventas = c.fetchone()[0]
    return float(caja_base) + float(total_ventas)


def actualizar_caja_db(monto: float, usuario_actual: str) -> tuple[float, float]:
    with get_db() as conn:
        caja_actual = obtener_caja_actual(conn)
        caja_nueva = caja_actual + monto
        conn.cursor().execute("""
            INSERT INTO caja (fecha_inicio, caja_inicial, caja_final, usuario, tipo)
            VALUES (?, ?, ?, ?, 'MOVIMIENTO')
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            caja_actual,
            caja_nueva,
            usuario_actual,
        ))
    return caja_actual, caja_nueva
