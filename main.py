"""Encontrado UNSA — punto de entrada (escritorio, web, Android e iOS con el mismo código)."""
import flet as ft

from app import datos
from app.ui.aplicacion import App


def main(page: ft.Page):
    datos.iniciar()
    App(page)


if __name__ == "__main__":
    ft.run(main)
