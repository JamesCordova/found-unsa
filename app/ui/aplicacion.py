"""Núcleo de la interfaz: sesión, navegación por rol y renderizado."""
import flet as ft

from app import datos as db
from app.datos import ReglaError
from app.ui.componentes import atras, boton_tema, marca
from app.ui.pantallas.admin import pantalla_admin
from app.ui.pantallas.bitacora import pantalla_bitacora
from app.ui.pantallas.catalogo import pantalla_catalogo
from app.ui.pantallas.detalle import pantalla_detalle
from app.ui.pantallas.entrega import pantalla_entrega
from app.ui.pantallas.login import pantalla_login
from app.ui.pantallas.mis_reclamos import pantalla_mis_reclamos
from app.ui.pantallas.perfil import pantalla_perfil
from app.ui.pantallas.publicar import pantalla_publicar
from app.ui.pantallas.recepcion import pantalla_recepcion
from app.ui.pantallas.reclamar import pantalla_reclamar
from app.ui.tema import COLUMNAS_CONTENIDO, COLUMNAS_LOGIN, aplicar_tema

# Pestañas de la barra inferior según el rol: (etiqueta, icono, pantalla)
PESTANIAS_USUARIO = [
    ("Catálogo", ft.Icons.SEARCH, pantalla_catalogo),
    ("Publicar", ft.Icons.ADD_CIRCLE, pantalla_publicar),
    ("Mis reclamos", ft.Icons.CONFIRMATION_NUMBER, pantalla_mis_reclamos),
    ("Perfil", ft.Icons.PERSON, pantalla_perfil),
]
PESTANIAS_STAFF = [
    ("Recepción", ft.Icons.MOVE_TO_INBOX, pantalla_recepcion),
    ("Entrega", ft.Icons.HANDSHAKE, pantalla_entrega),
    ("Bitácora", ft.Icons.RECEIPT_LONG, pantalla_bitacora),
]
PESTANIA_ADMIN = ("Admin", ft.Icons.ADMIN_PANEL_SETTINGS, pantalla_admin)
VISTAS_SECUNDARIAS = {"detalle": pantalla_detalle, "reclamar": pantalla_reclamar}


class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.user: dict | None = None
        self.tab = 0
        self.vista: tuple | None = None  # pantalla secundaria, p. ej. ("detalle", objeto)
        self.modo_registro = False
        self.filtro = {"categoria": "", "punto": "", "texto": ""}
        aplicar_tema(page)
        page.on_resize = lambda _: self.render()
        self.render()

    # ---------- utilidades usadas por las pantallas ----------
    def aviso(self, texto: str, error: bool = False):
        self.page.show_dialog(ft.SnackBar(ft.Text(texto, size=16),
                                          bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_800))

    def hacer(self, accion, ok: str | None = None, despues=None):
        """Ejecuta una acción de negocio y muestra el error de regla si lo hay."""
        try:
            accion()
        except ReglaError as e:
            self.aviso(str(e), error=True)
            return
        if ok:
            self.aviso(ok)
        if despues:
            despues()

    def confirmar(self, titulo: str, texto: str, accion, etiqueta: str = "Confirmar"):
        """Diálogo de confirmación para acciones que no se pueden deshacer."""
        def si(_):
            self.page.pop_dialog()
            accion()
        self.page.show_dialog(ft.AlertDialog(
            title=ft.Text(titulo), content=ft.Text(texto, size=16),
            actions=[ft.TextButton("Volver", on_click=lambda _: self.page.pop_dialog()),
                     ft.FilledButton(etiqueta, on_click=si)]))

    def alternar_tema(self, _=None):
        oscuro = self.page.theme_mode == ft.ThemeMode.DARK
        self.page.theme_mode = ft.ThemeMode.LIGHT if oscuro else ft.ThemeMode.DARK
        self.render()

    def ir(self, tab: int | None = None, vista: tuple | None = None):
        if tab is not None:
            self.tab = tab
        self.vista = vista
        self.render()

    def cerrar_sesion(self):
        self.user, self.tab, self.vista = None, 0, None
        self.render()

    # ---------- renderizado ----------
    def pestanias(self) -> list:
        if self.user["rol"] == "usuario":
            return PESTANIAS_USUARIO
        return PESTANIAS_STAFF + ([PESTANIA_ADMIN] if self.user["rol"] == "admin" else [])

    def render(self):
        p = self.page
        p.controls.clear()
        p.appbar = None
        p.navigation_bar = None
        if not self.user:
            p.appbar = ft.AppBar(actions=[boton_tema(self)], bgcolor=ft.Colors.TRANSPARENT)
            p.add(ft.SafeArea(expand=True, content=ft.Column(
                [ft.ResponsiveRow(
                    [ft.Container(pantalla_login(self), padding=16, col=COLUMNAS_LOGIN)],
                    alignment=ft.MainAxisAlignment.CENTER)],
                alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                scroll=ft.ScrollMode.AUTO, expand=True)))
            p.update()
            return
        pestanias = self.pestanias()
        self.tab = min(self.tab, len(pestanias) - 1)
        p.appbar = ft.AppBar(
            title=marca(), center_title=False,
            actions=[ft.PopupMenuButton(tooltip="Ajustes", items=[
                ft.PopupMenuItem(content=self.user["nombre"], disabled=True),
                ft.PopupMenuItem(icon=ft.Icons.BRIGHTNESS_6, content="Cambiar tema claro/oscuro",
                                 on_click=self.alternar_tema),
                ft.PopupMenuItem(icon=ft.Icons.LOGOUT, content="Cerrar sesión",
                                 on_click=lambda _: self.cerrar_sesion())])])
        pendientes = len(db.pendientes()) if self.user["rol"] != "usuario" else 0
        p.navigation_bar = ft.NavigationBar(
            selected_index=self.tab,
            destinations=[ft.NavigationBarDestination(
                icon=ft.Icon(i, badge=ft.Badge(label=str(pendientes)) if t == "Recepción" and pendientes else None),
                label=t) for t, i, _ in pestanias],
            on_change=lambda e: self.ir(tab=e.control.selected_index))
        if self.vista:
            nombre, dato = self.vista
            cuerpo = VISTAS_SECUNDARIAS[nombre](self, dato)
        else:
            cuerpo = pestanias[self.tab][2](self)
        p.add(ft.SafeArea(expand=True, content=ft.Column(
            [ft.ResponsiveRow(
                [ft.Container(cuerpo, padding=16, col=COLUMNAS_CONTENIDO)],
                alignment=ft.MainAxisAlignment.CENTER)],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH, scroll=ft.ScrollMode.AUTO, expand=True)))
        p.update()
