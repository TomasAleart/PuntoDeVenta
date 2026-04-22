from __future__ import annotations
from datetime import datetime
from models.carrito import Carrito


def imprime_ticket(carrito: Carrito, desc: float) -> str:
    ahora = datetime.now()
    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M")

    lineas = [
        "-----------------------------------------------",
        "             MINIMARKET V&E",
        "-----------------------------------------------",
        "               Ticket de Venta",
        f"Fecha: {fecha}  Hora: {hora}",
        "-----------------------------------------------",
        "Cant/Peso  Descripción            Precio     Subtotal",
        "-----------------------------------------------",
    ]

    for item in carrito.values():
        nombre = item.nombre[:22]

        if item.tipo == "unidad":
            cant_txt = str(item.cantidad)
            precio_txt = f"${item.precio_unitario:.2f}"
        else:
            cant_txt = f"{item.peso:.3f}kg"
            precio_txt = f"${item.precio_unitario:.2f}/kg"

        lineas.append(
            f"{cant_txt:<10}{nombre:<22}{precio_txt:>10}{item.subtotal:>11.2f}"
        )
        if item.promo:
            lineas.append(f"   PROMO: {item.promo}")

    lineas.append("-----------------------------------------------")

    subtotal_total = sum(item.subtotal for item in carrito.values())
    descuento = subtotal_total * (desc / 100)
    total_final = subtotal_total - descuento

    lineas.extend([
        f"Subtotal:{subtotal_total:>37.2f}",
        f"Descuento:{descuento:>36.2f}",
        f"TOTAL:{total_final:>40.2f}",
        "-----------------------------------------------",
        "DOCUMENTO NO VALIDO COMO FACTURA",
        "\n\n\n",
    ])

    return "\r\n".join(lineas)
