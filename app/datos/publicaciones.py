"""Publicar, cancelar, recibir hallazgos y consultar el catálogo."""
from datetime import datetime

from .cliente import rpc
from .errores import ReglaError


def puntos_activos(uid: str) -> list[dict]:
    return rpc(uid, "puntos_activos")


def publicar(uid: str, categoria, descripcion, lugar, fecha_txt, punto_id, foto_url="") -> None:
    """`fecha_txt` va en hora local ('AAAA-MM-DD HH:MM'); el resto de reglas las aplica la base."""
    try:
        fecha = datetime.strptime((fecha_txt or "").strip(), "%Y-%m-%d %H:%M").astimezone()
    except ValueError:
        raise ReglaError("La fecha debe tener el formato AAAA-MM-DD HH:MM.")
    rpc(uid, "publicar_objeto", p_categoria=categoria or None, p_descripcion=descripcion, p_lugar=lugar,
        p_fecha=fecha.isoformat(), p_punto=punto_id or None, p_foto=(foto_url or "").strip() or None)


def mis_publicaciones(uid: str) -> list[dict]:
    return rpc(uid, "mis_publicaciones")


def cancelar_publicacion(uid: str, oid: str) -> None:
    rpc(uid, "cancelar_publicacion", p_id=oid)


def pendientes(uid: str) -> list[dict]:
    return rpc(uid, "pendientes")


def confirmar_recepcion(uid: str, oid: str, detalle_oculto: str, notas: str = "") -> None:
    rpc(uid, "confirmar_recepcion", p_id=oid, p_detalle=detalle_oculto, p_notas=notas or None)


def rechazar_publicacion(uid: str, oid: str, motivo: str) -> None:
    rpc(uid, "rechazar_publicacion", p_id=oid, p_motivo=motivo)


def catalogo(uid: str, categoria=None, punto_id=None, texto="") -> list[dict]:
    """Solo objetos EN_CUSTODIA. La función de la base nunca toca el detalle oculto (CA-04)."""
    return rpc(uid, "catalogo", p_categoria=categoria or None, p_punto=punto_id or None, p_texto=texto or "")
