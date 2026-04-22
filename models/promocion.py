from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


@dataclass
class Promocion:
    tipo: Literal["cantidad", "peso", "porcentaje"]
    cantidad_min: float
    precio_promo: float
    descuento: float
