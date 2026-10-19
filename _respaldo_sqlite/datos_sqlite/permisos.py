"""Verificación de rol en la capa de datos."""
from .conexion import ReglaError


def exigir_staff(con, actor_id):
    p = con.execute("SELECT rol, bloqueado FROM perfiles WHERE id=?", (actor_id,)).fetchone()
    if not p or p["rol"] not in ("funcionario", "admin") or p["bloqueado"]:
        raise ReglaError("Solo un funcionario o administrador puede hacer esto.")


def exigir_admin(con, actor_id):
    p = con.execute("SELECT rol FROM perfiles WHERE id=?", (actor_id,)).fetchone()
    if not p or p["rol"] != "admin":
        raise ReglaError("Solo un administrador puede hacer esto.")
