import os
from tkinter import messagebox
from core.logic_ticket import generar_ticket
def imprimir_ticket(carrito, entrada_descuento):
    try:
        desc = float(entrada_descuento.get())
    except ValueError:
        desc = 0.0
    desc = max(0, min(desc, 100))
    
    path = generar_ticket(carrito, desc)

    try:
        os.startfile(path)
        messagebox.showinfo(
            "Ticket abierto",
            "El ticket se abrió en el Bloc de Notas.\nUse Archivo → Imprimir o Ctrl + P."
        )
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el ticket:\n{e}")