# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Desktop POS (Point-of-Sale) system for a small retail store (minimarket), built with Python + Tkinter + SQLite3. The app runs on Windows and can be bundled into a standalone executable via PyInstaller.

## Running the Application

```bash
python main.py
```

**Dependencies:** Standard library + Pillow. Install with:
```bash
pip install pillow
```

> Note: `requirements.txt` is empty — Pillow is the only third-party dependency.

## Architecture

Three-layer architecture:

```
gui/          ← Tkinter UI windows (no business logic)
core/         ← Business logic, calculations, validations
database/     ← SQLite3 queries (one file per domain)
reports/      ← Report/receipt formatting and printing
```

Entry point: `main.py` → `gui/login_window.py` → `gui/main_window.py`

## Database

SQLite3 database stored at `%APPDATA%\SistemaMinimarketVE\productos.db` (not in the project directory). `database/connection.py` handles path resolution and first-run initialization, including PyInstaller bundle path detection via `sys._MEIPASS`.

Every connection executes `PRAGMA foreign_keys = ON` before being used, enforcing referential integrity between `ventas` and `ventas_detalle`.

Key tables: `productos`, `usuarios`, `ventas`, `ventas_detalle`, `promociones`, `caja`, `arqueos`.

## Domain Concepts

**Product types:** Products are either unit-based (integer quantity) or weight-based (decimal kg). Weight products use `PrecioKilo` for pricing; bulk entry goes through `gui/kg_window.py`.

**Cart structure:** Cart is a dict keyed by product code for unit items, or `"{code}_{timestamp}"` for weight items:
```python
{
  "codigo": ..., "nombre": ..., "tipo": "unidad"|"peso",
  "cantidad": int, "peso": float,
  "precio_unitario": float, "subtotal": float, "promo": str | None
}
```

**Promotions:** Three types (`cantidad`, `peso`, `porcentaje`) defined in the `promociones` table. Applied automatically in `core/logic_ventas.py` via `obtener_promocion()` at add-to-cart time.

**Stock:** The cart operates purely in-memory during the session. Stock is validated against DB value minus units already in the current cart (in `VentaService.agregar_unidad`). Actual stock decrement happens atomically inside `registrar_venta()` together with the sale INSERT — both operations share a single SQLite transaction and roll back together on failure. Weight-based items bypass stock count entirely.

**Roles:** `jerarquia` field on `usuarios` controls access. Value `"admin"` unlocks stock editing, user management, and transaction deletion. The role is passed through window constructors as the `jerarquia` parameter.

## Key Files

| File | Purpose |
|------|---------|
| `core/venta_service.py` | Cart state and sale operations (in-memory, no DB side effects) |
| `core/logic_ventas.py` | Subtotal, total, and promotion calculation |
| `database/ventas_db.py` | Atomic sale registration: stock decrement + INSERT ventas + INSERT ventas_detalle |
| `database/productos_db.py` | Product CRUD + promotion lookup + admin stock/price adjustments |
| `database/connection.py` | DB path resolution, `get_db()` context manager, FK pragma |

## Stub Files

`config.py`, `core/utils.py`, `gui/widgets.py`, and `gui/stock_window.py` are empty placeholders.

`core/logic_compra.py`, `core/main_logic.py`, and `database/stock_db.py` are empty modules kept for import-path stability; their logic was consolidated into `core/venta_service.py` and `database/ventas_db.py`.

## Security Note

Passwords are stored as plain text in the `usuarios` table. Any authentication changes should address this.

---

## Development History

### Fase 1 — Modelos y excepciones
Introduced typed domain models (`models/producto.py`, `models/carrito.py`, `models/promocion.py`) and a centralized exception hierarchy (`exceptions.py`) replacing ad-hoc string errors throughout the codebase.

### Fase 2 — Capa de base de datos
Refactored all raw SQLite calls into dedicated per-domain modules under `database/`. Added `database/connection.py` with a `get_db()` context manager that auto-commits on success and rolls back on exception, and activates `PRAGMA foreign_keys = ON` on every connection.

### Fase 3 — Lógica de negocio
Extracted business logic from GUI files into `core/`. Created `core/venta_service.py` (`VentaService` class) as the single owner of cart state. Moved promotion calculations to `core/logic_ventas.py`.

### Fase 4 — Capa de presentación (GUI)
Cleaned up all Tkinter windows to delegate to `VentaService` and `core/` functions. Windows contain no business logic or direct DB access.

### Fase 5 — Atomicidad transaccional y Foreign Keys
**Problem:** stock was decremented in separate per-item DB transactions at add-to-cart time; if `registrar_venta` failed, the DB would have decremented stock with no corresponding sale record.

**Fix:** the cart is now purely in-memory during the session. `registrar_venta()` opens a single connection and, within one transaction: validates + decrements stock for all unit items (`UPDATE ... AND stock >= ?`), then inserts `ventas` + all `ventas_detalle` rows. Any failure triggers a full rollback. Weight items continue to bypass stock tracking. Foreign Keys confirmed active via `PRAGMA foreign_keys = ON` in `connection.py`.

### Fase 6 — Limpieza de código muerto y documentación
Removed all dead functions from `database/stock_db.py` (functions became unreachable after Fase 5 restructure). Removed dead comment-only content from `core/logic_compra.py` and `core/main_logic.py`. Removed unused `codigo` parameter from `core/validar.aceptar()`. Generated `README.md` for portfolio.
