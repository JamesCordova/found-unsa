"""Constantes de negocio y configuración de Supabase (leída de .env)."""
import os
from pathlib import Path

try:
    from . import config_web as _config_web
except ImportError:
    _config_web = None

DOMINIO = "@unsa.edu.pe"
CATEGORIAS = [
    "Electrónicos",
    "Documentos y tarjetas",
    "Llaves",
    "Ropa y accesorios",
    "Útiles y libros",
    "Otros",
]
# Solo para mostrar en pantalla: las reglas reales se aplican en la base (supabase/migrations/002_funciones.sql).
HORAS_CODIGO = 48
MAX_RECLAMOS_ACTIVOS = 3
MIN_DESC_RECLAMO = 20
MIN_CLAVE = 6


def _leer_env() -> dict[str, str]:
    """Lee .env de la raíz del proyecto (sin dependencias); las variables del sistema tienen prioridad."""
    valores: dict[str, str] = {}
    ruta = Path(__file__).resolve().parent.parent.parent / ".env"
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                valores[clave.strip()] = valor.strip().strip('"').strip("'")
    for clave in ("SUPABASE_URL", "SUPABASE_KEY", "DEMO_CLAVE"):
        if os.environ.get(clave):
            valores[clave] = os.environ[clave]
    return valores


_ENV = _leer_env()
SUPABASE_URL = getattr(_config_web, "SUPABASE_URL", "").rstrip("/") or _ENV.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = getattr(_config_web, "SUPABASE_KEY", "") or _ENV.get(
    "SUPABASE_KEY", ""
)  # clave publicable (anon): es pública por diseño; NUNCA la service_role
DEMO_CLAVE = _ENV.get("DEMO_CLAVE", "")  # si está definida, el login muestra el acceso rápido de demostración
