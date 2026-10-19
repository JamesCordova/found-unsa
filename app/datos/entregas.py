"""Validación de código, entrega presencial y bitácora (funcionario)."""
from .cliente import rpc


def buscar_codigo(uid: str, codigo: str) -> dict:
    """Mensaje distinto para código inexistente, usado, vencido o de objeto no custodiado."""
    return rpc(uid, "buscar_codigo", p_codigo=codigo or "")


def entregar(uid: str, rid: str, identidad_verificada: bool) -> None:
    rpc(uid, "entregar", p_reclamo=rid, p_identidad=bool(identidad_verificada))


def rechazar_reclamo(uid: str, rid: str, motivo: str) -> None:
    rpc(uid, "rechazar_reclamo", p_id=rid, p_motivo=motivo)


def bitacora(uid: str, accion: str = "") -> list[dict]:
    return rpc(uid, "bitacora", p_accion=accion or "")
