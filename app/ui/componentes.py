"""Widgets reutilizables: marca, campos, botones, chips de estado."""
from datetime import datetime, timedelta

import flet as ft

from app.ui.tema import CATEGORIA_ICONOS, ESTADOS


def chip_estado(estado: str) -> ft.Control:
    texto, color, icono = ESTADOS[estado]
    return ft.Container(
        content=ft.Row([ft.Icon(icono, size=16, color=color), ft.Text(texto, size=14, color=color, weight="bold")],
                       spacing=4, tight=True),
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border=ft.Border.all(1, color), border_radius=16,
    )


def tiempo_restante(vence_en: str) -> str:
    resto = datetime.fromisoformat(vence_en) - datetime.now()
    if resto.total_seconds() <= 0:
        return "vencido"
    horas, resto_s = divmod(int(resto.total_seconds()), 3600)
    return f"{horas} h {resto_s // 60} min restantes"


def campo(etiqueta, **kw) -> ft.TextField:
    return ft.TextField(label=etiqueta, **kw)


def boton(texto, on_click, icono=None, tonal=False, ancho_total=True) -> ft.Control:
    cls = ft.FilledTonalButton if tonal else ft.FilledButton
    return cls(texto, icon=icono, on_click=on_click, height=48, expand=ancho_total)


def titulo(texto, sub=None) -> ft.Control:
    col = [ft.Text(texto, size=22, weight="bold")]
    if sub:
        col.append(ft.Text(sub, size=16, color=ft.Colors.ON_SURFACE_VARIANT))
    return ft.Column(col, spacing=2)


def vacio(texto, icono=ft.Icons.INBOX) -> ft.Control:
    return ft.Container(
        ft.Column([ft.Icon(icono, size=48, color=ft.Colors.OUTLINE), ft.Text(texto, size=16, text_align="center")],
                  horizontal_alignment="center"),
        padding=32, alignment=ft.Alignment.CENTER)


def caja_aviso(*textos: ft.Text) -> ft.Control:
    """Aviso ámbar con texto oscuro fijo: legible en modo claro y oscuro."""
    for t in textos:
        t.color = ft.Colors.BROWN_900
    return ft.Container(ft.Column(list(textos), spacing=4), padding=10,
                        bgcolor=ft.Colors.AMBER_200, border_radius=8)


def marca(grande: bool = False) -> ft.Control:
    """Logotipo: icono en cuadro redondeado + «Encontrado» + etiqueta UNSA."""
    k = 1.8 if grande else 1
    return ft.Row([
        ft.Container(ft.Icon(ft.Icons.TRAVEL_EXPLORE, color=ft.Colors.WHITE, size=22 * k),
                     bgcolor=ft.Colors.INDIGO, border_radius=10 * k, padding=6 * k),
        ft.Text("Encontrado", size=22 * k, font_family="PoppinsBold", weight=ft.FontWeight.W_400),
        ft.Container(ft.Text("UNSA", size=12 * k, color=ft.Colors.WHITE, font_family="PoppinsBold",
                             weight=ft.FontWeight.W_400),
                     bgcolor=ft.Colors.INDIGO, border_radius=6 * k,
                     padding=ft.Padding.symmetric(horizontal=6 * k, vertical=2 * k)),
    ], spacing=6 * k, tight=True, vertical_alignment="center")


def boton_tema(app) -> ft.Control:
    oscuro = app.page.theme_mode == ft.ThemeMode.DARK
    return ft.IconButton(ft.Icons.LIGHT_MODE if oscuro else ft.Icons.DARK_MODE,
                         tooltip="Cambiar a modo claro" if oscuro else "Cambiar a modo oscuro",
                         on_click=app.alternar_tema)


def imagen_objeto(o: dict, ancho: int | None = 88, alto: int = 88, radio: int = 12) -> ft.Control:
    """Foto del objeto desde su enlace; si no hay o falla, ícono de la categoría."""
    lado = min(ancho or alto, alto)
    respaldo = ft.Container(
        ft.Icon(CATEGORIA_ICONOS.get(o.get("categoria"), ft.Icons.CATEGORY), size=lado * 0.45,
                color=ft.Colors.ON_SURFACE_VARIANT),
        width=ancho, height=alto, alignment=ft.Alignment.CENTER,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=radio)
    if not o.get("foto_url"):
        return respaldo
    return ft.Image(src=o["foto_url"], width=ancho, height=alto, fit=ft.BoxFit.COVER, border_radius=radio,
                    error_content=respaldo)


def hace(fecha: str) -> str:
    """'2026-10-18 09:30:00' -> 'hace 3 h', 'ayer', 'hace 4 días'."""
    delta = datetime.now() - datetime.fromisoformat(fecha)
    if delta < timedelta(hours=1):
        return "hace unos minutos"
    if delta < timedelta(days=1):
        return f"hace {int(delta.total_seconds() // 3600)} h"
    if delta < timedelta(days=2):
        return "ayer"
    return f"hace {delta.days} días"


def es_nuevo(o: dict) -> bool:
    return bool(o.get("recibido_en")) and datetime.now() - datetime.fromisoformat(o["recibido_en"]) < timedelta(hours=48)


def ver_imagen_completa(app, o: dict) -> None:
    """Abre la foto completa en un diálogo, con zoom y desplazamiento."""
    if not o.get("foto_url"):
        return
    app.page.show_dialog(ft.AlertDialog(
        title=ft.Text(o["categoria"]),
        content=ft.Container(ft.InteractiveViewer(
            content=ft.Image(src=o["foto_url"], fit=ft.BoxFit.CONTAIN,
                             error_content=ft.Text("No se pudo cargar la imagen.")),
            min_scale=1, max_scale=5), width=600, height=480),
        actions=[ft.TextButton("Cerrar", on_click=lambda _: app.page.pop_dialog())]))


def imagen_completa(app, o: dict, alto: int = 220) -> ft.Control:
    """Foto en formato banner; al tocarla se abre el visor con la imagen entera."""
    if not o.get("foto_url"):
        return imagen_objeto(o, ancho=None, alto=alto // 2, radio=16)
    return ft.Container(
        ft.Stack([
            imagen_objeto(o, ancho=None, alto=alto, radio=16),
            ft.Container(ft.Icon(ft.Icons.ZOOM_OUT_MAP, size=18, color=ft.Colors.WHITE), right=8, bottom=8,
                         padding=6, border_radius=20, bgcolor=ft.Colors.with_opacity(0.55, ft.Colors.BLACK)),
        ], fit=ft.StackFit.EXPAND),  # EXPAND: la imagen ocupa todo el ancho del contenedor
        height=alto, border_radius=16, ink=True, tooltip="Toca para ver la imagen completa",
        on_click=lambda _: ver_imagen_completa(app, o))
