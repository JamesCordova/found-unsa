"""Pantalla: perfil."""
import flet as ft

from app import datos as db
from app.ui.componentes import boton, chip_estado, titulo, vacio


def pantalla_perfil(app) -> ft.Control:
    return ft.Column([
        titulo(app.user["nombre"], app.user["email"]),
        ft.Switch(label="Modo oscuro", value=app.page.theme_mode == ft.ThemeMode.DARK,
                  on_change=app.alternar_tema),
        ft.Row([boton("Cerrar sesión", lambda _: app.cerrar_sesion(), ft.Icons.LOGOUT, tonal=True)]),
        ft.ExpansionTile(title=ft.Text("Reglas de uso y privacidad"), controls=[ft.Container(ft.Text(
            "• Solo se guardan correo, nombre, publicaciones, reclamos y bitácora.\n"
            "• No se guardan DNI ni fotos de documentos.\n"
            "• Quien publica un objeto no puede reclamarlo.\n"
            "• La app ordena el proceso; la identidad la verifica el funcionario en persona.", size=14),
            padding=12)]),
        ft.Divider(),
        titulo("Mis publicaciones"),
        *lista_mis_publicaciones(app),
    ], spacing=12)


def lista_mis_publicaciones(app) -> list[ft.Control]:
    items = db.mis_publicaciones(app.user["id"])
    if not items:
        return [vacio("Aún no publicaste nada.")]
    tarjetas = []
    for o in items:
        fila = [ft.Row([ft.Text(o["categoria"], weight="bold", size=16), chip_estado(o["estado"])],
                       alignment="spaceBetween", wrap=True),
                ft.Text(o["descripcion_publica"], size=16)]
        if o["estado"] == "RECHAZADO":
            fila.append(ft.Text(f"Motivo: {o['motivo']}", size=14, color=ft.Colors.ERROR))
        if o["estado"] == "PENDIENTE_RECEPCION":
            fila.append(ft.OutlinedButton("Cancelar publicación", icon=ft.Icons.CLOSE, on_click=(
                lambda _, oid=o["id"]: app.hacer(lambda: db.cancelar_publicacion(app.user["id"], oid),
                                                  "Publicación cancelada.", app.render))))
        tarjetas.append(ft.Card(ft.Container(ft.Column(fila, spacing=6), padding=14)))
    return tarjetas
