import os
import tempfile
from reports.ticket_generator import imprime_ticket

def generar_ticket(carrito, desc):
    contenido = imprime_ticket(carrito, desc)

    txt_path = os.path.join(tempfile.gettempdir(), "ticket_minimarket.txt")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(contenido)
        
    return txt_path