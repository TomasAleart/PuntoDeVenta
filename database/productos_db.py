from __future__ import annotations
import sqlite3
from database.connection import get_db
from core.logic_gestion import calcular_precio_nuevo, calcular_stock
from models.producto import Producto
from models.promocion import Promocion
from exceptions import ProductoNoEncontrado, ProductoExistente


def obtener_productos() -> list[tuple]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT codigo_barras, nombre, precio, PrecioKilo, stock FROM productos")
        return cursor.fetchall()


def agregar_producto(codigo: str, nombre: str, precio: float, stock: int, precio_kg: str) -> None:
    try:
        with get_db() as conn:
            conn.cursor().execute(
                "INSERT INTO productos VALUES (?, ?, ?, ?, ?)",
                (codigo, nombre, precio, stock, precio_kg),
            )
    except sqlite3.IntegrityError:
        raise ProductoExistente(f"Ya existe un producto con el código '{codigo}'.")


def buscar_producto(codigo: str) -> Producto | None:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nombre, precio, stock, PrecioKilo FROM productos WHERE codigo_barras = ?",
            (codigo,),
        )
        row = cursor.fetchone()

    if not row:
        return None
    nombre, precio, stock, precio_kg = row
    return Producto(
        codigo=codigo,
        nombre=nombre,
        precio=float(precio) if precio else 0.0,
        stock=int(stock) if stock is not None else 0,
        precio_kg=precio_kg if precio_kg is not None else "",
    )


def obtener_producto_por_codigo(codigo: str) -> tuple | None:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM productos WHERE codigo_barras = ?", (codigo,))
        return c.fetchone()


def eliminar_producto(codigo: str) -> None:
    with get_db() as conn:
        conn.cursor().execute("DELETE FROM productos WHERE codigo_barras = ?", (codigo,))


def obtener_promocion(codigo_producto: str) -> Promocion | None:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT tipo, cantidad_min, precio_promo, descuento
            FROM promociones
            WHERE codigo_producto = ?
              AND activa = 1
            LIMIT 1
        """, (codigo_producto,))
        row = c.fetchone()

    if not row:
        return None

    def to_float(value: object) -> float:
        try:
            return float(value)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            return 0.0

    return Promocion(
        tipo=row[0],
        cantidad_min=to_float(row[1]),
        precio_promo=to_float(row[2]),
        descuento=to_float(row[3]),
    )


def ajustar_stock(codigo: str, delta: int | str) -> None:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT stock FROM productos WHERE codigo_barras = ?", (codigo,))
        fila = cursor.fetchone()
        if not fila:
            raise ProductoNoEncontrado(f"No existe un producto con el código '{codigo}'.")
        stock_nuevo = calcular_stock(fila[0], delta)
        cursor.execute(
            "UPDATE productos SET stock = ? WHERE codigo_barras = ?",
            (stock_nuevo, codigo),
        )


def ajustar_precio(codigo: str, delta: int | str) -> None:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT precio FROM productos WHERE codigo_barras = ?", (codigo,))
        if not cursor.fetchone():
            raise ProductoNoEncontrado(f"No existe un producto con el código '{codigo}'.")
        precio_nuevo = calcular_precio_nuevo(delta)
        cursor.execute(
            "UPDATE productos SET precio = ? WHERE codigo_barras = ?",
            (precio_nuevo, codigo),
        )


def ajustar_precioKg(codigo: str, delta: int | str) -> None:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT PrecioKilo FROM productos WHERE codigo_barras = ?", (codigo,))
        if not cursor.fetchone():
            raise ProductoNoEncontrado(f"No existe un producto con el código '{codigo}'.")
        precio_kg_nuevo = calcular_precio_nuevo(delta)
        cursor.execute(
            "UPDATE productos SET PrecioKilo = ? WHERE codigo_barras = ?",
            (precio_kg_nuevo, codigo),
        )

def actualizar_precios_masivo(desc_pct: float, rec_pct: float) -> None:
    """Aplica un descuento y un recargo porcentual a TODOS los productos del sistema.
    
    Usa una única consulta SQL optimizada con redondeo a 2 decimales para evitar 
    errores de precisión de punto flotante en la base de datos.
    """
    # Calculamos el factor matemático neto: Ej: -10% y +20% -> 0.90 * 1.20 = 1.08
    factor = (1.0 - (desc_pct / 100.0)) * (1.0 + (rec_pct / 100.0))
    
    with get_db() as conn:
        cursor = conn.cursor()
        # El CASE asegura que si PrecioKilo está vacío o no es numérico, no se rompa la consulta
        cursor.execute(
            """
            UPDATE productos 
            SET 
                precio = ROUND(precio * ?, 2),
                PrecioKilo = CASE 
                    WHEN PrecioKilo IS NOT NULL AND PrecioKilo != '' AND PrecioKilo != '0'
                    THEN ROUND(CAST(PrecioKilo AS REAL) * ?, 2)
                    ELSE PrecioKilo 
                END
            """,
            (factor, factor),
        )