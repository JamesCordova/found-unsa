"""Pantalla: mis reclamos."""
import flet as ft

from app import datos as db
from app.ui.componentes import chip_estado, imagen_objeto, tiempo_restante, titulo, vacio


def copiar_codigo(app, codigo: str):
    """Devuelve el manejador async del botón (Flet solo espera funciones async directas)."""
    async def copiar(_):
        await app.portapapeles.set(codigo)
        app.aviso("Código copiado")
    return copiar


def pantalla_mis_reclamos(app) -> ft.Control:
    items = db.mis_reclamos(app.user["id"])
    tarjetas: list[ft.Control] = []
    for r in items:
        cabecera = ft.Row([
            imagen_objeto(r, 64, 64, 10),
            ft.Column([ft.Text(r["categoria"], weight="bold", size=16),
                       ft.Text(r["descripcion_publica"], size=14, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                       ], spacing=2, expand=True)], spacing=12)
        fila: list[ft.Control] = [cabecera, ft.Row([chip_estado(r["estado"])])]
        if r["estado"] == "activo":
            fila += [
                ft.Text("Tu código de retiro", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(ft.Text(r["codigo"], size=40, weight="bold", font_family="monospace",
                                     selectable=True),
                             alignment=ft.Alignment.CENTER, padding=8,
                             bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=8),
                ft.Row([ft.FilledTonalButton("Copiar código", icon=ft.Icons.CONTENT_COPY, height=44, expand=True,
                                             on_click=copiar_codigo(app, r["codigo"]))]),
                ft.Text(f"Vence: {tiempo_restante(r['vence_en'])}", size=16),
                ft.Text(f"Retira en {r['punto']} · {r['ubicacion']} · {r['horario']}", size=14),
                ft.Text("Lleva tu carné o DNI.", size=14, italic=True),
                ft.OutlinedButton("Cancelar reclamo", icon=ft.Icons.CLOSE, on_click=(
                    lambda _, rid=r["id"]: app.confirmar(
                        "¿Cancelar el reclamo?", "Tu código dejará de funcionar. Podrás reclamar de nuevo.",
                        lambda: app.hacer(lambda: db.cancelar_reclamo(app.user["id"], rid),
                                          "Reclamo cancelado.", app.render),
                        "Sí, cancelar")))]
        elif r["estado"] == "vencido":
            fila.append(ft.Text("El código venció. Puedes reclamar de nuevo desde el catálogo.", size=14))
        elif r["estado"] == "rechazado":
            fila.append(ft.Text(f"Motivo: {r['motivo']}", size=14, color=ft.Colors.ERROR))
        tarjetas.append(ft.Card(ft.Container(ft.Column(fila, spacing=8), padding=14)))
    return ft.Column([
        titulo("Mis reclamos", f"Máximo {db.MAX_RECLAMOS_ACTIVOS} activos a la vez"),
        *(tarjetas or [vacio("No tienes reclamos.\nBusca tu objeto en el catálogo y toca «Es mío».",
                             ft.Icons.CONFIRMATION_NUMBER)])], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
