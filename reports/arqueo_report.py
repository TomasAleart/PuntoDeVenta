from tkinter import messagebox
import os
import tempfile

def imprimir_arqueos(tabla):
    filas = tabla.get_children()
    if not filas:
        messagebox.showwarning("Sin datos", "No hay arqueos para imprimir.")
        return

    contenido = ["====== INFORME DE ARQUEOS ======\n"]
    for fila in filas:
        contenido.append(" | ".join(map(str, tabla.item(fila)["values"])))
    contenido.append("\n================================")

    path = os.path.join(tempfile.gettempdir(), "arqueos_filtrados.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(contenido))

    try:
        os.startfile(path)
    except:
        pass
