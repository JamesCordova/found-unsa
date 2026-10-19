"""Cliente HTTP de Supabase (Auth + PostgREST) con httpx. Sin dependencias nativas.

Las sesiones se guardan por id de usuario, no en una variable global única: con `flet run --web`
varias personas comparten el mismo proceso de Python y no deben mezclar sus tokens.
"""
import time
from datetime import datetime

import httpx

from .config import SUPABASE_KEY, SUPABASE_URL
from .errores import ConfiguracionError, ReglaError, SesionExpiradaError, SinConexionError

MENSAJE_SIN_CONEXION = "Sin conexión con el servidor. Revisa tu internet e inténtalo de nuevo."
CAMPOS_FECHA = {"fecha_hallazgo", "recibido_en", "creado_en", "vence_en", "resuelto_en"}

_http = httpx.Client(timeout=15)
_sesiones: dict[str, dict] = {}  # id de usuario -> {"acceso", "renovacion", "expira"}


def verificar_configuracion() -> None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ConfiguracionError(
            "Falta configurar Supabase. Copia .env.example a .env y completa SUPABASE_URL y SUPABASE_KEY.")


# ---------------------------------------------------------------- HTTP base
def _cabeceras(token: str | None = None) -> dict:
    cab = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    if token:
        cab["Authorization"] = f"Bearer {token}"
    return cab


def _enviar(metodo: str, ruta: str, *, token: str | None = None, json=None, params=None) -> httpx.Response:
    try:
        return _http.request(metodo, f"{SUPABASE_URL}{ruta}", headers=_cabeceras(token), json=json, params=params)
    except httpx.HTTPError as e:  # TransportError, timeouts, DNS…
        raise SinConexionError(MENSAJE_SIN_CONEXION) from e


def _cuerpo(r: httpx.Response) -> dict:
    try:
        datos = r.json()
        return datos if isinstance(datos, dict) else {}
    except ValueError:
        return {}


# ---------------------------------------------------------------- Auth
MENSAJES_AUTH = {
    "invalid_credentials": "Correo o contraseña incorrectos.",
    "email_not_confirmed": "Confirma tu correo antes de ingresar. Revisa tu bandeja de entrada y la carpeta de spam.",
    "user_already_exists": "Ya existe una cuenta con ese correo.",
    "email_exists": "Ya existe una cuenta con ese correo.",
    "weak_password": "La contraseña es muy débil: usa al menos 6 caracteres.",
    "over_email_send_rate_limit": "Se enviaron demasiados correos. Espera unos minutos e inténtalo de nuevo.",
    "over_request_rate_limit": "Demasiados intentos. Espera un momento e inténtalo de nuevo.",
    "signup_disabled": "El registro de cuentas está desactivado.",
}


def _error_auth(r: httpx.Response, dominio_msg: str) -> ReglaError:
    cuerpo = _cuerpo(r)
    codigo = cuerpo.get("error_code") or cuerpo.get("code") or ""
    if codigo in MENSAJES_AUTH:
        return ReglaError(MENSAJES_AUTH[codigo])
    texto = str(cuerpo.get("msg") or cuerpo.get("message") or cuerpo.get("error_description") or "")
    if "Database error saving new user" in texto:  # el trigger de dominio rechazó el correo
        return ReglaError(dominio_msg)
    if r.status_code == 429:
        return ReglaError(MENSAJES_AUTH["over_email_send_rate_limit"])
    return ReglaError(texto or f"No se pudo completar la operación (código {r.status_code}).")


def _guardar_sesion(datos: dict) -> str:
    uid = datos["user"]["id"]
    _sesiones[uid] = {"acceso": datos["access_token"], "renovacion": datos["refresh_token"],
                      "expira": time.time() + int(datos.get("expires_in", 3600))}
    return uid


def auth_login(email: str, clave: str, dominio_msg: str) -> str:
    r = _enviar("POST", "/auth/v1/token", params={"grant_type": "password"}, json={"email": email, "password": clave})
    if r.status_code >= 400:
        raise _error_auth(r, dominio_msg)
    return _guardar_sesion(r.json())


