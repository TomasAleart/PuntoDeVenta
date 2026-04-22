from __future__ import annotations
import sqlite3
from datetime import datetime


def insertar_arqueo(
    conn: sqlite3.Connection,
    usuario_actual: str,
    caja_sis: float,
    caja_real: float,
    diferencia: float,
) -> None:
    """Inserta un registro de arqueo usando la conexión provista por el llamador.
    La gestión de commit/rollback/close queda a cargo del contexto get_db() del llamador.
    """
    c = conn.cursor()
    c.execute("""
        INSERT INTO arqueos (fecha, usuario, caja_sistema, caja_real, diferencia)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        usuario_actual,
        caja_sis,
        caja_real,
        diferencia,
    ))
