from __future__ import annotations
import sqlite3
from database.connection import get_db
from core.security import hash_password, verify_password, needs_upgrade
from exceptions import UsuarioExistente


def validar_usuario(user: str, pwd: str) -> tuple | None:
    """Valida credenciales. Migra automáticamente contraseñas en texto plano al primer login.

    Devuelve (id, usuario, contrasena, jerarquia) o None si las credenciales son inválidas.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        # Realizamos la búsqueda de usuario de forma insensible a mayúsculas/minúsculas.
        cursor.execute(
            "SELECT id, usuario, contrasena, jerarquia FROM usuarios WHERE LOWER(usuario) = LOWER(?)",
            (user,),
        )
        fila = cursor.fetchone()
        if not fila:
            return None

        _id, usuario_col, contrasena, jerarquia = fila

        # Asegurarse de que el hash de la contraseña recuperado no tenga espacios en blanco
        contrasena = contrasena.strip()

        if not verify_password(pwd, contrasena):
            return None

        # Migración transparente: hashear contraseña legado en texto plano
        if needs_upgrade(contrasena):
            nuevo_hash = hash_password(pwd)
            cursor.execute(
                "UPDATE usuarios SET contrasena = ? WHERE usuario = ?",
                (nuevo_hash, usuario_col),
            )

        return fila


def obtener_usuario(nombre: str) -> tuple | None:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE usuario = ?", (nombre,))
        return c.fetchone()


def eliminar_usuario_por_nombre(nombre: str) -> None:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM usuarios WHERE usuario = ?", (nombre,))


def agregar_usuario(nombre: str, contrasena: str, jerarquia: str) -> None:
    """Agrega un nuevo usuario con la contraseña hasheada.
    Raises UsuarioExistente si el nombre ya está registrado.
    """
    try:
        with get_db() as conn:
            conn.cursor().execute(
                "INSERT INTO usuarios (usuario, contrasena, jerarquia) VALUES (?, ?, ?)",
                (nombre, hash_password(contrasena), jerarquia),
            )
    except sqlite3.IntegrityError:
        raise UsuarioExistente(f"Ya existe un usuario con el nombre '{nombre}'.")
