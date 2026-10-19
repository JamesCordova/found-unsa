"""Pantalla: catálogo."""
import flet as ft

from app import datos as db
from app.ui.componentes import campo, es_nuevo, hace, imagen_objeto, titulo, vacio
from app.ui.tema import CATEGORIA_ICONOS


def pantalla_catalogo(app) -> ft.Control:
    puntos = db.puntos_activos()
    chips = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
    lista = ft.Column(spacing=8)
    contador = ft.Text("", size=14, color=ft.Colors.ON_SURFACE_VARIANT)

    def elegir_categoria(valor):
        app.filtro["categoria"] = valor
        refrescar()
        app.page.update()

    def refrescar():
        """Reconstruye chips, contador y lista según los filtros actuales."""
        f = app.filtro
        items = db.catalogo(f["categoria"] or None, f["punto"] or None, f["texto"])
        chips.controls = [ft.Chip(label=ft.Text("Todas"), leading=ft.Icon(ft.Icons.APPS),
                                  selected=not f["categoria"], on_click=lambda _: elegir_categoria(""))] + [
            ft.Chip(label=ft.Text(c), leading=ft.Icon(CATEGORIA_ICONOS[c]), selected=f["categoria"] == c,
                    on_click=lambda _, c=c: elegir_categoria(c)) for c in db.CATEGORIAS]
        contador.value = f"{len(items)} objeto{'s' if len(items) != 1 else ''} en custodia"
        lista.controls = [tarjeta_objeto(app, o) for o in items] or [
            vacio("No hay objetos con esos filtros.\nPrueba con otra categoría o borra la búsqueda.",
                  ft.Icons.SEARCH_OFF)]

    def al_buscar(e):
        app.filtro["texto"] = e.control.value or ""
        refrescar()
        app.page.update()

    def limpiar(_):
        app.filtro["texto"] = ""
        buscar.value = ""
        refrescar()
        app.page.update()

    buscar = campo("Buscar por descripción o lugar", prefix_icon=ft.Icons.SEARCH, value=app.filtro["texto"],
                   on_change=al_buscar, height=48, dense=True,
                   content_padding=ft.Padding.symmetric(horizontal=12, vertical=0),
                   suffix=ft.IconButton(ft.Icons.CLEAR, icon_size=18, padding=0, tooltip="Borrar búsqueda",
                                        on_click=limpiar))
    filtros = [buscar, chips]
    if len(puntos) > 1:
        def al_elegir_punto(e):
            app.filtro["punto"] = e.control.value or ""
            refrescar()
            app.page.update()
        filtros.append(ft.Row([ft.Dropdown(
            label="Punto de custodia", value=app.filtro["punto"], expand=True, on_select=al_elegir_punto,
            options=[ft.DropdownOption(key="", text="Todos los puntos")] +
                    [ft.DropdownOption(key=str(x["id"]), text=x["nombre"]) for x in puntos])]))
    refrescar()
    return ft.Column([titulo("Objetos en custodia", "Hallados y guardados en un punto oficial"),
                      *filtros, contador, lista], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def tarjeta_objeto(app, o: dict) -> ft.Control:
    cabecera = [ft.Text(o["categoria"], weight="bold", size=16, expand=True)]
    if es_nuevo(o):
        cabecera.append(ft.Container(ft.Text("Nuevo", size=12, weight="bold", color=ft.Colors.WHITE),
                                     bgcolor=ft.Colors.INDIGO, border_radius=8,
                                     padding=ft.Padding.symmetric(horizontal=8, vertical=2)))
    return ft.Card(ft.Container(
        ft.Row([
            imagen_objeto(o),
            ft.Column([
                ft.Row(cabecera),
                ft.Text(o["descripcion_publica"], size=15, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"{o['lugar_hallazgo']} · hallado {hace(o['fecha_hallazgo'])}", size=13,
                        color=ft.Colors.ON_SURFACE_VARIANT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"Retiro: {o['punto']}", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
            ], spacing=2, expand=True),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
        padding=12, ink=True, on_click=lambda _: app.ir(vista=("detalle", o))))
