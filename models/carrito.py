from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


@dataclass
class CarritoItem:
    codigo: str
    nombre: str
    tipo: Literal["unidad", "peso"]
    precio_unitario: float
    cantidad: int = 0
    peso: float = 0.0
    subtotal: float = 0.0
    promo: str | None = None


Carrito = dict[str, CarritoItem]
