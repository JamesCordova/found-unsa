"""Roles y bloqueos."""
from .auditoria import auditar
from .conexion import ReglaError, conectar
from .permisos import exigir_admin


def usuarios(actor) -> list[dict]:
    with conectar() as con:
        exigir_admin(con, actor)
        return [dict(r) for r in con.execute("SELECT id,email,nombre,rol,bloqueado FROM perfiles ORDER BY id")]


def cambiar_rol(actor, uid, rol) -> None:
    if rol not in ("usuario", "funcionario", "admin"):
        raise ReglaError("Rol inválido.")
    with conectar() as con:
        exigir_admin(con, actor)
        if uid == actor:
            raise ReglaError("No puedes cambiar tu propio rol.")
        antes = con.execute("SELECT rol FROM perfiles WHERE id=?", (uid,)).fetchone()["rol"]
        con.execute("UPDATE perfiles SET rol=? WHERE id=?", (rol, uid))
        auditar(con, "rol_cambiado", actor, None, None, antes, rol, f"usuario {uid}")


def bloquear(actor, uid, bloqueado: bool) -> None:
    with conectar() as con:
        exigir_admin(con, actor)
        if uid == actor:
            raise ReglaError("No puedes bloquearte a ti mismo.")
        con.execute("UPDATE perfiles SET bloqueado=? WHERE id=?", (int(bloqueado), uid))
        if bloqueado:  # los reclamos activos se cancelan
            for r in con.execute("SELECT id, objeto_id FROM reclamos WHERE reclamante_id=? AND estado='activo'",
                                 (uid,)).fetchall():
                con.execute("UPDATE reclamos SET estado='cancelado' WHERE id=?", (r["id"],))
                auditar(con, "reclamo_cancelado", actor, r["objeto_id"], r["id"], "activo", "cancelado", "usuario bloqueado")
        auditar(con, "usuario_bloqueado" if bloqueado else "usuario_desbloqueado", actor, detalle=f"usuario {uid}")
