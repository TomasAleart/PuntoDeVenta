from __future__ import annotations
from database.login_db import validar_usuario


def validar_login(user: str, pwd: str) -> tuple | None:
    """Valida credenciales. Devuelve (id, usuario, contraseña, jerarquia) o None."""
    return validar_usuario(user.strip(), pwd.strip())