def auth_registro(email: str, clave: str, nombre: str, dominio_msg: str) -> bool:
    """Devuelve True si hay que confirmar el correo antes de ingresar."""
    r = _enviar("POST", "/auth/v1/signup", json={"email": email, "password": clave, "data": {"nombre": nombre}})
    if r.status_code >= 400:
        raise _error_auth(r, dominio_msg)
    return "access_token" not in r.json()


def auth_reenviar(email: str) -> None:
    r = _enviar("POST", "/auth/v1/resend", json={"type": "signup", "email": email})
    if r.status_code >= 400:
        raise _error_auth(r, "")


def auth_salir(uid: str) -> None:
    sesion = _sesiones.pop(uid, None)
    if sesion:
        try:
            _enviar("POST", "/auth/v1/logout", token=sesion["acceso"])
        except ReglaError:
            pass  # cerrar localmente basta aunque no haya conexión


def _token(uid: str) -> str:
    sesion = _sesiones.get(uid)
    if not sesion:
        raise SesionExpiradaError("Tu sesión expiró. Vuelve a iniciar sesión.")
    if sesion["expira"] - 60 < time.time():  # renovar antes de que venza
        r = _enviar("POST", "/auth/v1/token", params={"grant_type": "refresh_token"},
                    json={"refresh_token": sesion["renovacion"]})
        if r.status_code >= 400:
            _sesiones.pop(uid, None)
            raise SesionExpiradaError("Tu sesión expiró. Vuelve a iniciar sesión.")
        _guardar_sesion(r.json())
        sesion = _sesiones[uid]
    return sesion["acceso"]


# ---------------------------------------------------------------- PostgREST
def _error_rest(r: httpx.Response) -> ReglaError:
    cuerpo = _cuerpo(r)
    if r.status_code == 401 or cuerpo.get("code") == "PGRST301":
        return SesionExpiradaError("Tu sesión expiró. Vuelve a iniciar sesión.")
    if cuerpo.get("code") == "P0001":  # raise exception de nuestras funciones: el mensaje ya es para el usuario
        return ReglaError(cuerpo.get("message", "Operación rechazada."))
    if cuerpo.get("code") == "42501" or r.status_code == 403:
        return ReglaError("No tienes permiso para hacer esto.")
    if r.status_code >= 500:
        return SinConexionError("El servidor no respondió bien. Inténtalo de nuevo en unos segundos.")
    return ReglaError(cuerpo.get("message") or f"No se pudo completar la operación (código {r.status_code}).")


def _normalizar(valor):
    """Fechas del servidor (UTC, ISO) -> hora local sin zona, como 'AAAA-MM-DD HH:MM:SS' (lo que usa la interfaz)."""
    if isinstance(valor, list):
        return [_normalizar(v) for v in valor]
    if isinstance(valor, dict):
        salida = {}
        for k, v in valor.items():
            if k in CAMPOS_FECHA and isinstance(v, str):
                salida[k] = datetime.fromisoformat(v).astimezone().replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")
            else:
                salida[k] = _normalizar(v)
        return salida
    return valor


def rpc(uid: str, funcion: str, **parametros):
    """Llama a una función de Postgres (/rest/v1/rpc/<funcion>) como el usuario `uid`."""
    r = _enviar("POST", f"/rest/v1/rpc/{funcion}", token=_token(uid), json=parametros)
    if r.status_code >= 400:
        raise _error_rest(r)
    return _normalizar(r.json()) if r.content else None


def seleccionar(uid: str, tabla: str, **filtros) -> list[dict]:
    """GET /rest/v1/<tabla>?<filtros> (la seguridad por fila decide qué filas se ven)."""
    r = _enviar("GET", f"/rest/v1/{tabla}", token=_token(uid), params=filtros)
    if r.status_code >= 400:
        raise _error_rest(r)
    return _normalizar(r.json())
