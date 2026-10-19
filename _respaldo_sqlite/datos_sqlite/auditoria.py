"""Bitácora inmutable de cambios de estado."""
from .conexion import a_texto, conectar, hora_actual
from .permisos import exigir_staff


def auditar(con, accion, actor_id, objeto_id=None, reclamo_id=None, antes=None, despues=None, detalle=None):
    con.execute(
        "INSERT INTO auditoria(objeto_id,reclamo_id,accion,estado_anterior,estado_nuevo,actor_id,detalle,creado_en)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (objeto_id, reclamo_id, accion, antes, despues, actor_id, detalle, a_texto(hora_actual())),
    )


def bitacora(actor, accion="") -> list[dict]:
    with conectar() as con:
        exigir_staff(con, actor)
        sql = ("SELECT a.*, u.nombre AS actor FROM auditoria a LEFT JOIN perfiles u ON u.id=a.actor_id")
        args: list = []
        if accion:
            sql += " WHERE a.accion LIKE ?"
            args.append(f"%{accion}%")
        return [dict(r) for r in con.execute(sql + " ORDER BY a.id DESC LIMIT 100", args)]
