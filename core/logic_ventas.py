from __future__ import annotations
from database.productos_db import obtener_promocion
from models.carrito import CarritoItem, Carrito


def calcular_subtotal_item(item: CarritoItem) -> tuple[float, str | None]:
    """Calcula el subtotal de un ítem aplicando la promoción activa si corresponde."""
    promo = obtener_promocion(item.codigo)

    if not promo:
        if item.tipo == "unidad":
            return item.cantidad * item.precio_unitario, None
        return item.peso * item.precio_unitario, None

    if promo.tipo == "cantidad" and item.tipo == "unidad":
        if item.cantidad < promo.cantidad_min:
            return item.cantidad * item.precio_unitario, None
        packs = int(item.cantidad // promo.cantidad_min)
        resto = item.cantidad % int(promo.cantidad_min)
        subtotal = packs * promo.precio_promo + resto * item.precio_unitario
        return subtotal, f"{int(promo.cantidad_min)}x${promo.precio_promo}"

    if promo.tipo == "peso" and item.tipo == "peso":
        if item.peso < promo.cantidad_min:
            return item.peso * item.precio_unitario, None
        return item.peso * promo.precio_promo, f"{promo.precio_promo}/kg PROMO"

    if promo.tipo == "porcentaje":
        base = (item.cantidad * item.precio_unitario if item.tipo == "unidad"
                else item.peso * item.precio_unitario)
        descuento = base * (promo.descuento / 100)
        return base - descuento, f"{promo.descuento}% OFF"

    if item.tipo == "unidad":
        return item.cantidad * item.precio_unitario, None
    return item.peso * item.precio_unitario, None


def calcular_total(carrito: Carrito, descuento_pct: float = 0.0) -> float:
    """Calcula el total del carrito aplicando un descuento porcentual."""
    subtotal = sum(item.subtotal for item in carrito.values())
    descuento_pct = max(0.0, min(descuento_pct, 100.0))
    return subtotal * (1 - descuento_pct / 100)


def calcular_caja_actual(venta: tuple | None, caja: tuple | None) -> float:
    if venta and caja:
        return float(venta[1]) if venta[0] > caja[0] else float(caja[1])
    if venta:
        return float(venta[1])
    if caja:
        return float(caja[1])
    return 0.0
