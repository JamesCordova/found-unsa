"""Registro, inicio y cierre de sesión (Supabase Auth)."""
from . import cliente
from .config import DOMINIO, MIN_CLAVE
from .errores import ReglaError

MSG_DOMINIO = f"Solo se aceptan correos institucionales ({DOMINIO})."


def _validar_correo(email: str) -> str:
    email = (email or "").strip().lower()
    if not email.endswith(DOMINIO):  # aviso inmediato; el servidor también lo rechaza (trigger en la base)
        raise ReglaError(MSG_DOMINIO)
    return email


def registrar(nombre: str, email: str, clave: str) -> bool:
    """Crea la cuenta. Devuelve True si hay que confirmar el correo antes de ingresar (CU-02)."""
    email = _validar_correo(email)
    if not (nombre or "").strip() or len(nombre.strip()) > 60:
        raise ReglaError("El nombre es obligatorio (máximo 60 caracteres).")
    if len(clave or "") < MIN_CLAVE:
        raise ReglaError(f"La contraseña debe tener al menos {MIN_CLAVE} caracteres.")
    return cliente.auth_registro(email, clave, nombre.strip(), MSG_DOMINIO)


def iniciar_sesion(email: str, clave: str) -> dict:
    """Devuelve el perfil (id, email, nombre, rol, bloqueado) del usuario autenticado."""
    email = _validar_correo(email)
    if not clave:
        raise ReglaError("Escribe tu contraseña.")
    uid = cliente.auth_login(email, clave, MSG_DOMINIO)
    return perfil(uid)


def perfil(uid: str) -> dict:
    filas = cliente.seleccionar(uid, "perfiles", id=f"eq.{uid}", select="id,email,nombre,rol,bloqueado")
    if not filas:
        raise ReglaError("No se encontró tu perfil. Contacta al administrador.")
    return filas[0]


def reenviar_confirmacion(email: str) -> None:
    cliente.auth_reenviar(_validar_correo(email))


def cerrar_sesion(uid: str) -> None:
    cliente.auth_salir(uid)
