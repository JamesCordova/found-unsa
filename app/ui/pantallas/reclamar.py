"""Pantalla: reclamar."""
import flet as ft

from app import datos as db
from app.ui.componentes import atras, boton, campo, titulo


def pantalla_reclamar(app, o: dict) -> ft.Control:
    desc = campo("Describe el objeto con tus palabras", multiline=True, min_lines=4,
                      hint_text=f"Mínimo {db.MIN_DESC_RECLAMO} caracteres: color, marca, contenido…")

    def enviar(_):
        def accion():
            db.crear_reclamo(app.user["id"], o["id"], desc.value or "")
        app.hacer(accion, "Reclamo creado. Presenta tu código en el punto de custodia.",
                   lambda: app.ir(tab=2, vista=None))

    return ft.Column([
        atras(app), titulo("Reclamar objeto", o["descripcion_publica"]),
        ft.Text("El funcionario comparará tu descripción con un detalle que solo el dueño conoce y verificará "
                "tu identidad en persona. El código dura 48 horas.", size=16),
        desc, ft.Row([boton("Generar código", enviar, ft.Icons.KEY)]),
    ], spacing=12)
