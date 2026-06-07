from __future__ import annotations
from datetime import datetime
from models.carrito import Carrito
from core.logic_ventas import calcular_total  # 🏢 Importamos la lógica centralizada


def imprime_ticket(carrito: Carrito, desc_global_pct: float) -> str:
    ahora = datetime.now()
    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M")

    lineas = [
        "-----------------------------------------------",
        "              MINIMARKET V&E",
        "-----------------------------------------------",
        "               Ticket de Venta",
        f"Fecha: {fecha}  Hora: {hora}",
        "-----------------------------------------------",
        "Cant/Peso  Descripción            Precio     Subtotal",
        "-----------------------------------------------",
    ]

    for item in carrito.values():
        # Limitamos el nombre a 22 caracteres para que no desplace las columnas derechas
        nombre = item.nombre[:22]

        if item.tipo == "unidad":
            cant_txt = str(item.cantidad)
            precio_txt = f"${item.precio_unitario:.2f}"
        else:
            cant_txt = f"{item.peso:.3f}kg"
            precio_txt = f"${item.precio_unitario:.2f}/kg"

        # Fila principal del producto
        lineas.append(
            f"{cant_txt:<10}{nombre:<22}{precio_txt:>10}{item.subtotal:>11.2f}"
        )
        
        # ── SUB-LÍNEAS DE MODIFICADORES ──────────────────────────────────────
        # Si tiene promo activa, la listamos abajo
        if item.promo:
            lineas.append(f"   PROMO: {item.promo}")

        # Si se aplicó un descuento manual desde la interfaz
        if getattr(item, "descuento", 0.0) > 0:
            lineas.append(f"   Desc. Individual: -${item.descuento:.2f}")

        # Si se aplicó un recargo manual desde la interfaz
        if getattr(item, "recargo", 0.0) > 0:
            lineas.append(f"   Recargo Individual: +${item.recargo:.2f}")
        # ─────────────────────────────────────────────────────────────────────

    lineas.append("-----------------------------------------------")

    # 🏢 CÁLCULOS CENTRALIZADOS
    # Sumamos los subtotales de los ítems (que ya contemplan sus propios desc/recargos)
    subtotal_acumulado = sum(item.subtotal for item in carrito.values())
    
    # Delegamos el cálculo final al core de tu lógica
    total_final = calcular_total(carrito, desc_global_pct)
    
    # El descuento global en pesos es la diferencia entre el acumulado y el neto final
    descuento_global_pesos = subtotal_acumulado - total_final

    # Bloque de cierre del ticket
    lineas.extend([
        f"Subtotal:{subtotal_acumulado:>37.2f}",
        f"Descuento Global ({desc_global_pct}%):{descuento_global_pesos:>21.2f}",
        f"TOTAL:{total_final:>40.2f}",
        "-----------------------------------------------",
        "DOCUMENTO NO VALIDO COMO FACTURA",
        "\n\n\n",
    ])

    return "\r\n".join(lineas)