from __future__ import annotations
from typing import Any
from database.connection import get_db


def refrescar(tabla: Any) -> None:
    tabla.delete(*tabla.get_children())
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, codigo_producto, tipo, cantidad_min,
                    precio_promo, descuento, activa
            FROM promociones
        """)
        filas = c.fetchall()
    for fila in filas:
        tabla.insert("", "end", values=fila)


def guardar_promo(tabla: Any, entry_codigo: Any, entry_tipo: Any, entry_cant: Any, entry_precio: Any, entry_desc: Any, entry_activa: Any) -> None:
    with get_db() as conn:
        conn.cursor().execute("""
            INSERT INTO promociones
            (codigo_producto,tipo,cantidad_min,precio_promo,descuento,activa)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            entry_codigo.get().strip(),
            entry_tipo.get().strip(),
            entry_cant.get().strip(),
            entry_precio.get().strip(),
            entry_desc.get().strip(),
            entry_activa.get().strip() or "1",
        ))
    refrescar(tabla)


def eliminar_promo(tabla: Any) -> None:
    sel = tabla.selection()
    if not sel:
        return
    id_promo = tabla.item(sel[0])["values"][0]
    with get_db() as conn:
        conn.cursor().execute("DELETE FROM promociones WHERE id=?", (id_promo,))
    refrescar(tabla)


def editar_promo(tabla: Any, entry_codigo: Any, entry_tipo: Any, entry_cant: Any, entry_precio: Any, entry_desc: Any, entry_activa: Any) -> None:
    sel = tabla.selection()
    if not sel:
        return
    id_promo = tabla.item(sel[0])["values"][0]
    with get_db() as conn:
        conn.cursor().execute("""
            UPDATE promociones
            SET codigo_producto=?, tipo=?, cantidad_min=?,
                precio_promo=?, descuento=?, activa=?
            WHERE id=?
        """, (
            entry_codigo.get().strip(),
            entry_tipo.get().strip(),
            entry_cant.get().strip(),
            entry_precio.get().strip(),
            entry_desc.get().strip(),
            entry_activa.get().strip(),
            id_promo,
        ))
    refrescar(tabla)
