"""Conexión a SQLite y utilidades comunes."""
from datetime import datetime
import hashlib
import sqlite3
from contextlib import contextmanager
from .config import DB_PATH


class ReglaError(Exception):
    """Operación rechazada por una regla de negocio; el mensaje va al usuario."""


def hora_actual() -> datetime:
    return datetime.now().replace(microsecond=0)


def a_texto(dt: datetime) -> str:
    return dt.isoformat(sep=" ")


def hash_clave(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


@contextmanager
def conectar():
    """Abre la base, confirma al salir (o revierte si hubo error) y siempre cierra."""
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        with con:
            from .esquema import asegurar_esquema  # import tardío: esquema usa conectar
            asegurar_esquema(con)
            yield con
    finally:
        con.close()
