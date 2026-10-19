"""Pantalla: admin."""
import flet as ft

from app import datos as db
from app.ui.componentes import titulo


def pantalla_admin(app) -> ft.Control:
    filas = []
    for u in db.usuarios(app.user["id"]):
        propio = u["id"] == app.user["id"]
        rol = ft.Dropdown(value=u["rol"], disabled=propio, width=170,
                          options=[ft.DropdownOption(key=r, text=r) for r in ("usuario", "funcionario", "admin")],
                          on_select=lambda e, uid=u["id"]: confirmar_rol(app, uid, e.control.value))
        filas.append(ft.Card(ft.Container(ft.Column([
            ft.Text(f"{u['nombre']}  ·  {u['email']}", size=15),
            ft.Row([rol, ft.Switch(label="Bloqueado", value=bool(u["bloqueado"]), disabled=propio,
                                   on_change=lambda e, uid=u["id"]: app.hacer(
                                       lambda: db.bloquear(app.user["id"], uid, bool(e.control.value)),
                                       "Estado de bloqueo actualizado.", app.render))],
                   wrap=True, alignment="spaceBetween"),
        ], spacing=6), padding=12)))
    return ft.Column([titulo("Administración", "Roles y bloqueos"), *filas], spacing=12)


def confirmar_rol(app, uid: int, rol: str):
    def aplicar(_):
        app.page.pop_dialog()
        app.hacer(lambda: db.cambiar_rol(app.user["id"], uid, rol), "Rol actualizado.", app.render)

    def cancelar(_):
        app.page.pop_dialog()
        app.render()
    app.page.show_dialog(ft.AlertDialog(
        title=ft.Text("Confirmar cambio de rol"),
        content=ft.Text(f"¿Asignar el rol «{rol}» a este usuario? Queda registrado en la bitácora."),
        actions=[ft.TextButton("Cancelar", on_click=cancelar), ft.FilledButton("Confirmar", on_click=aplicar)]))
