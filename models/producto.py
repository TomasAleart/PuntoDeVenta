from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Producto:
    codigo: str
    nombre: str
    precio: float
    stock: int
    precio_kg: str | float  # "" para productos por unidad, float para productos a granel

    @property
    def es_por_peso(self) -> bool:
        return bool(self.precio_kg)

    @property
    def precio_kg_float(self) -> float:
        """Precio por kg como float. Devuelve 0.0 si no es producto a granel."""
        return float(self.precio_kg) if self.precio_kg else 0.0
