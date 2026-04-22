from __future__ import annotations
import sqlite3
from datetime import datetime
from database.connection import get_db
from core.logic_ventas import calcular_total, calcular_caja_actual
from models.carrito import Carrito
from exceptions import StockInsuficiente


def registrar_venta(usuario: str, carrito: Carrito, descuento_pct: float = 0.0) -> None:
    """Persiste la venta completa en una única transacción atómica.

    Dentro de la misma transacción: decrementa el stock de cada ítem por unidad,
    inserta la cabecera en `ventas` e inserta cada línea en `ventas_detalle`.
    Si cualquier operación falla, toda la transacción se revierte.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        total_final = calcular_total(carrito, descuento_pct)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        venta = obtener_ultima_venta(cursor)
        ultima_caja = obtener_ultima_caja(cursor)
        caja_actual = calcular_caja_actual(venta, ultima_caja)

        for item in carrito.values():
            if item.tipo == "unidad":
                cursor.execute(
                    "UPDATE productos SET stock = stock - ? WHERE codigo_barras = ? AND stock >= ?",
                    (item.cantidad, item.codigo, item.cantidad),
                )
                if cursor.rowcount == 0:
                    raise StockInsuficiente(f"Stock insuficiente para '{item.nombre}'.")

        id_venta = insertar_venta(cursor, fecha, total_final, usuario, caja_actual)
        insertar_detalle(cursor, id_venta, carrito)


def obtener_ultima_venta(cursor: sqlite3.Cursor) -> tuple | None:
    cursor.execute("""
        SELECT fecha, caja_inicial + total
        FROM ventas
        ORDER BY fecha DESC
        LIMIT 1
    """)
    return cursor.fetchone()


def obtener_ultima_caja(cursor: sqlite3.Cursor) -> tuple | None:
    cursor.execute("""
        SELECT fecha_inicio, caja_final
        FROM caja
        ORDER BY fecha_inicio DESC
        LIMIT 1
    """)
    return cursor.fetchone()


def insertar_venta(
    cursor: sqlite3.Cursor,
    fecha: str,
    total_final: float,
    usuario: str,
    caja_actual: float,
) -> int:
    cursor.execute("""
        INSERT INTO ventas (fecha, total, vendedor, caja_inicial)
        VALUES (?, ?, ?, ?)
    """, (fecha, total_final, usuario, caja_actual))
    return cursor.lastrowid


def insertar_detalle(cursor: sqlite3.Cursor, id_venta: int, carrito: Carrito) -> None:
    for item in carrito.values():
        cursor.execute("""
            INSERT INTO ventas_detalle
            (id_venta, codigo, nombre, cantidad, peso,
             precio_unitario, subtotal, promo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_venta,
            item.codigo,
            item.nombre,
            item.cantidad,
            item.peso,
            item.precio_unitario,
            item.subtotal,
            item.promo,
        ))
