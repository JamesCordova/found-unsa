"""Colores de estado, ancho máximo, fuentes y tema claro/oscuro."""
import flet as ft

ESTADOS = {  # texto + color + icono: nunca solo color
    "PENDIENTE_RECEPCION": ("Pendiente de recepción", ft.Colors.ORANGE_700, ft.Icons.HOURGLASS_TOP),
    "EN_CUSTODIA": ("En custodia", ft.Colors.GREEN_700, ft.Icons.VERIFIED_USER),
    "ENTREGADO": ("Entregado", ft.Colors.GREY_700, ft.Icons.CHECK_CIRCLE),
    "RECHAZADO": ("Rechazado", ft.Colors.RED_700, ft.Icons.CANCEL),
    "ARCHIVADO": ("Archivado", ft.Colors.GREY_600, ft.Icons.INVENTORY_2),
    "activo": ("Activo", ft.Colors.GREEN_700, ft.Icons.PENDING),
    "entregado": ("Entregado", ft.Colors.GREY_700, ft.Icons.CHECK_CIRCLE),
    "rechazado": ("Rechazado", ft.Colors.RED_700, ft.Icons.CANCEL),
    "vencido": ("Vencido", ft.Colors.ORANGE_700, ft.Icons.TIMER_OFF),
    "cancelado": ("Cancelado", ft.Colors.GREY_600, ft.Icons.BLOCK),
}
ANCHO_MAX = 600

_GF = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/"
FUENTES = {"Poppins": _GF + "Poppins-Regular.ttf", "PoppinsBold": _GF + "Poppins-Bold.ttf"}


def aplicar_tema(page: ft.Page) -> None:
    page.title = "Encontrado UNSA"
    page.fonts = FUENTES
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO, font_family="Poppins")
    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO, font_family="Poppins")
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
