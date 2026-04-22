from __future__ import annotations
import hashlib
import os

_SCHEME = "pbkdf2"
_ALGO = "sha256"
_ITERATIONS = 260_000   # Django 4.x default; cumple OWASP 2023 para PBKDF2-SHA256
_SALT_BYTES = 32        # 256-bit salt aleatorio por contraseña


def hash_password(plain: str) -> str:
    """Devuelve un hash listo para almacenar.

    Formato: pbkdf2:sha256:<iterations>:<salt_hex>:<key_hex>
    El salt es aleatorio por cada llamada, garantizando hashes únicos
    incluso para contraseñas iguales.
    """
    salt = os.urandom(_SALT_BYTES)
    key = hashlib.pbkdf2_hmac(_ALGO, plain.encode("utf-8"), salt, _ITERATIONS)
    return f"{_SCHEME}:{_ALGO}:{_ITERATIONS}:{salt.hex()}:{key.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    """Verifica plain contra el hash almacenado.

    Acepta contraseñas en texto plano (legado) para la migración transparente.
    Siempre retorna False ante cualquier formato malformado.
    """
    if not stored.startswith(f"{_SCHEME}:"):
        return plain == stored  # compatibilidad con contraseñas legado

    try:
        _, algo, iters, salt_hex, key_hex = stored.split(":")
        key = hashlib.pbkdf2_hmac(
            algo,
            plain.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iters),
        )
        return key.hex() == key_hex
    except Exception:
        return False


def needs_upgrade(stored: str) -> bool:
    """True si la contraseña almacenada está en texto plano (necesita migración)."""
    return not stored.startswith(f"{_SCHEME}:")
