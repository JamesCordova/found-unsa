"""Publicar, cancelar y recibir hallazgos."""
from datetime import datetime
from .auditoria import auditar
from .conexion import ReglaError, a_texto, conectar, hora_actual
from .config import CATEGORIAS
from .permisos import exigir_staff
from .vencimientos import limpiar_estados


def puntos_activos() -> list[dict]:
    with conectar() as con:
        return [dict(r) for r in con.execute("SELECT * FROM puntos_entrega WHERE activo=1")]


def publicar(uid, categoria, descripcion, lugar, fecha_txt, punto_id, foto_url="") -> None:
    descripcion, lugar, foto_url = descripcion.strip(), lugar.strip(), (foto_url or "").strip()
    if categoria not in CATEGORIAS:
        raise ReglaError("Elige una categoría.")
    if not descripcion or len(descripcion) > 280:
        raise ReglaError("La descripción pública es obligatoria (máximo 280 caracteres).")
    if not lugar:
        raise ReglaError("Indica dónde lo encontraste.")
    if not punto_id:
        raise ReglaError("Elige el punto de entrega.")
    if categoria == "Documentos y tarjetas":
        foto_url = ""  # PU-03: en documentos no se muestra foto
    elif foto_url and (not foto_url.lower().startswith(("http://", "https://")) or len(foto_url) > 500):
        raise ReglaError("El enlace de la foto debe empezar con http:// o https:// (máximo 500 caracteres).")
    try:
        fecha = datetime.strptime(fecha_txt.strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        raise ReglaError("La fecha debe tener el formato AAAA-MM-DD HH:MM.")
    if fecha > hora_actual():
        raise ReglaError("La fecha del hallazgo no puede ser futura.")
    with conectar() as con:
        p = con.execute("SELECT bloqueado FROM perfiles WHERE id=?", (uid,)).fetchone()
        if p["bloqueado"]:
            raise ReglaError("Tu cuenta está bloqueada.")
        cur = con.execute(
            "INSERT INTO objetos(categoria,descripcion_publica,lugar_hallazgo,fecha_hallazgo,"
            "foto_url,publicado_por,punto_id,creado_en) VALUES (?,?,?,?,?,?,?,?)",
            (categoria, descripcion, lugar, a_texto(fecha), foto_url or None, uid, punto_id,
             a_texto(hora_actual())),
        )
        auditar(con, "publicacion_creada", uid, cur.lastrowid, despues="PENDIENTE_RECEPCION")


def mis_publicaciones(uid) -> list[dict]:
    with conectar() as con:
        limpiar_estados(con)
        return [dict(r) for r in con.execute(
            "SELECT o.*, p.nombre AS punto FROM objetos o JOIN puntos_entrega p ON p.id=o.punto_id "
            "WHERE publicado_por=? ORDER BY o.id DESC", (uid,))]


def cancelar_publicacion(uid, oid) -> None:
    with conectar() as con:
        o = con.execute("SELECT * FROM objetos WHERE id=? AND publicado_por=?", (oid, uid)).fetchone()
        if not o or o["estado"] != "PENDIENTE_RECEPCION":
            raise ReglaError("Solo puedes cancelar publicaciones pendientes de recepción.")
        con.execute("UPDATE objetos SET estado='RECHAZADO', motivo='cancelada por el hallador' WHERE id=?", (oid,))
        auditar(con, "publicacion_cancelada", uid, oid, "PENDIENTE_RECEPCION", "RECHAZADO")


def pendientes() -> list[dict]:
    with conectar() as con:
        limpiar_estados(con)
        return [dict(r) for r in con.execute(
            "SELECT o.*, p.nombre AS punto FROM objetos o JOIN puntos_entrega p ON p.id=o.punto_id "
            "WHERE estado='PENDIENTE_RECEPCION' ORDER BY o.id")]


def confirmar_recepcion(actor, oid, detalle_oculto, notas="") -> None:
    if not detalle_oculto.strip():
        raise ReglaError("Registra al menos un detalle oculto de verificación.")
    with conectar() as con:
        exigir_staff(con, actor)
        o = con.execute("SELECT estado FROM objetos WHERE id=?", (oid,)).fetchone()
        if not o or o["estado"] != "PENDIENTE_RECEPCION":
            raise ReglaError("La publicación ya no está pendiente de recepción.")
        con.execute(
            "UPDATE objetos SET estado='EN_CUSTODIA', recibido_por=?, recibido_en=? WHERE id=?",
            (actor, a_texto(hora_actual()), oid),
        )
        con.execute(
            "INSERT OR REPLACE INTO objetos_privado(objeto_id,detalle_oculto,notas_internas) VALUES (?,?,?)",
            (oid, detalle_oculto.strip(), notas.strip() or None),
        )
        auditar(con, "recepcion_confirmada", actor, oid, "PENDIENTE_RECEPCION", "EN_CUSTODIA")


def rechazar_publicacion(actor, oid, motivo) -> None:
    if not motivo.strip():
        raise ReglaError("El motivo es obligatorio.")
    with conectar() as con:
        exigir_staff(con, actor)
        o = con.execute("SELECT estado FROM objetos WHERE id=?", (oid,)).fetchone()
        if not o or o["estado"] != "PENDIENTE_RECEPCION":
            raise ReglaError("La publicación ya no está pendiente de recepción.")
        con.execute("UPDATE objetos SET estado='RECHAZADO', motivo=? WHERE id=?", (motivo.strip(), oid))
        auditar(con, "recepcion_rechazada", actor, oid, "PENDIENTE_RECEPCION", "RECHAZADO", motivo.strip())
