from __future__ import annotations
import sys
import os
import shutil
import sqlite3
from contextlib import contextmanager
from typing import Generator


def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


def conectar() -> sqlite3.Connection:
    app_folder_name = "SistemaMinimarketVE"
    db_name = "productos.db"

    app_data_dir = os.path.join(os.environ.get('APPDATA'), app_folder_name)
    persistent_db_path = os.path.join(app_data_dir, db_name)

    if not os.path.exists(persistent_db_path):
        os.makedirs(app_data_dir, exist_ok=True)
        source_db_path = resource_path(db_name)
        try:
            shutil.copyfile(source_db_path, persistent_db_path)
        except Exception:
            persistent_db_path = source_db_path

    conn = sqlite3.connect(persistent_db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager para conexiones SQLite.
    Hace commit al salir con éxito y rollback ante cualquier excepción.
    Siempre cierra la conexión al finalizar.
    """
    conn = conectar()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
