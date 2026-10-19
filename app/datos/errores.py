"""Errores que la interfaz muestra al usuario."""


class ReglaError(Exception):
    """Operación rechazada por una regla de negocio; el mensaje va tal cual al usuario."""


class SinConexionError(ReglaError):
    """No se pudo hablar con el servidor (sin internet, servidor caído o tiempo agotado)."""


class SesionExpiradaError(ReglaError):
    """La sesión ya no es válida: hay que volver a iniciar sesión."""


class ConfiguracionError(Exception):
    """Falta configurar el proyecto (archivo .env)."""
