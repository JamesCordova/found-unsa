"""Widgets reutilizables: marca, campos, botones, chips de estado."""
from datetime import datetime

import flet as ft

from app.ui.tema import ESTADOS


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


def atras(app, texto="Volver"):
    return ft.TextButton(texto, icon=ft.Icons.ARROW_BACK, on_click=lambda _: app.ir(vista=None))
