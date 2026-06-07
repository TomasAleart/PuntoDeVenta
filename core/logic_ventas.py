from __future__ import annotations
from database.productos_db import obtener_promocion
from models.carrito import CarritoItem, Carrito


def calcular_subtotal_item(item: CarritoItem) -> tuple[float, str | None]:
    """Calcula el subtotal de un ítem aplicando la promoción activa 
    y los modificadores individuales (descuento/recargo) en porcentaje.
    """
    promo = obtener_promocion(item.codigo)
    subtotal_base = 0.0
    promo_str = None

    # 1. Determinar el subtotal según promociones vigentes de la base de datos
    if not promo:
        if item.tipo == "unidad":
            subtotal_base = item.cantidad * item.precio_unitario
        else:
            subtotal_base = item.peso * item.precio_unitario

    elif promo.tipo == "cantidad" and item.tipo == "unidad":
        if item.cantidad < promo.cantidad_min:
            subtotal_base = item.cantidad * item.precio_unitario
        else:
            packs = int(item.cantidad // promo.cantidad_min)
            resto = item.cantidad % int(promo.cantidad_min)
            subtotal_base = (packs * promo.precio_promo) + (resto * item.precio_unitario)
            promo_str = f"{int(promo.cantidad_min)}x${promo.precio_promo}"

    elif promo.tipo == "peso" and item.tipo == "peso":
        if item.peso < promo.cantidad_min:
            subtotal_base = item.peso * item.precio_unitario
        else:
            subtotal_base = item.peso * promo.precio_promo
            promo_str = f"{promo.precio_promo}/kg PROMO"

    elif promo.tipo == "porcentaje":
        base = (item.cantidad * item.precio_unitario if item.tipo == "unidad"
                else item.peso * item.precio_unitario)
        descuento_promo = base * (promo.descuento / 100)
        subtotal_base = base - descuento_promo
        promo_str = f"{promo.descuento}% OFF"
    
    else:
        if item.tipo == "unidad":
            subtotal_base = item.cantidad * item.precio_unitario
        else:
            subtotal_base = item.peso * item.precio_unitario

    # 2. 🌟 LOGIC ENHANCEMENT: Aplicar Descuento y Recargo Individuales en PORCENTAJE
    desc_pct = getattr(item, "descuento", 0.0)
    rec_pct = getattr(item, "recargo", 0.0)

    # Calculamos el monto real en dinero a partir de los porcentajes ingresados
    monto_descuento = subtotal_base * (desc_pct / 100.0)
    monto_recargo = subtotal_base * (rec_pct / 100.0)

    # El subtotal final se ve afectado por ambos modificadores
    subtotal_final = subtotal_base - monto_descuento + monto_recargo

    return subtotal_final, promo_str


def calcular_total(carrito: Carrito, descuento_pct: float = 0.0) -> float:
    """Calcula el total del carrito aplicando un descuento porcentual global 
    sobre la suma de los subtotales ya modificados.
    """
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
