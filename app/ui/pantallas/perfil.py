"""Pantalla: perfil y mis publicaciones."""
import flet as ft

from app import datos as db
from app.ui.componentes import chip_estado, hace, imagen_objeto, titulo, vacio


ROLES = {"usuario": "Usuario", "funcionario": "Funcionario", "admin": "Administrador"}


def pantalla_perfil(app) -> ft.Control:
    es_usuario = app.user["rol"] == "usuario"
    contenido = [
        titulo(app.user["nombre"], app.user["email"]),
        ft.Row([ft.Chip(label=ft.Text(ROLES[app.user["rol"]]), leading=ft.Icon(ft.Icons.VERIFIED_USER))]),
        ft.Switch(label="Modo oscuro", value=app.page.theme_mode == ft.ThemeMode.DARK,
                  on_change=app.alternar_tema),
        ft.ExpansionTile(title=ft.Text("Reglas de uso y privacidad"), controls=[ft.Container(ft.Text(
            "• Solo se guardan correo, nombre, publicaciones, reclamos y bitácora.\n"
            "• No se guardan DNI ni archivos de imagen: las fotos son enlaces.\n"
            "• Quien publica un objeto no puede reclamarlo.\n"
            "• La app ordena el proceso; la identidad la verifica el funcionario en persona.", size=14),
            padding=12)]),
        ft.Row([ft.FilledButton(
            "Cerrar sesión", icon=ft.Icons.LOGOUT, height=48, expand=True,
            style=ft.ButtonStyle(bgcolor=ft.Colors.ERROR, color=ft.Colors.ON_ERROR),
            on_click=lambda _: app.confirmar("¿Cerrar sesión?", "Tendrás que ingresar de nuevo.",
                                             app.cerrar_sesion, "Cerrar sesión"))]),
    ]
    if es_usuario:
        contenido += [ft.Divider(), titulo("Mis publicaciones"), *lista_mis_publicaciones(app)]
    return ft.Column(contenido, spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def lista_mis_publicaciones(app) -> list[ft.Control]:
    items = db.mis_publicaciones(app.user["id"])
    if not items:
        return [vacio("Aún no publicaste nada.\nVe a «Publicar» cuando encuentres algo.")]
    tarjetas = []
    for o in items:
        detalle = [ft.Row([ft.Text(o["categoria"], weight="bold", size=16, expand=True)]),
                   ft.Text(o["descripcion_publica"], size=15, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                   ft.Text(f"Publicado {hace(o['creado_en'])}", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                   ft.Row([chip_estado(o["estado"])])]
        if o["estado"] == "RECHAZADO":
            detalle.append(ft.Text(f"Motivo: {o['motivo']}", size=14, color=ft.Colors.ERROR))
        if o["estado"] == "PENDIENTE_RECEPCION":
            detalle.append(ft.Text(f"Déjalo en: {o['punto']} para que lo confirmen.", size=13, italic=True))
            detalle.append(ft.OutlinedButton("Cancelar publicación", icon=ft.Icons.CLOSE, on_click=(
                lambda _, oid=o["id"]: app.confirmar(
                    "¿Cancelar la publicación?", "Se rechazará y ya no podrás editarla.",
                    lambda: app.hacer(lambda: db.cancelar_publicacion(app.user["id"], oid),
                                      "Publicación cancelada.", app.render),
                    "Sí, cancelar"))))
        tarjetas.append(ft.Card(ft.Container(
            ft.Row([imagen_objeto(o), ft.Column(detalle, spacing=4, expand=True)], spacing=12,
                   vertical_alignment=ft.CrossAxisAlignment.START), padding=12)))
    return tarjetas
