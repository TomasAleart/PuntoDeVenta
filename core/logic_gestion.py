from __future__ import annotations


def calcular_stock(stock_actual: int, delta: int | str) -> int:
    """Calcula el nuevo stock aplicando un delta. Nunca devuelve valor negativo."""
    if delta == '':
        delta = 0
    return max(0, stock_actual + int(delta))


def calcular_precio_nuevo(delta: int | str) -> int:
    """Convierte un delta de precio a entero. Nunca devuelve valor negativo."""
    if delta == '':
        delta = 0
    return max(0, int(delta))
