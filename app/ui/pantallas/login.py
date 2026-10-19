"""Pantalla: login."""
import flet as ft

from app import datos as db
from app.datos import ReglaError
from app.ui.componentes import boton, campo, marca


ACCESOS = [  # cuentas de demostración (contraseña 1234)
    ("Usuario", ft.Icons.PERSON, "usuario@unsa.edu.pe"),
    ("Otro usuario", ft.Icons.PERSON_OUTLINE, "otro@unsa.edu.pe"),
    ("Funcionario", ft.Icons.BADGE, "funcionario@unsa.edu.pe"),
    ("Admin", ft.Icons.ADMIN_PANEL_SETTINGS, "admin@unsa.edu.pe"),
]


def pantalla_login(app) -> ft.Control:
    nombre = campo("Nombre visible", visible=app.modo_registro, max_length=60)
    email = campo("Correo institucional", hint_text=f"usuario{db.DOMINIO}",
                  keyboard_type=ft.KeyboardType.EMAIL)
    clave = campo("Contraseña", password=True, can_reveal_password=True)
    error = ft.Text("", color=ft.Colors.ERROR, size=16)

    def enviar(_=None):
        try:
            if app.modo_registro:
                db.registrar(nombre.value or "", email.value or "", clave.value or "")
            app.user = db.iniciar_sesion(email.value or "", clave.value or "")
            app.tab, app.vista = 0, None
            app.render()
        except ReglaError as e:
            error.value = str(e)
            app.page.update()

    def alternar(_):
        app.modo_registro = not app.modo_registro
        app.render()

    def rapido(correo):
        email.value, clave.value = correo, "1234"
        enviar()

    clave.on_submit = enviar
    texto_boton = "Crear cuenta" if app.modo_registro else "Ingresar"
    return ft.Column([
        ft.Container(marca(grande=True), alignment=ft.Alignment.CENTER),
        ft.Text("Devuelve objetos perdidos del campus mediante un punto oficial de custodia.",
                size=16, text_align=ft.TextAlign.CENTER, color=ft.Colors.ON_SURFACE_VARIANT),
        ft.Card(ft.Container(ft.Column([
            ft.Text("Crear cuenta" if app.modo_registro else "Iniciar sesión", size=20, weight="bold"),
            nombre, email, clave, error,
            ft.Row([boton(texto_boton, enviar)]),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH), padding=20)),
        ft.TextButton("Ya tengo cuenta" if app.modo_registro else "No tengo cuenta: registrarme",
                      on_click=alternar),
        ft.Container(ft.Column([
            ft.Text("Acceso rápido de demostración", weight="bold", size=14),
            ft.Row([ft.Chip(label=ft.Text(etiqueta), leading=ft.Icon(icono),
                            on_click=lambda _, c=correo: rapido(c))
                    for etiqueta, icono, correo in ACCESOS], wrap=True, spacing=8, run_spacing=8)], spacing=8),
            padding=12, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=8,
            visible=not app.modo_registro),
    ], spacing=16, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
