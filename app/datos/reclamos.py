"""Reclamos con código de un solo uso."""
from .cliente import rpc


def crear_reclamo(uid: str, oid: str, descripcion: str) -> dict:
    return rpc(uid, "crear_reclamo", p_objeto=oid, p_descripcion=descripcion)


def mis_reclamos(uid: str) -> list[dict]:
    return rpc(uid, "mis_reclamos")


def cancelar_reclamo(uid: str, rid: str) -> None:
    rpc(uid, "cancelar_reclamo", p_id=rid)
