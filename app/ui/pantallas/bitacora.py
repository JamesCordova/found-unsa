"""Pantalla: bitacora."""
import flet as ft

from app import datos as db
from app.ui.componentes import campo, titulo, vacio


def pantalla_bitacora(app) -> ft.Control:
    lista = ft.Column(spacing=6)

    def cargar(texto=""):
        filas = db.bitacora(app.user["id"], texto.strip())
        lista.controls = [ft.ListTile(
            leading=ft.Icon(ft.Icons.HISTORY),
            title=ft.Text(f"{a['accion']}  ({a['estado_anterior'] or '—'} → {a['estado_nuevo'] or '—'})", size=15),
            subtitle=ft.Text(f"{a['creado_en']} · {a['actor'] or 'sistema'}"
                             + (f" · {a['detalle']}" if a["detalle"] else ""), size=13)) for a in filas
        ] or [vacio("Sin registros.", ft.Icons.RECEIPT_LONG)]

    filtro = campo("Filtrar por acción (ej. entregado)", prefix_icon=ft.Icons.FILTER_ALT)

    def al_filtrar(e):
        cargar(e.control.value or "")
        app.page.update()
    filtro.on_change = al_filtrar
    cargar()
    return ft.Column([titulo("Bitácora de auditoría", "Registro inmutable de cada cambio"),
                      filtro, lista], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
