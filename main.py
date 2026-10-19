"""Encontrado UNSA — interfaz en Flet (un solo código para escritorio, web, Android e iOS)."""
from datetime import datetime

import flet as ft

import db
from db import ReglaError

ESTADOS = {  # texto + color + icono: nunca solo color
    "PENDIENTE_RECEPCION": ("Pendiente de recepción", ft.Colors.ORANGE_700, ft.Icons.HOURGLASS_TOP),
    "EN_CUSTODIA": ("En custodia", ft.Colors.GREEN_700, ft.Icons.VERIFIED_USER),
    "ENTREGADO": ("Entregado", ft.Colors.GREY_700, ft.Icons.CHECK_CIRCLE),
    "RECHAZADO": ("Rechazado", ft.Colors.RED_700, ft.Icons.CANCEL),
    "ARCHIVADO": ("Archivado", ft.Colors.GREY_600, ft.Icons.INVENTORY_2),
    "activo": ("Activo", ft.Colors.GREEN_700, ft.Icons.PENDING),
    "entregado": ("Entregado", ft.Colors.GREY_700, ft.Icons.CHECK_CIRCLE),
    "rechazado": ("Rechazado", ft.Colors.RED_700, ft.Icons.CANCEL),
    "vencido": ("Vencido", ft.Colors.ORANGE_700, ft.Icons.TIMER_OFF),
    "cancelado": ("Cancelado", ft.Colors.GREY_600, ft.Icons.BLOCK),
}
ANCHO_MAX = 600


def chip_estado(estado: str) -> ft.Control:
    texto, color, icono = ESTADOS[estado]
    return ft.Container(
        content=ft.Row([ft.Icon(icono, size=16, color=color), ft.Text(texto, size=14, color=color, weight="bold")],
                       spacing=4, tight=True),
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border=ft.Border.all(1, color), border_radius=16,
    )


def tiempo_restante(vence_en: str) -> str:
    resto = datetime.fromisoformat(vence_en) - datetime.now()
    if resto.total_seconds() <= 0:
        return "vencido"
    horas, resto_s = divmod(int(resto.total_seconds()), 3600)
    return f"{horas} h {resto_s // 60} min restantes"


