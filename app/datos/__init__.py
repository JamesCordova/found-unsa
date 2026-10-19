"""Capa de datos: Supabase (Auth + Postgres). La interfaz solo usa esta fachada.

Las reglas de negocio y los permisos viven en la base (supabase/migrations); aquí solo se llama a la API.
"""
from .administracion import activar_punto, bloquear, cambiar_rol, guardar_punto, puntos_todos, usuarios
from .cliente import verificar_configuracion as iniciar
from .config import (CATEGORIAS, DEMO_CLAVE, DOMINIO, HORAS_CODIGO, MAX_RECLAMOS_ACTIVOS, MIN_CLAVE,
                     MIN_DESC_RECLAMO)
from .cuentas import cerrar_sesion, iniciar_sesion, perfil, reenviar_confirmacion, registrar
from .entregas import bitacora, buscar_codigo, entregar, rechazar_reclamo
from .errores import ConfiguracionError, ReglaError, SesionExpiradaError, SinConexionError
from .publicaciones import (cancelar_publicacion, catalogo, confirmar_recepcion, mis_publicaciones, pendientes,
                            publicar, puntos_activos, rechazar_publicacion)
from .reclamos import cancelar_reclamo, crear_reclamo, mis_reclamos
