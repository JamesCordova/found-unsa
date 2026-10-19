"""Pantalla: error de red con botón de reintentar (estado que toda pantalla debe cubrir)."""
import flet as ft

from app.ui.componentes import boton


def pantalla_sin_conexion(app, mensaje: str) -> ft.Control:
    return ft.Column([
        ft.Container(height=40),
        ft.Icon(ft.Icons.WIFI_OFF, size=64, color=ft.Colors.OUTLINE),
        ft.Text("No se pudo conectar", size=22, weight="bold", text_align=ft.TextAlign.CENTER),
        ft.Text(mensaje, size=16, text_align=ft.TextAlign.CENTER, color=ft.Colors.ON_SURFACE_VARIANT),
        ft.Row([boton("Reintentar", lambda _: app.render(), ft.Icons.REFRESH)]),
    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
