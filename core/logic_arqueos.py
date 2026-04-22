from __future__ import annotations
from typing import Any
from database.connection import get_db


def buscar(
    tabla: Any,
    entry_desde: Any,
    entry_hasta: Any,
    entry_usuario: Any,
    label_totales: Any,
) -> None:
    tabla.delete(*tabla.get_children())

    desde = entry_desde.get().strip()
    hasta = entry_hasta.get().strip()
    usuario = entry_usuario.get().strip()

    query = """
        SELECT fecha, usuario, caja_sistema, caja_real, diferencia
        FROM arqueos
        WHERE 1=1
    """
    params: list[str] = []

    if desde:
        query += " AND fecha >= ?"
        params.append(desde + " 00:00:00")
    if hasta:
        query += " AND fecha <= ?"
        params.append(hasta + " 23:59:59")
    if usuario:
        query += " AND usuario = ?"
        params.append(usuario)

    with get_db() as conn:
        c = conn.cursor()
        c.execute(query, params)
        filas = c.fetchall()

    total_pos = 0.0
    total_neg = 0.0

    for fecha, user, sis, real, dif in filas:
        tabla.insert("", "end", values=(fecha, user, sis, real, dif))
        if dif >= 0:
            total_pos += dif
        else:
            total_neg += dif

    label_totales.config(
        text=f"Diferencia positiva total: ${total_pos:.2f}   -   Diferencia negativa total: ${total_neg:.2f}"
    )
