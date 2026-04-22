import os
import tempfile
from tkinter import messagebox
def imprimir_informe(tree, total_ventas):
    """
    Genera un archivo TXT con el informe completo (ventas + caja)
    y lo abre en el Bloc de Notas para impresión manual.
    """

    lineas = []
    lineas.append("=" * 61)
    lineas.append("                    INFORME DE MOVIMIENTOS")
    lineas.append("=" * 61)
    lineas.append("")
    lineas.append(
    f"{'Fecha y hora':<20} {'Tipo':<6} {'Usuario':<12} "
    f"{'Detalle':<22} {'Importe':>12}"
    )
    lineas.append("-" * 61)

    # Recorrer TreeView
    for item_id in tree.get_children():
        fecha, tipo, detalle, usuario, importe = tree.item(item_id)["values"]

        linea = (
            f"{fecha:<20} "
            f"{tipo:<6} "
            f"{str(usuario):<12} "
            f"{detalle:<22} "
            f"{float(importe):>12.2f}"
        )
        lineas.append(linea)

    lineas.append("-" * 61)
    lineas.append(f"TOTAL VENTAS: ${total_ventas:.2f}")
    lineas.append("=" * 61)
    lineas.append("\n")

    contenido = "\n".join(lineas)

    # Guardar TXT temporal
    txt_path = os.path.join(
        tempfile.gettempdir(),
        "informe_minimarket.txt"
    )

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(contenido)

    # Abrir en Bloc de Notas
    try:
        os.startfile(txt_path)
        messagebox.showinfo(
            "Informe abierto",
            "El informe se abrió en el Bloc de Notas.\n"
            "Use Archivo → Imprimir o Ctrl+P."
        )
    except Exception as e:
        messagebox.showerror(
            "Error",
            f"No se pudo abrir el informe:\n{e}"
        )