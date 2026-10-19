"""Pantalla: mis_reclamos."""
import flet as ft

from app import datos as db
from app.ui.componentes import chip_estado, tiempo_restante, titulo, vacio


def pantalla_mis_reclamos(app) -> ft.Control:
    items = db.mis_reclamos(app.user["id"])
    tarjetas: list[ft.Control] = []
    for r in items:
        fila: list[ft.Control] = [
            ft.Row([ft.Text(r["descripcion_publica"], size=16, expand=True), chip_estado(r["estado"])],
                   vertical_alignment="start")]
        if r["estado"] == "activo":
            fila += [
                ft.Container(ft.Text(r["codigo"], size=40, weight="bold", font_family="monospace"),
                             alignment=ft.Alignment.CENTER, padding=8,
                             bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=8),
                ft.Text(f"Vence: {tiempo_restante(r['vence_en'])}", size=16),
                ft.Text(f"Retira en {r['punto']} · {r['ubicacion']} · {r['horario']}", size=14),
                ft.Text("Lleva tu carné o DNI.", size=14, italic=True),
                ft.OutlinedButton("Cancelar reclamo", icon=ft.Icons.CLOSE, on_click=(
                    lambda _, rid=r["id"]: app.hacer(lambda: db.cancelar_reclamo(app.user["id"], rid),
                                                      "Reclamo cancelado.", app.render)))]
        elif r["estado"] == "vencido":
            fila.append(ft.Text("El código venció. Puedes reclamar de nuevo desde el catálogo.", size=14))
        elif r["estado"] == "rechazado":
            fila.append(ft.Text(f"Motivo: {r['motivo']}", size=14, color=ft.Colors.ERROR))
        tarjetas.append(ft.Card(ft.Container(ft.Column(fila, spacing=8), padding=14)))
    return ft.Column([
        titulo("Mis reclamos", f"Máximo {db.MAX_RECLAMOS_ACTIVOS} activos a la vez"),
        *(tarjetas or [vacio("No tienes reclamos. Busca tu objeto en el catálogo.",
                                   ft.Icons.CONFIRMATION_NUMBER)])], spacing=12)
