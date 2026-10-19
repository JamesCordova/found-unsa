"""Pantalla: administración (roles, bloqueos y puntos de entrega)."""
import flet as ft

from app import datos as db
from app.datos import ReglaError
from app.ui.componentes import boton, campo, titulo, vacio


def pantalla_admin(app) -> ft.Control:
    def cambiar_seccion(e):
        app.admin_seccion = list(e.control.selected)[0]
        app.render()

    secciones = ft.Row([ft.SegmentedButton(
        selected=[app.admin_seccion], allow_empty_selection=False, on_change=cambiar_seccion,
        segments=[ft.Segment(value="usuarios", label=ft.Text("Usuarios"), icon=ft.Icon(ft.Icons.GROUP)),
                  ft.Segment(value="puntos", label=ft.Text("Puntos de entrega"), icon=ft.Icon(ft.Icons.STORE))])],
        scroll=ft.ScrollMode.AUTO)
    cuerpo = _seccion_puntos(app) if app.admin_seccion == "puntos" else _seccion_usuarios(app)
    return ft.Column([titulo("Administración", "Roles, bloqueos y puntos de entrega"), secciones, *cuerpo],
                     spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


# ---------- usuarios ----------
def _seccion_usuarios(app) -> list[ft.Control]:
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
    return filas


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


# ---------- puntos de entrega ----------
def _seccion_puntos(app) -> list[ft.Control]:
    puntos = db.puntos_todos(app.user["id"])
    tarjetas = []
    for p in puntos:
        activo = bool(p["activo"])
        tarjetas.append(ft.Card(ft.Container(ft.Column([
            ft.Row([ft.Icon(ft.Icons.STORE if activo else ft.Icons.STORE_MALL_DIRECTORY,
                            color=None if activo else ft.Colors.OUTLINE),
                    ft.Column([ft.Text(p["nombre"], weight="bold", size=16),
                               ft.Text(f"{p['ubicacion']} · {p['horario']}", size=13,
                                       color=ft.Colors.ON_SURFACE_VARIANT),
                               ft.Text(f"{p['en_custodia']} objeto(s) en custodia", size=13)],
                              spacing=2, expand=True),
                    ft.IconButton(ft.Icons.EDIT, tooltip="Editar", on_click=lambda _, p=p: dialogo_punto(app, p))],
                   vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Switch(label="Activo (se ofrece al publicar)", value=activo,
                      on_change=lambda e, pid=p["id"]: _activar(app, pid, bool(e.control.value))),
        ], spacing=4), padding=12), opacity=1 if activo else 0.6))
    return [ft.Row([boton("Nuevo punto de entrega", lambda _: dialogo_punto(app), ft.Icons.ADD_LOCATION_ALT)]),
            *(tarjetas or [vacio("Aún no hay puntos de entrega.", ft.Icons.STORE)])]


def _activar(app, pid: int, activo: bool):
    app.hacer(lambda: db.activar_punto(app.user["id"], pid, activo),
              "Punto activado." if activo else "Punto desactivado.", app.render)


def dialogo_punto(app, punto: dict | None = None):
    """Formulario para crear o editar un punto de entrega."""
    nombre = campo("Nombre", value=punto["nombre"] if punto else "", max_length=60,
                   hint_text="Ej.: Biblioteca central")
    ubicacion = campo("Ubicación (cómo llegar)", value=punto["ubicacion"] if punto else "")
    horario = campo("Horario de atención", value=punto["horario"] if punto else "",
                    hint_text="Ej.: Lun-Vie 8:00-16:00")
    error = ft.Text("", color=ft.Colors.ERROR, size=14)

    def guardar(_):
        try:
            db.guardar_punto(app.user["id"], nombre.value or "", ubicacion.value or "", horario.value or "",
                             punto["id"] if punto else None)
        except ReglaError as e:
            error.value = str(e)
            app.page.update()
            return
        app.page.pop_dialog()
        app.aviso("Punto guardado.")
        app.render()

    app.page.show_dialog(ft.AlertDialog(
        title=ft.Text("Editar punto de entrega" if punto else "Nuevo punto de entrega"),
        content=ft.Container(ft.Column([nombre, ubicacion, horario, error], spacing=12, tight=True), width=420),
        actions=[ft.TextButton("Cancelar", on_click=lambda _: app.page.pop_dialog()),
                 ft.FilledButton("Guardar", on_click=guardar)]))
