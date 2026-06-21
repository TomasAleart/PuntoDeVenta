import os
import tempfile
from tkinter import messagebox
# Importamos las funciones necesarias de la base de datos
from database.informe_db import buscar_id_real, obtener_detalle

def imprimir_informe(tree, total_ventas):
    """
    Genera un archivo TXT con el informe completo (ventas con sus detalles + caja)
    y lo abre en el Bloc de Notas para impresión manual.
    """

    lineas = []
    lineas.append("=" * 70)
    lineas.append("                    INFORME DE MOVIMIENTOS CON DETALLE")
    lineas.append("=" * 70)
    lineas.append("")
    lineas.append(
        f"{'Fecha y hora':<20} {'Tipo':<6} {'Usuario':<12} "
        f"{'Detalle':<20} {'Importe':>10}"
    )
    lineas.append("-" * 70)

    # Recorrer TreeView
    for item_id in tree.get_children():
        fecha, tipo, detalle, usuario, importe = tree.item(item_id)["values"]

        linea = (
            f"{fecha:<20} "
            f"{tipo:<6} "
            f"{str(usuario):<12} "
            f"{detalle:<20} "
            f"{float(importe):>10.2f}"
        )
        lineas.append(linea)

        # 🎯 SI ES UNA VENTA, BUSCAMOS Y AGREGAMOS SUS ARTÍCULOS ABAJO
        if tipo == "VENTA":
            row_venta = buscar_id_real(fecha)
            if row_venta:
                id_venta, _ = row_venta
                detalles = obtener_detalle(id_venta)
                
                if detalles:
                    lineas.append("   └─ DETALLE DE LA VENTA:")
                    lineas.append(f"      {'Código':<14} {'Producto':<28} {'Cant.':<10} {'Subtotal':>10}")
                    lineas.append("      " + "." * 64)
                    
                    for codigo, nombre, cantidad, peso, precio_unit, subtotal, promo in detalles:
                        # Formatear cantidad según corresponda (KG o Unidades)
                        if peso and peso > 0:
                            cant_txt = f"{peso:.3f} kg"
                        else:
                            cant_txt = f"{int(cantidad)} un"
                            
                        lineas.append(
                            f"      {codigo:<14} "
                            f"{nombre[:26]:<28} " # Recortamos nombres extremadamente largos para no romper el TXT
                            f"{cant_txt:<10} "
                            f"${subtotal:>9.2f}"
                        )
                    lineas.append("   " + "─" * 65)

    lineas.append("-" * 70)
    lineas.append(f"TOTAL VENTAS: ${total_ventas:.2f}")
    lineas.append("=" * 70)
    lineas.append("\n")

    contenido = "\n".join(lineas)

    # Guardar TXT temporal
    txt_path = os.path.join(
        tempfile.gettempdir(),
        "informe_minimarket_detalle.txt"
    )

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(contenido)

    # Abrir en Bloc de Notas
    try:
        os.startfile(txt_path)
        messagebox.showinfo(
            "Informe abierto",
            "El informe con detalles se abrió en el Bloc de Notas.\n"
            "Use Archivo → Imprimir o Ctrl+P."
        )
    except Exception as e:
        messagebox.showerror(
            "Error",
            f"No se pudo abrir el informe:\n{e}"
        )