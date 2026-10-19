"""Pantalla: detalle."""
import flet as ft

from app.ui.componentes import atras, boton, chip_estado, titulo


def pantalla_detalle(app, o: dict) -> ft.Control:
    propio = o["publicado_por"] == app.user["id"]
    accion = (ft.Text("Tú publicaste este objeto: no puedes reclamarlo.", size=16, italic=True)
              if propio else boton("Es mío", lambda _: app.ir(vista=("reclamar", o)),
                                        ft.Icons.BACK_HAND))
    return ft.Column([
        atras(app, "Catálogo"),
        titulo(o["categoria"]),
        chip_estado("EN_CUSTODIA"),
        ft.Text(o["descripcion_publica"], size=18),
        ft.Divider(),
        ft.ListTile(leading=ft.Icon(ft.Icons.PLACE), title=ft.Text("Dónde se encontró"),
                    subtitle=ft.Text(o["lugar_hallazgo"])),
        ft.ListTile(leading=ft.Icon(ft.Icons.SCHEDULE), title=ft.Text("Cuándo"),
                    subtitle=ft.Text(o["fecha_hallazgo"][:16])),
        ft.ListTile(leading=ft.Icon(ft.Icons.STORE), title=ft.Text(f"Retiro en: {o['punto']}"),
                    subtitle=ft.Text(f"{o['ubicacion']} · {o['horario']}")),
        ft.Row([accion]),
    ], spacing=8)
