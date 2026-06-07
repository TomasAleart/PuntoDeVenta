from __future__ import annotations
from datetime import datetime
from database.ventas_db import registrar_venta
from core.logic_ventas import calcular_subtotal_item, calcular_total
from models.carrito import CarritoItem, Carrito
from models.producto import Producto
from exceptions import StockInsuficiente, StockBajoWarning, VentaError, PagoInsuficiente


class VentaService:
    """Encapsula el estado del carrito y las operaciones de venta."""

    def __init__(self) -> None:
        self.carrito: Carrito = {}

    # ── Agregar ──────────────────────────────────────────────────────────────

    def agregar_unidad(self, producto: Producto) -> None:
        """Agrega o suma una unidad al carrito validando disponibilidad en memoria.

        El stock real se descuenta atómicamente junto con la venta al finalizar.
        Raises StockInsuficiente si no hay unidades disponibles (DB stock menos
        las ya reservadas en este carrito).
        Raises StockBajoWarning DESPUÉS de agregar cuando era la última unidad.
        """
        units_in_cart = (
            self.carrito[producto.codigo].cantidad
            if producto.codigo in self.carrito
            else 0
        )
        available = producto.stock - units_in_cart
        if available <= 0:
            raise StockInsuficiente(f"No queda stock de '{producto.nombre}'.")

        era_ultimo = available == 1

        codigo = producto.codigo
        if codigo in self.carrito:
            self.carrito[codigo].cantidad += 1
        else:
            self.carrito[codigo] = CarritoItem(
                codigo=codigo,
                nombre=producto.nombre,
                tipo="unidad",
                precio_unitario=producto.precio,
                cantidad=1,
            )

        item = self.carrito[codigo]
        item.subtotal, item.promo = calcular_subtotal_item(item)

        if era_ultimo:
            raise StockBajoWarning(f"Se agregó el último stock de '{producto.nombre}'.")

    def agregar_kg(self, producto: Producto, peso: float) -> str:
            """Agrega un ítem por peso. Devuelve la clave generada en el carrito.
            
            Raises StockInsuficiente si el peso solicitado supera el stock disponible
            restando lo que ya se acumuló en este carrito.
            """
            # 1. Sumamos el peso de todas las entradas de este mismo producto que ya estén en el carrito
            peso_en_carrito = sum(
                item.peso 
                for item in self.carrito.values() 
                if item.codigo == producto.codigo and item.tipo == "peso"
            )
            
            # 2. Calculamos el stock disponible restante
            available = producto.stock - peso_en_carrito
            
            # 3. Validamos si el nuevo peso que se quiere agregar supera lo disponible
            if peso > available:
                raise StockInsuficiente(
                    f"Stock insuficiente de '{producto.nombre}'. Disponible: {available:.3f} kg."
                )

            # 4. Si pasa la validación, se procesa el agregado de manera normal
            clave = f"{producto.codigo}_{datetime.now().timestamp()}"
            item = CarritoItem(
                codigo=producto.codigo,
                nombre=producto.nombre,
                tipo="peso",
                precio_unitario=producto.precio_kg_float,
                peso=peso,
            )
            item.subtotal, item.promo = calcular_subtotal_item(item)
            self.carrito[clave] = item
            return clave
    # ── Eliminar ─────────────────────────────────────────────────────────────

    def eliminar_uno(self, clave: str) -> None:
        """Elimina 1 unidad del ítem (o el ítem entero si es el último)."""
        item = self.carrito.get(clave)
        if not item:
            raise VentaError("Ítem no encontrado en el carrito.")

        if item.tipo == "unidad":
            item.cantidad -= 1
            item.subtotal, item.promo = calcular_subtotal_item(item)
            if item.cantidad <= 0:
                del self.carrito[clave]
        else:
            del self.carrito[clave]

    def eliminar_completo(self, clave: str) -> None:
        """Elimina el ítem completo del carrito."""
        if clave not in self.carrito:
            raise VentaError("Ítem no encontrado en el carrito.")
        del self.carrito[clave]

    # ── Totales ───────────────────────────────────────────────────────────────

    def total(self, descuento_pct: float = 0.0) -> float:
        """Calcula el total con descuento aplicado."""
        return calcular_total(self.carrito, descuento_pct)

    def calcular_vuelto(self, pago_str: str, descuento_pct: float = 0.0) -> float:
        """Calcula el vuelto.
        Raises ValueError si pago_str no es numérico.
        Raises PagoInsuficiente si el pago no cubre el total.
        """
        try:
            pago = float(pago_str)
        except ValueError:
            raise ValueError("El monto de pago ingresado no es válido.")

        total = self.total(descuento_pct)
        if pago < total:
            raise PagoInsuficiente(
                f"El pago (${pago:.2f}) no cubre el total (${total:.2f})."
            )
        return pago - total

    # ── Finalizar / Limpiar ───────────────────────────────────────────────────

    def finalizar(self, usuario: str, descuento_pct: float = 0.0) -> None:
        """Registra la venta en la base de datos.
        Raises VentaError si el carrito está vacío.
        """
        if not self.carrito:
            raise VentaError("No hay productos en el carrito.")
        registrar_venta(usuario, self.carrito, descuento_pct)

    def limpiar(self) -> None:
        """Vacía el carrito."""
        self.carrito.clear()

    # ── Métodos a agregar en tu clase VentaService ───────────────────────────

    def obtener_item(self, clave: str) -> CarritoItem:
        """Devuelve un ítem del carrito por su clave única."""
        if clave not in self.carrito:
            raise VentaError("El producto no se encuentra en el carrito actual.")
        return self.carrito[clave]

    def modificar_item(self, clave: str, nueva_cantidad: float, descuento: float, recargo: float) -> CarritoItem:
        if clave not in self.carrito:
            raise VentaError("El producto no se encuentra en el carrito.")

        item = self.carrito[clave]

        if item.tipo == "unidad":
            item.cantidad = int(nueva_cantidad)
        elif item.tipo == "peso":
            item.peso = nueva_cantidad

        # Guardamos los modificadores en el objeto
        item.descuento = descuento
        item.recargo = recargo

        # Al llamar a tu función del core, ya procesa promos + tus nuevos modificadores de una sola vez
        item.subtotal, item.promo = calcular_subtotal_item(item)

        return item
