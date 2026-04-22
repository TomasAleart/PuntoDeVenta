from __future__ import annotations


class MinimarketError(Exception):
    """Excepción base del sistema. Todas las excepciones de dominio la heredan."""


class ProductoNoEncontrado(MinimarketError):
    """El código de barras no corresponde a ningún producto."""


class StockInsuficiente(MinimarketError):
    """El producto no tiene stock disponible."""


class StockBajoWarning(MinimarketError):
    """El producto fue agregado al carrito pero era el último en stock.
    El procesamiento ya se completó; el receptor solo debe mostrar una advertencia.
    """


class ProductoExistente(MinimarketError):
    """Ya existe un producto con ese código de barras."""


class UsuarioExistente(MinimarketError):
    """Ya existe un usuario con ese nombre."""


class VentaError(MinimarketError):
    """Error al procesar una operación de venta."""


class PagoInsuficiente(VentaError):
    """El monto de pago no cubre el total de la venta."""
