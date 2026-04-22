from database.informe_db import obtener_caja_inicial

def primer_caja(eventos):
    eventos.sort(key=lambda x: x[0])
    primer_evento = eventos[0]

    if primer_evento[1] == "CAJA":
        caja_inicial_mostrada = float(primer_evento[4])
    else:
         caja_inicial_mostrada = obtener_caja_inicial(primer_evento[0])
    return caja_inicial_mostrada

def sumar(eventos, fecha_base, caja_base, tree):
    total_ventas_periodo = 0.0
    total_ventas_computadas = 0.0
    total_movimientos = 0.0

    for fecha, tipo, detalle, usuario, importe in eventos:
        importe = float(importe)

        tree.insert(
            "",
            "end",
            values=(fecha, tipo, detalle, usuario, f"{importe:.2f}")
        )

        if tipo == "VENTA":
            total_ventas_periodo += importe

            if fecha_base is None or fecha >= fecha_base:
                total_ventas_computadas += importe

        elif tipo == "CAJA" and detalle != "Caja inicial del sistema":
            total_movimientos += importe

    caja_final = caja_base + total_ventas_computadas + total_movimientos
    return total_ventas_periodo, caja_final


