"""Pantalla: catálogo."""
import flet as ft

from app import datos as db
from app.datos import SinConexionError
from app.ui.componentes import (abrir_selector_punto, campo, campo_selector, es_nuevo, hace, imagen_objeto,
                                titulo, vacio)
from app.ui.tema import CATEGORIA_ICONOS


def pantalla_catalogo(app) -> ft.Control:
    puntos = db.puntos_activos(app.user["id"])
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
        try:
            items = db.catalogo(app.user["id"], f["categoria"] or None, f["punto"] or None, f["texto"])
        except SinConexionError as e:  # búsqueda en vivo: el aviso va en la lista, con botón de reintentar
            lista.controls = [vacio(str(e), ft.Icons.WIFI_OFF),
                              ft.Row([ft.OutlinedButton("Reintentar", icon=ft.Icons.REFRESH, on_click=reintentar)])]
            contador.value = ""
            return
        chips.controls = [ft.Chip(label=ft.Text("Todas"), leading=ft.Icon(ft.Icons.APPS),
                                  selected=not f["categoria"], on_click=lambda _: elegir_categoria(""))] + [
            ft.Chip(label=ft.Text(c), leading=ft.Icon(CATEGORIA_ICONOS[c]), selected=f["categoria"] == c,
                    on_click=lambda _, c=c: elegir_categoria(c)) for c in db.CATEGORIAS]
        contador.value = f"{len(items)} objeto{'s' if len(items) != 1 else ''} en custodia"
        lista.controls = [tarjeta_objeto(app, o) for o in items] or [
            vacio("No hay objetos con esos filtros.\nPrueba con otra categoría o borra la búsqueda.",
                  ft.Icons.SEARCH_OFF)]

    def reintentar(_):
        refrescar()
        app.page.update()

    def al_buscar(e):
        app.filtro["texto"] = e.control.value or ""
        borrar.visible = bool(app.filtro["texto"])
        refrescar()
        app.page.update()

    def limpiar(_):
        app.filtro["texto"] = ""
        buscar.value = ""
        borrar.visible = False
        refrescar()
        app.page.update()

    buscar = campo("Buscar por descripción o lugar", prefix_icon=ft.Icons.SEARCH, value=app.filtro["texto"],
                   on_change=al_buscar, expand=True)
    borrar = ft.IconButton(ft.Icons.CLEAR, tooltip="Borrar búsqueda", on_click=limpiar,
                           visible=bool(app.filtro["texto"]))  # fuera del campo: no altera el centrado del texto
    filtros = [ft.Row([buscar, borrar], vertical_alignment=ft.CrossAxisAlignment.CENTER), chips]
    if len(puntos) > 1:
        zona_punto = ft.Column()

        def elegir_punto(pid):
            app.filtro["punto"] = str(pid) if pid else ""
            pintar_filtro_punto()
            refrescar()
            app.page.update()

        def pintar_filtro_punto():
            actual = app.filtro["punto"] or None
            p = next((x for x in puntos if x["id"] == actual), None)
            zona_punto.controls = [campo_selector(
                ft.Icons.STORE_OUTLINED, p["nombre"] if p else "Todos los puntos", None,
                lambda _: abrir_selector_punto(app, puntos, actual, elegir_punto, con_todos=True,
                                               titulo_dialogo="Punto de custodia"))]
        pintar_filtro_punto()
        filtros.append(zona_punto)
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