class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.user: dict | None = None
        self.tab = 0
        self.vista: tuple | None = None  # pantalla secundaria, p. ej. ("detalle", objeto)
        self.modo_registro = False
        self.filtro = {"categoria": "", "punto": "", "texto": ""}
        page.title = "Encontrado UNSA"
        page.fonts = {"Poppins": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf", "PoppinsBold": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf"}
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO, font_family="Poppins")
        page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO, font_family="Poppins")
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.on_resize = lambda _: self.render()
        self.render()

    # ---------- utilidades ----------
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

    def alternar_tema(self, _=None):
        oscuro = self.page.theme_mode == ft.ThemeMode.DARK
        self.page.theme_mode = ft.ThemeMode.LIGHT if oscuro else ft.ThemeMode.DARK
        self.render()

    def boton_tema(self) -> ft.Control:
        oscuro = self.page.theme_mode == ft.ThemeMode.DARK
        return ft.IconButton(ft.Icons.LIGHT_MODE if oscuro else ft.Icons.DARK_MODE,
                             tooltip="Cambiar a modo claro" if oscuro else "Cambiar a modo oscuro",
                             on_click=self.alternar_tema)

    def caja_aviso(self, *textos: ft.Text) -> ft.Control:
        """Aviso ámbar con texto oscuro fijo: legible en modo claro y oscuro."""
        for t in textos:
            t.color = ft.Colors.BROWN_900
        return ft.Container(ft.Column(list(textos), spacing=4), padding=10,
                            bgcolor=ft.Colors.AMBER_200, border_radius=8)

    def marca(self, grande: bool = False) -> ft.Control:
        """Logotipo: icono en cuadro redondeado + «Encontrado» + etiqueta UNSA."""
        k = 1.8 if grande else 1
        return ft.Row([
            ft.Container(ft.Icon(ft.Icons.TRAVEL_EXPLORE, color=ft.Colors.WHITE, size=22 * k),
                         bgcolor=ft.Colors.INDIGO, border_radius=10 * k, padding=6 * k),
            ft.Text("Encontrado", size=22 * k, font_family="PoppinsBold", weight=ft.FontWeight.W_400),
            ft.Container(ft.Text("UNSA", size=12 * k, color=ft.Colors.WHITE, font_family="PoppinsBold",
                                 weight=ft.FontWeight.W_400),
                         bgcolor=ft.Colors.INDIGO, border_radius=6 * k,
                         padding=ft.Padding.symmetric(horizontal=6 * k, vertical=2 * k)),
        ], spacing=6 * k, tight=True, vertical_alignment="center")

    def campo(self, etiqueta, **kw) -> ft.TextField:
        return ft.TextField(label=etiqueta, **kw)

    def boton(self, texto, on_click, icono=None, tonal=False, ancho_total=True) -> ft.Control:
        cls = ft.FilledTonalButton if tonal else ft.FilledButton
        return cls(texto, icon=icono, on_click=on_click, height=48, expand=ancho_total)

    def ir(self, tab: int | None = None, vista: tuple | None = None):
        if tab is not None:
            self.tab = tab
        self.vista = vista
        self.render()

    def titulo(self, texto, sub=None) -> ft.Control:
        col = [ft.Text(texto, size=22, weight="bold")]
        if sub:
            col.append(ft.Text(sub, size=16, color=ft.Colors.ON_SURFACE_VARIANT))
        return ft.Column(col, spacing=2)

    def vacio(self, texto, icono=ft.Icons.INBOX) -> ft.Control:
        return ft.Container(
            ft.Column([ft.Icon(icono, size=48, color=ft.Colors.OUTLINE), ft.Text(texto, size=16, text_align="center")],
                      horizontal_alignment="center"),
            padding=32, alignment=ft.Alignment.CENTER)

    # ---------- estructura general ----------
    def render(self):
        p = self.page
        p.controls.clear()
        p.appbar = None
        p.navigation_bar = None
        if not self.user:
            cuerpo = self.pantalla_login()
        else:
            if self.user["rol"] == "usuario":
                etiquetas = [("Catálogo", ft.Icons.SEARCH), ("Publicar", ft.Icons.ADD_CIRCLE),
                             ("Mis reclamos", ft.Icons.CONFIRMATION_NUMBER), ("Perfil", ft.Icons.PERSON)]
            else:
                etiquetas = [("Recepción", ft.Icons.MOVE_TO_INBOX), ("Entrega", ft.Icons.HANDSHAKE),
                             ("Bitácora", ft.Icons.RECEIPT_LONG)]
                if self.user["rol"] == "admin":
                    etiquetas.append(("Admin", ft.Icons.ADMIN_PANEL_SETTINGS))
            self.tab = min(self.tab, len(etiquetas) - 1)
            p.appbar = ft.AppBar(
                title=self.marca(), center_title=False,
                actions=[ft.PopupMenuButton(tooltip="Ajustes", items=[
                    ft.PopupMenuItem(content=self.user["nombre"], disabled=True),
                    ft.PopupMenuItem(icon=ft.Icons.BRIGHTNESS_6, content="Cambiar tema claro/oscuro",
                                     on_click=self.alternar_tema),
                    ft.PopupMenuItem(icon=ft.Icons.LOGOUT, content="Cerrar sesión",
                                     on_click=lambda _: self.cerrar_sesion())])])
            p.navigation_bar = ft.NavigationBar(
                selected_index=self.tab,
                destinations=[ft.NavigationBarDestination(icon=i, label=t) for t, i in etiquetas],
                on_change=lambda e: self.ir(tab=e.control.selected_index))
            nombre = etiquetas[self.tab][0]
            cuerpo = self.vista_secundaria() if self.vista else {
                "Catálogo": self.pantalla_catalogo, "Publicar": self.pantalla_publicar,
                "Mis reclamos": self.pantalla_mis_reclamos, "Perfil": self.pantalla_perfil,
                "Recepción": self.pantalla_recepcion, "Entrega": self.pantalla_entrega,
                "Bitácora": self.pantalla_bitacora, "Admin": self.pantalla_admin}[nombre]()
        ancho = min(ANCHO_MAX, p.width or ANCHO_MAX)
        p.add(ft.SafeArea(expand=True, content=ft.Row(
            [ft.Container(cuerpo, width=ancho, padding=16)], alignment="center", vertical_alignment="start",
            scroll=ft.ScrollMode.AUTO, expand=True)))
        p.update()

    def cerrar_sesion(self):
        self.user, self.tab, self.vista = None, 0, None
        self.render()

    def vista_secundaria(self) -> ft.Control:
        nombre, dato = self.vista
        if nombre == "detalle":
            return self.pantalla_detalle(dato)
        return self.pantalla_reclamar(dato)

    def atras(self, texto="Volver"):
        return ft.TextButton(texto, icon=ft.Icons.ARROW_BACK, on_click=lambda _: self.ir(vista=None))

    # ---------- 1. Inicio de sesión y registro ----------
    def pantalla_login(self) -> ft.Control:
        nombre = self.campo("Nombre visible", visible=self.modo_registro, max_length=60)
        email = self.campo("Correo institucional", hint_text=f"usuario{db.DOMINIO}",
                           keyboard_type=ft.KeyboardType.EMAIL)
        clave = self.campo("Contraseña", password=True, can_reveal_password=True)
        error = ft.Text("", color=ft.Colors.RED_700, size=16)

        def enviar(_=None):
            try:
                if self.modo_registro:
                    db.registrar(nombre.value or "", email.value or "", clave.value or "")
                self.user = db.iniciar_sesion(email.value or "", clave.value or "")
                self.tab, self.vista = 0, None
                self.render()
            except ReglaError as e:
                error.value = str(e)
                self.page.update()

        def alternar(_):
            self.modo_registro = not self.modo_registro
            self.render()

        clave.on_submit = enviar
        return ft.Column([
            ft.Row([self.boton_tema()], alignment="end"),
            ft.Container(self.marca(grande=True), alignment=ft.Alignment.CENTER, padding=ft.Padding.only(top=8)),
            ft.Text("Devuelve objetos perdidos del campus mediante un punto oficial de custodia.", size=16),
            nombre, email, clave, error,
            ft.Row([self.boton("Crear cuenta" if self.modo_registro else "Ingresar", enviar)]),
            ft.TextButton("Ya tengo cuenta" if self.modo_registro else "No tengo cuenta: registrarme",
                          on_click=alternar),
            ft.Container(ft.Column([
                ft.Text("Cuentas de demostración (contraseña 1234)", weight="bold", size=14),
                ft.Text("usuario@ · otro@ · funcionario@ · admin@  +  unsa.edu.pe", size=14)]),
                padding=12, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=8),
        ], spacing=12)

    # ---------- 3. Catálogo ----------
    def pantalla_catalogo(self) -> ft.Control:
        lista = ft.Column(spacing=8)
        puntos = db.puntos_activos()

        def cargar(_=None):
            f = self.filtro
            items = db.catalogo(f["categoria"] or None, f["punto"] or None, f["texto"])
            lista.controls = [self.tarjeta_objeto(o) for o in items] or [
                self.vacio("No hay objetos en custodia con esos filtros.", ft.Icons.SEARCH_OFF)]
            self.page.update()

        def cambiar(clave):
            def h(e):
                self.filtro[clave] = e.control.value or ""
                cargar()
            return h

        buscar = self.campo("Buscar en la descripción", prefix_icon=ft.Icons.SEARCH, value=self.filtro["texto"])
        buscar.on_change = cambiar("texto")
        cat = ft.Dropdown(label="Categoría", value=self.filtro["categoria"], expand=True,
                          options=[ft.DropdownOption(key="", text="Todas")] +
                                  [ft.DropdownOption(key=c, text=c) for c in db.CATEGORIAS],
                          on_select=cambiar("categoria"))
        pto = ft.Dropdown(label="Punto de custodia", value=self.filtro["punto"], expand=True,
                          options=[ft.DropdownOption(key="", text="Todos")] +
                                  [ft.DropdownOption(key=str(x["id"]), text=x["nombre"]) for x in puntos],
                          on_select=cambiar("punto"))
        cargar_inicial = ft.Column([self.titulo("Objetos en custodia", "Hallados y guardados en un punto oficial"),
                                    buscar, ft.Row([cat, pto]), lista], spacing=12)
        f = self.filtro
        items = db.catalogo(f["categoria"] or None, f["punto"] or None, f["texto"])
        lista.controls = [self.tarjeta_objeto(o) for o in items] or [
            self.vacio("No hay objetos en custodia con esos filtros.", ft.Icons.SEARCH_OFF)]
        return cargar_inicial

    def tarjeta_objeto(self, o: dict) -> ft.Control:
        return ft.Card(ft.Container(
            ft.Column([
                ft.Row([ft.Icon(ft.Icons.INVENTORY_2_OUTLINED), ft.Text(o["categoria"], weight="bold", size=16)]),
                ft.Text(o["descripcion_publica"], size=16),
                ft.Text(f"{o['lugar_hallazgo']} · {o['fecha_hallazgo'][:16]}", size=14,
                        color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(f"Custodia: {o['punto']}", size=14, color=ft.Colors.ON_SURFACE_VARIANT),
            ], spacing=4),
            padding=14, ink=True, on_click=lambda _: self.ir(vista=("detalle", o))))

    # ---------- 4. Detalle ----------
    def pantalla_detalle(self, o: dict) -> ft.Control:
        propio = o["publicado_por"] == self.user["id"]
        accion = (ft.Text("Tú publicaste este objeto: no puedes reclamarlo.", size=16, italic=True)
                  if propio else self.boton("Es mío", lambda _: self.ir(vista=("reclamar", o)),
                                            ft.Icons.BACK_HAND))
        return ft.Column([
            self.atras("Catálogo"),
            self.titulo(o["categoria"]),
            chip_estado("EN_CUSTODIA"),
            ft.Text(o["descripcion_publica"], size=18),
            ft.Divider(),
            ft.ListTile(leading=ft.Icon(ft.Icons.PLACE), title=ft.Text("Dónde se encontró"),
                        subtitle=ft.Text(o["lugar_hallazgo"])),
            ft.ListTile(leading=ft.Icon(ft.Icons.SCHEDULE), title=ft.Text("Cuándo"),
                        subtitle=ft.Text(o["fecha_hallazgo"][:16])),
            ft.ListTile(leading=ft.Icon(ft.Icons.STORE), title=ft.Text(f"Retiro en: {o['punto']}"),
                        subtitle=ft.Text(f"{o['ubicacion']} · {o['horario']}")),
            ft.Row([accion]),
        ], spacing=8)

    # ---------- 7. Reclamar ----------
    def pantalla_reclamar(self, o: dict) -> ft.Control:
        desc = self.campo("Describe el objeto con tus palabras", multiline=True, min_lines=4,
                          hint_text=f"Mínimo {db.MIN_DESC_RECLAMO} caracteres: color, marca, contenido…")

        def enviar(_):
            def accion():
                db.crear_reclamo(self.user["id"], o["id"], desc.value or "")
            self.hacer(accion, "Reclamo creado. Presenta tu código en el punto de custodia.",
                       lambda: self.ir(tab=2, vista=None))

        return ft.Column([
            self.atras(), self.titulo("Reclamar objeto", o["descripcion_publica"]),
            ft.Text("El funcionario comparará tu descripción con un detalle que solo el dueño conoce y verificará "
                    "tu identidad en persona. El código dura 48 horas.", size=16),
            desc, ft.Row([self.boton("Generar código", enviar, ft.Icons.KEY)]),
        ], spacing=12)

    # ---------- 5 y 6. Publicar y mis publicaciones ----------
    def pantalla_publicar(self) -> ft.Control:
        puntos = db.puntos_activos()
        cat = ft.Dropdown(label="Categoría",
                          options=[ft.DropdownOption(key=c, text=c) for c in db.CATEGORIAS])
        desc = self.campo("Descripción pública", multiline=True, min_lines=3, max_length=280,
                          helper="No incluyas datos que solo el dueño sabría.")
        lugar = self.campo("Lugar donde lo encontraste")
        fecha = self.campo("Fecha y hora aproximadas", value=datetime.now().strftime("%Y-%m-%d %H:%M"))
        punto = ft.Dropdown(label="Punto de entrega",
                            options=[ft.DropdownOption(key=str(x["id"]), text=x["nombre"]) for x in puntos])
        aviso_doc = ft.Text("", size=14, color=ft.Colors.ORANGE_500)

        def al_cambiar_cat(_):
            if cat.value == "Documentos y tarjetas":
                aviso_doc.value = ("En documentos y tarjetas no se publica foto, y la descripción no debe "
                                   "incluir nombres ni números (RN-08).")
            else:
                aviso_doc.value = ""
            self.page.update()
        cat.on_select = al_cambiar_cat

        def enviar(_):
            def accion():
                db.publicar(self.user["id"], cat.value or "", desc.value or "", lugar.value or "",
                            fecha.value or "", int(punto.value) if punto.value else None)
            self.hacer(accion, "Publicado. Déjalo en el punto de entrega para que el funcionario lo confirme.",
                       lambda: self.ir(tab=3))

        return ft.Column([
            self.titulo("Publicar un hallazgo", "Después déjalo físicamente en el punto elegido"),
            self.caja_aviso(ft.Text("No publiques dinero, armas, medicamentos ni sustancias: entrégalos "
                                    "directamente al funcionario (RN-09).", size=14)),
            cat, aviso_doc, desc, lugar, fecha, punto,
            ft.Row([self.boton("Publicar", enviar, ft.Icons.PUBLISH)]),
        ], spacing=12)

    def lista_mis_publicaciones(self) -> list[ft.Control]:
        items = db.mis_publicaciones(self.user["id"])
        if not items:
            return [self.vacio("Aún no publicaste nada.")]
        tarjetas = []
        for o in items:
            fila = [ft.Row([ft.Text(o["categoria"], weight="bold", size=16), chip_estado(o["estado"])],
                           alignment="spaceBetween", wrap=True),
                    ft.Text(o["descripcion_publica"], size=16)]
            if o["estado"] == "RECHAZADO":
                fila.append(ft.Text(f"Motivo: {o['motivo']}", size=14, color=ft.Colors.ERROR))
            if o["estado"] == "PENDIENTE_RECEPCION":
                fila.append(ft.OutlinedButton("Cancelar publicación", icon=ft.Icons.CLOSE, on_click=(
                    lambda _, oid=o["id"]: self.hacer(lambda: db.cancelar_publicacion(self.user["id"], oid),
                                                      "Publicación cancelada.", self.render))))
            tarjetas.append(ft.Card(ft.Container(ft.Column(fila, spacing=6), padding=14)))
        return tarjetas

    # ---------- 8. Mis reclamos ----------
    def pantalla_mis_reclamos(self) -> ft.Control:
        items = db.mis_reclamos(self.user["id"])
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
                        lambda _, rid=r["id"]: self.hacer(lambda: db.cancelar_reclamo(self.user["id"], rid),
                                                          "Reclamo cancelado.", self.render)))]
            elif r["estado"] == "vencido":
                fila.append(ft.Text("El código venció. Puedes reclamar de nuevo desde el catálogo.", size=14))
            elif r["estado"] == "rechazado":
                fila.append(ft.Text(f"Motivo: {r['motivo']}", size=14, color=ft.Colors.ERROR))
            tarjetas.append(ft.Card(ft.Container(ft.Column(fila, spacing=8), padding=14)))
        return ft.Column([
            self.titulo("Mis reclamos", f"Máximo {db.MAX_RECLAMOS_ACTIVOS} activos a la vez"),
            *(tarjetas or [self.vacio("No tienes reclamos. Busca tu objeto en el catálogo.",
                                       ft.Icons.CONFIRMATION_NUMBER)])], spacing=12)

    # ---------- 13. Perfil ----------
    def pantalla_perfil(self) -> ft.Control:
        return ft.Column([
            self.titulo(self.user["nombre"], self.user["email"]),
            ft.Switch(label="Modo oscuro", value=self.page.theme_mode == ft.ThemeMode.DARK,
                      on_change=self.alternar_tema),
            ft.Row([self.boton("Cerrar sesión", lambda _: self.cerrar_sesion(), ft.Icons.LOGOUT, tonal=True)]),
            ft.ExpansionTile(title=ft.Text("Reglas de uso y privacidad"), controls=[ft.Container(ft.Text(
                "• Solo se guardan correo, nombre, publicaciones, reclamos y bitácora.\n"
                "• No se guardan DNI ni fotos de documentos.\n"
                "• Quien publica un objeto no puede reclamarlo.\n"
                "• La app ordena el proceso; la identidad la verifica el funcionario en persona.", size=14),
                padding=12)]),
            ft.Divider(),
            self.titulo("Mis publicaciones"),
            *self.lista_mis_publicaciones(),
        ], spacing=12)

    # ---------- 9. Recepción ----------
    def pantalla_recepcion(self) -> ft.Control:
        items = db.pendientes()
        tarjetas = []
        for o in items:
            detalle = self.campo("Detalle oculto de verificación (obligatorio)",
                                 hint_text="Marca, rayón, fondo de pantalla…")
            notas = self.campo("Notas internas (opcional)")
            motivo = self.campo("Motivo del rechazo", hint_text="No llegó el objeto, duplicado, contenido indebido")
            tarjetas.append(ft.Card(ft.Container(ft.Column([
                ft.Row([ft.Text(o["categoria"], weight="bold", size=16), chip_estado(o["estado"])],
                       alignment="spaceBetween", wrap=True),
                ft.Text(o["descripcion_publica"], size=16),
                ft.Text(f"{o['lugar_hallazgo']} · {o['fecha_hallazgo'][:16]} · Punto: {o['punto']}", size=14),
                detalle, notas,
                ft.Row([self.boton("Confirmar recepción", (
                    lambda _, oid=o["id"], d=detalle, n=notas: self.hacer(
                        lambda: db.confirmar_recepcion(self.user["id"], oid, d.value or "", n.value or ""),
                        "Recepción confirmada: el objeto ya es visible.", self.render)), ft.Icons.CHECK)]),
                motivo,
                ft.Row([ft.OutlinedButton("Rechazar", icon=ft.Icons.CLOSE, height=48, expand=True, on_click=(
                    lambda _, oid=o["id"], m=motivo: self.hacer(
                        lambda: db.rechazar_publicacion(self.user["id"], oid, m.value or ""),
                        "Publicación rechazada.", self.render)))]),
            ], spacing=8), padding=14)))
        return ft.Column([self.titulo("Recepción", "Publicaciones pendientes de confirmar"),
                          *(tarjetas or [self.vacio("No hay publicaciones pendientes.")])], spacing=12)

    # ---------- 10. Entrega ----------
    def pantalla_entrega(self) -> ft.Control:
        codigo = self.campo("Código de reclamo", capitalization=ft.TextCapitalization.CHARACTERS, max_length=6)
        resultado = ft.Column(spacing=8)

        def buscar(_=None):
            resultado.controls.clear()
            try:
                r = db.buscar_codigo(self.user["id"], codigo.value or "")
            except ReglaError as e:
                resultado.controls.append(ft.Container(ft.Text(str(e), size=16, color=ft.Colors.ERROR),
                                                       padding=10))
                self.page.update()
                return
            verificado = ft.Checkbox(label="Verifiqué el carné o DNI de la persona")
            motivo = self.campo("Motivo (solo si rechazas)")
            resultado.controls = [ft.Card(ft.Container(ft.Column([
                ft.Text(f"{r['categoria']} · {r['punto']}", weight="bold", size=16),
                ft.Text(r["descripcion_publica"], size=16),
                ft.Divider(),
                ft.Text(f"Reclamante: {r['reclamante']} ({r['reclamante_email']})", size=14),
                ft.Text("Según el reclamante:", size=14, weight="bold"),
                ft.Text(r["descripcion"], size=16),
                self.caja_aviso(ft.Text("Detalle oculto (solo funcionario)", size=14, weight="bold"),
                                ft.Text(r["detalle_oculto"] or "—", size=16)),
                verificado,
                ft.Row([self.boton("Entregar", (lambda _: self.hacer(
                    lambda: db.entregar(self.user["id"], r["id"], bool(verificado.value)),
                    "Entrega registrada en la bitácora.", self.render)), ft.Icons.HANDSHAKE)]),
                motivo,
                ft.Row([ft.OutlinedButton("Rechazar reclamo", icon=ft.Icons.CLOSE, height=48, expand=True,
                                          on_click=lambda _: self.hacer(
                                              lambda: db.rechazar_reclamo(self.user["id"], r["id"],
                                                                          motivo.value or ""),
                                              "Reclamo rechazado.", self.render))]),
            ], spacing=8), padding=14))]
            self.page.update()

        codigo.on_submit = buscar
        return ft.Column([self.titulo("Entrega", "Valida el código y verifica la identidad"), codigo,
                          ft.Row([self.boton("Validar código", buscar, ft.Icons.SEARCH)]), resultado], spacing=12)

    # ---------- 11. Bitácora ----------
    def pantalla_bitacora(self) -> ft.Control:
        lista = ft.Column(spacing=6)

        def cargar(texto=""):
            filas = db.bitacora(self.user["id"], texto.strip())
            lista.controls = [ft.ListTile(
                leading=ft.Icon(ft.Icons.HISTORY),
                title=ft.Text(f"{a['accion']}  ({a['estado_anterior'] or '—'} → {a['estado_nuevo'] or '—'})", size=15),
                subtitle=ft.Text(f"{a['creado_en']} · {a['actor'] or 'sistema'}"
                                 + (f" · {a['detalle']}" if a["detalle"] else ""), size=13)) for a in filas
            ] or [self.vacio("Sin registros.", ft.Icons.RECEIPT_LONG)]

        filtro = self.campo("Filtrar por acción (ej. entregado)", prefix_icon=ft.Icons.FILTER_ALT)

        def al_filtrar(e):
            cargar(e.control.value or "")
            self.page.update()
        filtro.on_change = al_filtrar
        cargar()
        return ft.Column([self.titulo("Bitácora de auditoría", "Registro inmutable de cada cambio"),
                          filtro, lista], spacing=12)

    # ---------- 12. Administración ----------
    def pantalla_admin(self) -> ft.Control:
        filas = []
        for u in db.usuarios(self.user["id"]):
            propio = u["id"] == self.user["id"]
            rol = ft.Dropdown(value=u["rol"], disabled=propio, width=170,
                              options=[ft.DropdownOption(key=r, text=r) for r in ("usuario", "funcionario", "admin")],
                              on_select=lambda e, uid=u["id"]: self.confirmar_rol(uid, e.control.value))
            filas.append(ft.Card(ft.Container(ft.Column([
                ft.Text(f"{u['nombre']}  ·  {u['email']}", size=15),
                ft.Row([rol, ft.Switch(label="Bloqueado", value=bool(u["bloqueado"]), disabled=propio,
                                       on_change=lambda e, uid=u["id"]: self.hacer(
                                           lambda: db.bloquear(self.user["id"], uid, bool(e.control.value)),
                                           "Estado de bloqueo actualizado.", self.render))],
                       wrap=True, alignment="spaceBetween"),
            ], spacing=6), padding=12)))
        return ft.Column([self.titulo("Administración", "Roles y bloqueos"), *filas], spacing=12)

    def confirmar_rol(self, uid: int, rol: str):
        def aplicar(_):
            self.page.pop_dialog()
            self.hacer(lambda: db.cambiar_rol(self.user["id"], uid, rol), "Rol actualizado.", self.render)

        def cancelar(_):
            self.page.pop_dialog()
            self.render()
        self.page.show_dialog(ft.AlertDialog(
            title=ft.Text("Confirmar cambio de rol"),
            content=ft.Text(f"¿Asignar el rol «{rol}» a este usuario? Queda registrado en la bitácora."),
            actions=[ft.TextButton("Cancelar", on_click=cancelar), ft.FilledButton("Confirmar", on_click=aplicar)]))


def main(page: ft.Page):
    db.iniciar()
    App(page)


if __name__ == "__main__":
    ft.run(main)
