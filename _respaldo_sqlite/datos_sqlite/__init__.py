"""Capa de datos: SQLite y reglas de negocio. La interfaz solo usa esta fachada."""
from .config import DB_PATH, DOMINIO, CATEGORIAS, ALFABETO_CODIGO, HORAS_CODIGO, MAX_RECLAMOS_ACTIVOS, MIN_DESC_RECLAMO, DIAS_PENDIENTE, DIAS_ARCHIVADO
from .conexion import ReglaError, conectar
from .esquema import iniciar
from .auditoria import bitacora
from .cuentas import registrar, iniciar_sesion, perfil
from .publicaciones import puntos_activos, publicar, mis_publicaciones, cancelar_publicacion, pendientes, confirmar_recepcion, rechazar_publicacion
from .catalogo import catalogo
from .reclamos import crear_reclamo, mis_reclamos, cancelar_reclamo
from .entregas import buscar_codigo, entregar, rechazar_reclamo
from .administracion import usuarios, cambiar_rol, bloquear, puntos_todos, guardar_punto, activar_punto
