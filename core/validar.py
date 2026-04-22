from __future__ import annotations
import tkinter as tk


def aceptar(
    entry_kg: tk.Entry,
    kilos: tk.Toplevel,
    precio_kg: float,
    resultado: dict,
) -> None:
    """Lanza ValueError si el peso ingresado es inválido o no positivo."""
    try:
        peso = float(entry_kg.get())
    except ValueError:
        raise ValueError("El peso ingresado no es válido.")

    if peso <= 0:
        raise ValueError("El peso debe ser mayor a 0.")

    resultado["peso"] = peso
    resultado["subtotal"] = peso * precio_kg
    kilos.destroy()
