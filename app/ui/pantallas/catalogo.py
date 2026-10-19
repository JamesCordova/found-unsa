"""Pantalla: catalogo."""
import flet as ft

from app import datos as db
from app.ui.componentes import campo, titulo, vacio


def pantalla_catalogo(app) -> ft.Control:
    lista = ft.Column(spacing=8)
    puntos = db.puntos_activos()

    def cargar(_=None):
        f = app.filtro
        items = db.catalogo(f["categoria"] or None, f["punto"] or None, f["texto"])
        lista.controls = [tarjeta_objeto(app, o) for o in items] or [
            vacio("No hay objetos en custodia con esos filtros.", ft.Icons.SEARCH_OFF)]
        app.page.update()

    def cambiar(clave):
        def h(e):
            app.filtro[clave] = e.control.value or ""
            cargar()
        return h

    buscar = campo("Buscar en la descripción", prefix_icon=ft.Icons.SEARCH, value=app.filtro["texto"])
    buscar.on_change = cambiar("texto")
    cat = ft.Dropdown(label="Categoría", value=app.filtro["categoria"], expand=True,
                      options=[ft.DropdownOption(key="", text="Todas")] +
                              [ft.DropdownOption(key=c, text=c) for c in db.CATEGORIAS],
                      on_select=cambiar("categoria"))
    pto = ft.Dropdown(label="Punto de custodia", value=app.filtro["punto"], expand=True,
                      options=[ft.DropdownOption(key="", text="Todos")] +
                              [ft.DropdownOption(key=str(x["id"]), text=x["nombre"]) for x in puntos],
                      on_select=cambiar("punto"))
    cargar_inicial = ft.Column([titulo("Objetos en custodia", "Hallados y guardados en un punto oficial"),
                                buscar, ft.Row([cat, pto]), lista], spacing=12)
    f = app.filtro
    items = db.catalogo(f["categoria"] or None, f["punto"] or None, f["texto"])
    lista.controls = [tarjeta_objeto(app, o) for o in items] or [
        vacio("No hay objetos en custodia con esos filtros.", ft.Icons.SEARCH_OFF)]
    return cargar_inicial


def tarjeta_objeto(app, o: dict) -> ft.Control:
    return ft.Card(ft.Container(
        ft.Column([
            ft.Row([ft.Icon(ft.Icons.INVENTORY_2_OUTLINED), ft.Text(o["categoria"], weight="bold", size=16)]),
            ft.Text(o["descripcion_publica"], size=16),
            ft.Text(f"{o['lugar_hallazgo']} · {o['fecha_hallazgo'][:16]}", size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Text(f"Custodia: {o['punto']}", size=14, color=ft.Colors.ON_SURFACE_VARIANT),
        ], spacing=4),
        padding=14, ink=True, on_click=lambda _: app.ir(vista=("detalle", o))))
