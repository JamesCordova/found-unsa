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


def puntos_todos(actor) -> list[dict]:
    """Todos los puntos de entrega (activos e inactivos) con cuántos objetos guardan."""
    with conectar() as con:
        exigir_admin(con, actor)
        return [dict(r) for r in con.execute(
            "SELECT p.*, (SELECT COUNT(*) FROM objetos o WHERE o.punto_id=p.id AND o.estado='EN_CUSTODIA') "
            "AS en_custodia FROM puntos_entrega p ORDER BY p.activo DESC, p.nombre")]


def guardar_punto(actor, nombre, ubicacion, horario, punto_id=None) -> None:
    """Crea un punto de entrega (punto_id=None) o edita uno existente (AD-02)."""
    nombre, ubicacion, horario = nombre.strip(), ubicacion.strip(), horario.strip()
    if not nombre or len(nombre) > 60:
        raise ReglaError("El nombre es obligatorio (máximo 60 caracteres).")
    if not ubicacion or not horario:
        raise ReglaError("Indica la ubicación y el horario de atención.")
    with conectar() as con:
        exigir_admin(con, actor)
        repetido = con.execute("SELECT id FROM puntos_entrega WHERE lower(nombre)=lower(?) AND id IS NOT ?",
                               (nombre, punto_id)).fetchone()
        if repetido:
            raise ReglaError("Ya existe un punto de entrega con ese nombre.")
        if punto_id is None:
            cur = con.execute("INSERT INTO puntos_entrega(nombre,ubicacion,horario) VALUES (?,?,?)",
                              (nombre, ubicacion, horario))
            auditar(con, "punto_creado", actor, detalle=f"punto {cur.lastrowid}: {nombre}")
        else:
            con.execute("UPDATE puntos_entrega SET nombre=?, ubicacion=?, horario=? WHERE id=?",
                        (nombre, ubicacion, horario, punto_id))
            auditar(con, "punto_editado", actor, detalle=f"punto {punto_id}: {nombre}")


def activar_punto(actor, punto_id, activo: bool) -> None:
    """Un punto inactivo deja de ofrecerse al publicar; sus objetos siguen en custodia."""
    with conectar() as con:
        exigir_admin(con, actor)
        if not activo and con.execute("SELECT COUNT(*) FROM puntos_entrega WHERE activo=1 AND id<>?",
                                      (punto_id,)).fetchone()[0] == 0:
            raise ReglaError("Debe quedar al menos un punto de entrega activo.")
        con.execute("UPDATE puntos_entrega SET activo=? WHERE id=?", (int(activo), punto_id))
        auditar(con, "punto_activado" if activo else "punto_desactivado", actor, detalle=f"punto {punto_id}")
