"""Pantalla: recepción (funcionario)."""
import flet as ft

from app import datos as db
from app.ui.componentes import boton, campo, chip_estado, hace, imagen_objeto, titulo, vacio


def pantalla_recepcion(app) -> ft.Control:
    items = db.pendientes()
    tarjetas = []
    for o in items:
        detalle = campo("Detalle oculto de verificación (obligatorio)",
                        hint_text="Marca, rayón, fondo de pantalla…")
        notas = campo("Notas internas (opcional)")
        motivo = campo("Motivo del rechazo", hint_text="No llegó el objeto, duplicado, contenido indebido")
        tarjetas.append(ft.Card(ft.Container(ft.Column([
            ft.Row([
                imagen_objeto(o, 72, 72, 10),
                ft.Column([ft.Text(o["categoria"], weight="bold", size=16),
                           ft.Text(o["descripcion_publica"], size=15, max_lines=3,
                                   overflow=ft.TextOverflow.ELLIPSIS),
                           ft.Text(f"{o['lugar_hallazgo']} · publicado {hace(o['creado_en'])}", size=13,
                                   color=ft.Colors.ON_SURFACE_VARIANT)], spacing=2, expand=True)], spacing=12),
            ft.Row([chip_estado(o["estado"]), ft.Text(f"Punto: {o['punto']}", size=13)], wrap=True),
            detalle, notas,
            ft.Row([boton("Confirmar recepción", (
                lambda _, oid=o["id"], d=detalle, n=notas: app.hacer(
                    lambda: db.confirmar_recepcion(app.user["id"], oid, d.value or "", n.value or ""),
                    "Recepción confirmada: el objeto ya es visible.", app.render)), ft.Icons.CHECK)]),
            motivo,
            ft.Row([ft.OutlinedButton("Rechazar", icon=ft.Icons.CLOSE, height=48, expand=True, on_click=(
                lambda _, oid=o["id"], m=motivo: app.confirmar(
                    "¿Rechazar la publicación?", "Quedará registrada con el motivo indicado.",
                    lambda: app.hacer(lambda: db.rechazar_publicacion(app.user["id"], oid, m.value or ""),
                                      "Publicación rechazada.", app.render),
                    "Rechazar")))]),
        ], spacing=8), padding=14)))
    return ft.Column([titulo("Recepción", "Publicaciones pendientes de confirmar"),
                      *(tarjetas or [vacio("No hay publicaciones pendientes.\n¡Todo al día!",
                                           ft.Icons.TASK_ALT)])], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
