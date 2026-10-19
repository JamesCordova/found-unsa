"""Registro e inicio de sesión."""
import sqlite3
from .conexion import ReglaError, a_texto, conectar, hash_clave, hora_actual
from .config import DOMINIO


def registrar(nombre: str, email: str, clave: str) -> None:
    email = email.strip().lower()
    if not email.endswith(DOMINIO):
        raise ReglaError(f"Solo se aceptan correos institucionales ({DOMINIO}).")
    if not nombre.strip() or len(nombre) > 60:
        raise ReglaError("El nombre es obligatorio (máximo 60 caracteres).")
    if len(clave) < 4:
        raise ReglaError("La contraseña debe tener al menos 4 caracteres.")
    try:
        with conectar() as con:
            con.execute(
                "INSERT INTO perfiles(email,nombre,clave,creado_en) VALUES (?,?,?,?)",
                (email, nombre.strip(), hash_clave(clave), a_texto(hora_actual())),
            )
    except sqlite3.IntegrityError:
        raise ReglaError("Ya existe una cuenta con ese correo.")


def iniciar_sesion(email: str, clave: str) -> dict:
    email = email.strip().lower()
    if not email.endswith(DOMINIO):
        raise ReglaError(f"Solo se aceptan correos institucionales ({DOMINIO}).")
    with conectar() as con:
        p = con.execute("SELECT * FROM perfiles WHERE email=?", (email,)).fetchone()
    if not p or p["clave"] != hash_clave(clave):
        raise ReglaError("Correo o contraseña incorrectos.")
    return dict(p)


def perfil(uid: int) -> dict:
    with conectar() as con:
        return dict(con.execute("SELECT * FROM perfiles WHERE id=?", (uid,)).fetchone())
