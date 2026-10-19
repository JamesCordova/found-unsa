"""Encontrado UNSA — punto de entrada (escritorio, web, Android e iOS con el mismo código)."""
import flet as ft

from app import datos
from app.ui.aplicacion import App


def main(page: ft.Page):
    try:
        datos.iniciar()  # comprueba que el archivo .env esté configurado
    except datos.ConfiguracionError as e:
        page.add(ft.SafeArea(ft.Container(ft.Text(str(e), size=18), padding=24)))
        return
    App(page)


if __name__ == "__main__":
    ft.run(main)
