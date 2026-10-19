"""Roles, bloqueos y puntos de entrega (administrador)."""
from .cliente import rpc


def usuarios(uid: str) -> list[dict]:
    return rpc(uid, "usuarios")


def cambiar_rol(uid: str, objetivo: str, rol: str) -> None:
    rpc(uid, "cambiar_rol", p_usuario=objetivo, p_rol=rol)


def bloquear(uid: str, objetivo: str, bloqueado: bool) -> None:
    rpc(uid, "bloquear", p_usuario=objetivo, p_bloqueado=bool(bloqueado))


def puntos_todos(uid: str) -> list[dict]:
    """Todos los puntos (activos e inactivos) con cuántos objetos guardan."""
    return rpc(uid, "puntos_todos")


def guardar_punto(uid: str, nombre, ubicacion, horario, punto_id=None) -> None:
    """Crea un punto de entrega (punto_id=None) o edita uno existente (AD-02)."""
    rpc(uid, "guardar_punto", p_nombre=nombre, p_ubicacion=ubicacion, p_horario=horario, p_id=punto_id)


def activar_punto(uid: str, punto_id: str, activo: bool) -> None:
    rpc(uid, "activar_punto", p_id=punto_id, p_activo=bool(activo))
