"""Constantes de negocio y configuración."""
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent.parent / "encontrado.db"


DOMINIO = "@unsa.edu.pe"


CATEGORIAS = [
    "Electrónicos",
    "Documentos y tarjetas",
    "Llaves",
    "Ropa y accesorios",
    "Útiles y libros",
    "Otros",
]


ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0, O, 1, I


HORAS_CODIGO = 48


MAX_RECLAMOS_ACTIVOS = 3


MIN_DESC_RECLAMO = 20


DIAS_PENDIENTE = 7


DIAS_ARCHIVADO = 60
