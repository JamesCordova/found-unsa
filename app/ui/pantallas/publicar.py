"""Pantalla: publicar."""
from datetime import datetime

import flet as ft

from app import datos as db
from app.ui.componentes import boton, caja_aviso, campo, titulo


def pantalla_publicar(app) -> ft.Control:
    puntos = db.puntos_activos()
    cat = ft.Dropdown(label="Categoría",
                      options=[ft.DropdownOption(key=c, text=c) for c in db.CATEGORIAS])
    desc = campo("Descripción pública", multiline=True, min_lines=3, max_length=280,
                      helper="No incluyas datos que solo el dueño sabría.")
    lugar = campo("Lugar donde lo encontraste")
    fecha = campo("Fecha y hora aproximadas", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
    punto = ft.Dropdown(label="Punto de entrega",
                        options=[ft.DropdownOption(key=str(x["id"]), text=x["nombre"]) for x in puntos])
    aviso_doc = ft.Text("", size=14, color=ft.Colors.ORANGE_500)

    def al_cambiar_cat(_):
        if cat.value == "Documentos y tarjetas":
            aviso_doc.value = ("En documentos y tarjetas no se publica foto, y la descripción no debe "
                               "incluir nombres ni números (RN-08).")
        else:
            aviso_doc.value = ""
        app.page.update()
    cat.on_select = al_cambiar_cat

    def enviar(_):
        def accion():
            db.publicar(app.user["id"], cat.value or "", desc.value or "", lugar.value or "",
                        fecha.value or "", int(punto.value) if punto.value else None)
        app.hacer(accion, "Publicado. Déjalo en el punto de entrega para que el funcionario lo confirme.",
                   lambda: app.ir(tab=3))

    return ft.Column([
        titulo("Publicar un hallazgo", "Después déjalo físicamente en el punto elegido"),
        caja_aviso(ft.Text("No publiques dinero, armas, medicamentos ni sustancias: entrégalos "
                                "directamente al funcionario (RN-09).", size=14)),
        cat, aviso_doc, desc, lugar, fecha, punto,
        ft.Row([boton("Publicar", enviar, ft.Icons.PUBLISH)]),
    ], spacing=12)
