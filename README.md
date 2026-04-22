# Sistema Minimarket V&E

> Sistema de punto de venta (POS) de escritorio para un pequeño comercio minorista. Desarrollado íntegramente en Python con interfaz gráfica nativa, base de datos local y soporte para empaquetado como ejecutable standalone.

---

## Características

- **Venta por unidad y por peso** — soporte para productos sueltos y a granel (kg)
- **Carrito en tiempo real** — agregar, eliminar uno a uno o eliminar ítem completo
- **Descuentos por venta** — porcentaje aplicable sobre el total antes de cobrar
- **Promociones automáticas** — por cantidad, por peso o por porcentaje, evaluadas al agregar al carrito
- **Control de stock atómico** — el descuento de stock y el registro de la venta ocurren en una única transacción SQLite; si algo falla, ambas operaciones se revierten juntas
- **Caja e historial** — apertura de caja, arqueos y saldo acumulado por sesión
- **Gestión de productos** — alta, baja y modificación de stock, precios y precio por kilo
- **Gestión de usuarios** — usuarios con roles `admin` / `cajero`; el rol admin habilita edición de stock, gestión de usuarios y eliminación de ventas
- **Informes de ventas** — filtrado por rango de fechas con detalle por ítem
- **Ticket de caja** — impresión del recibo con desglose de promo y vuelto
- **Empaquetable como `.exe`** — compatible con PyInstaller para distribución sin intérprete Python

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.10+ |
| Interfaz gráfica | Tkinter (stdlib) |
| Base de datos | SQLite3 (stdlib) |
| Imágenes | Pillow |
| Empaquetado | PyInstaller |

Sin dependencias externas pesadas. Un solo `pip install pillow` es suficiente para correr en desarrollo.

---

## Arquitectura

```
SistemaMinimarket/
├── main.py                  # Entry point
├── gui/                     # Ventanas Tkinter (sin lógica de negocio)
│   ├── login_window.py
│   ├── main_window.py       # Ventana principal de venta
│   ├── gestion_window.py    # ABM de productos y usuarios
│   ├── kg_window.py         # Modal de ingreso de peso
│   ├── promos_window.py     # Gestión de promociones
│   ├── caja_window.py       # Apertura y actualización de caja
│   ├── arqueo_window.py     # Arqueo de caja
│   ├── informe_window.py    # Informes de ventas
│   └── ticket_window.py     # Impresión de ticket
├── core/                    # Lógica de negocio
│   ├── venta_service.py     # Estado del carrito y operaciones de venta
│   ├── logic_ventas.py      # Cálculo de subtotales, totales y promociones
│   ├── logic_login.py       # Autenticación
│   ├── logic_gestion.py     # Cálculos de stock y precios
│   ├── logic_arqueos.py     # Lógica de arqueo
│   ├── logic_informe.py     # Filtrado de informes
│   ├── logic_ticket.py      # Formato del ticket
│   └── validar.py           # Validación de ingreso de peso (KgWindow)
├── database/                # Capa de acceso a datos (SQLite3)
│   ├── connection.py        # Pool de conexiones + PRAGMA foreign_keys + context manager
│   ├── productos_db.py      # CRUD de productos y promociones
│   ├── ventas_db.py         # Registro atómico de ventas + descuento de stock
│   ├── ventas_db.py
│   ├── caja_db.py
│   ├── arqueo_db.py
│   ├── informe_db.py
│   ├── promos_db.py
│   └── login_db.py
├── models/                  # Dataclasses de dominio
│   ├── producto.py
│   ├── carrito.py
│   └── promocion.py
├── reports/                 # Formato e impresión de reportes
├── exceptions.py            # Jerarquía de excepciones de dominio
└── LOGO.jpg
```

### Decisiones de diseño relevantes

**Transacción atómica en la venta:** el carrito opera puramente en memoria durante la sesión. Al ejecutar "Nueva compra", `registrar_venta()` abre una única conexión SQLite, decrementa el stock de todos los ítems por unidad y registra cabecera + detalle de venta. Si cualquier operación falla, SQLite hace rollback automático y el estado de la base de datos no cambia.

**Foreign Keys activas:** cada conexión ejecuta `PRAGMA foreign_keys = ON` antes de ser entregada, garantizando integridad referencial entre `ventas` y `ventas_detalle`.

**Separación GUI / lógica / datos:** las ventanas Tkinter no acceden directamente a la base de datos; invocan métodos de `VentaService` o funciones de `core/`. Las funciones de `database/` solo ejecutan SQL y devuelven resultados; no toman decisiones de negocio.

---

## Instalación y uso

### Requisitos

- Python 3.10 o superior
- Windows (la app está optimizada para escritorio Windows)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/SistemaMinimarket.git
cd SistemaMinimarket

# 2. Instalar dependencia
pip install pillow

# 3. Ejecutar
python main.py
```

La base de datos se crea automáticamente en `%APPDATA%\SistemaMinimarketVE\productos.db` en el primer arranque.

### Credenciales por defecto

| Usuario | Contraseña | Rol |
|---|---|---|
| admin | admin | admin |

> Se recomienda cambiar la contraseña por defecto desde la ventana de Gestión.

### Empaquetado como ejecutable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "productos.db;." --add-data "LOGO.jpg;." main.py
```

El ejecutable generado en `dist/` corre sin necesitar Python instalado.

---

## Base de datos

La base se almacena fuera del directorio del proyecto para sobrevivir reinstalaciones del ejecutable.

**Tablas principales:**

| Tabla | Descripción |
|---|---|
| `productos` | Catálogo con código de barras, precio, stock y precio por kg |
| `usuarios` | Credenciales y rol (`jerarquia`) |
| `ventas` | Cabecera de cada venta (fecha, total, vendedor, caja) |
| `ventas_detalle` | Líneas de venta con FK a `ventas` |
| `promociones` | Reglas de promoción activas por producto |
| `caja` | Historial de aperturas de caja |
| `arqueos` | Registro de arqueos por turno |

---

## Autor

**Tomás** — [tomasaleart@gmail.com](mailto:tomasaleart@gmail.com)

Proyecto de portfolio — sistema POS funcional desarrollado de cero, con foco en correctitud transaccional, separación de capas y empaquetado para producción.
