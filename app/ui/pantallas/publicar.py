"""Pantalla: publicar un hallazgo."""
from datetime import datetime, time, timedelta
from urllib.parse import quote

import flet as ft

from app import datos as db
from app.datos import ReglaError
from app.ui.componentes import abrir_selector_punto, boton, caja_aviso, campo, campo_selector, titulo
from app.ui.tema import CATEGORIA_ICONOS

MOMENTOS = {"manana": ("Mañana", 9), "tarde": ("Tarde", 15), "noche": ("Noche", 20)}


def pantalla_publicar(app) -> ft.Control:
    puntos = db.puntos_activos()
    est = {"cat": "", "punto": puntos[0]["id"] if puntos else None, "dia": "hoy", "fecha": None,
           "momento": "tarde"}

    # --- categoría: chips con ícono ---
    chips_cat = ft.Row(wrap=True, spacing=8, run_spacing=8)
    aviso_doc = ft.Text("", size=14, color=ft.Colors.ORANGE_500)

    def pintar_categorias():
        chips_cat.controls = [
            ft.Chip(label=ft.Text(c), leading=ft.Icon(CATEGORIA_ICONOS[c]), selected=est["cat"] == c,
                    on_click=lambda _, c=c: elegir_categoria(c)) for c in db.CATEGORIAS]

    def elegir_categoria(c):
        est["cat"] = c
        es_doc = c == "Documentos y tarjetas"
        aviso_doc.value = ("En documentos y tarjetas no se publica foto, y la descripción no debe incluir "
                           "nombres ni números." if es_doc else "")
        seccion_foto.visible = not es_doc
        pintar_categorias()
        app.page.update()

    # --- foto por enlace (no se guarda ningún archivo) ---
    url = campo("Enlace de la foto (opcional)", hint_text="https://…", prefix_icon=ft.Icons.LINK,
                helper="No guardamos imágenes: solo el enlace a una foto que ya esté en internet.")
    vista_previa = ft.Image(src="https://placehold.co/1x1.png", height=140, fit=ft.BoxFit.COVER, border_radius=12,
                            visible=False, error_content=ft.Text("No se pudo cargar esa imagen.", size=14))

    def al_escribir_url(_):
        v = (url.value or "").strip()
        vista_previa.visible = v.lower().startswith(("http://", "https://"))
        if vista_previa.visible:
            vista_previa.src = v
        app.page.update()
    url.on_change = al_escribir_url

    def usar_ejemplo(_):
        url.value = f"https://placehold.co/600x400/4f46e5/ffffff/png?text={quote(est['cat'] or 'Objeto')}"
        al_escribir_url(None)
    seccion_foto = ft.Column([url, vista_previa,
                              ft.TextButton("Usar imagen de ejemplo", icon=ft.Icons.IMAGE_OUTLINED,
                                            on_click=usar_ejemplo)], spacing=6)

    # --- descripción y lugar ---
    desc = campo("Descripción pública", multiline=True, min_lines=3, max_length=280,
                 helper="Color, marca, tamaño. No incluyas datos que solo el dueño sabría.")
    lugar = campo("¿Dónde lo encontraste?", hint_text="Ej.: Biblioteca central, aula 204, comedor")

    # --- cuándo: día + momento del día ---
    texto_fecha = ft.Text("", size=14, color=ft.Colors.ON_SURFACE_VARIANT)

    def al_elegir_fecha(e):
        valor = e.control.value
        est["fecha"] = valor.date() if isinstance(valor, datetime) else valor
        texto_fecha.value = f"Día elegido: {est['fecha'].strftime('%d/%m/%Y')}"
        app.page.update()

    def al_elegir_dia(e):
        est["dia"] = list(e.control.selected)[0]
        if est["dia"] == "otro":
            ahora = datetime.now()
            app.page.show_dialog(ft.DatePicker(first_date=ahora - timedelta(days=90), last_date=ahora,
                                               value=est["fecha"] or ahora, on_change=al_elegir_fecha))
        else:
            texto_fecha.value = ""
        app.page.update()

    def al_elegir_momento(e):
        est["momento"] = list(e.control.selected)[0]

    dia = ft.SegmentedButton(
        selected=["hoy"], allow_empty_selection=False, on_change=al_elegir_dia,
        segments=[ft.Segment(value="hoy", label=ft.Text("Hoy")), ft.Segment(value="ayer", label=ft.Text("Ayer")),
                  ft.Segment(value="otro", label=ft.Text("Otro día"), icon=ft.Icon(ft.Icons.CALENDAR_MONTH))])
    momento = ft.SegmentedButton(
        selected=["tarde"], allow_empty_selection=False, on_change=al_elegir_momento,
        segments=[ft.Segment(value=k, label=ft.Text(v[0])) for k, v in MOMENTOS.items()])

    def fecha_hallazgo() -> str:
        hoy = datetime.now().date()
        if est["dia"] == "hoy":
            d = hoy
        elif est["dia"] == "ayer":
            d = hoy - timedelta(days=1)
        elif est["fecha"]:
            d = est["fecha"]
        else:
            raise ReglaError("Elige el día en que lo encontraste.")
        hallazgo = datetime.combine(d, time(MOMENTOS[est["momento"]][1]))
        return min(hallazgo, datetime.now()).strftime("%Y-%m-%d %H:%M")  # nunca en el futuro

    # --- punto de entrega: un solo campo que abre una lista con buscador (sirve con 2 o con 200 puntos) ---
    zona_punto = ft.Column(spacing=6)

    def punto_actual() -> dict | None:
        return next((p for p in puntos if p["id"] == est["punto"]), None)

    def pintar_puntos():
        p = punto_actual()
        zona_punto.controls = [campo_selector(
            ft.Icons.STORE, p["nombre"] if p else "Elige un punto de entrega",
            f"{p['ubicacion']} · {p['horario']}" if p else None, lambda _: abrir_selector())]

    def elegir_punto(pid):
        est["punto"] = pid
        pintar_puntos()
        app.page.update()

    def abrir_selector():
        abrir_selector_punto(app, puntos, est["punto"], elegir_punto)

    pintar_categorias()
    pintar_puntos()

    def enviar(_):
        def accion():
            db.publicar(app.user["id"], est["cat"], desc.value or "", lugar.value or "", fecha_hallazgo(),
                        est["punto"], url.value or "")
        app.hacer(accion, "Publicado. Déjalo en el punto de entrega para que el funcionario lo confirme.",
                  lambda: app.ir(tab=3))

    def seccion(texto):
        return ft.Text(texto, size=16, weight="bold")

    return ft.Column([
        titulo("Publicar un hallazgo", "Después déjalo físicamente en el punto elegido"),
        caja_aviso(ft.Text("No publiques dinero, armas, medicamentos ni sustancias: entrégalos "
                           "directamente al funcionario.", size=14)),
        seccion("1. ¿Qué encontraste?"), chips_cat, aviso_doc, desc, seccion_foto,
        seccion("2. ¿Dónde y cuándo?"), lugar,
        ft.Row([dia], scroll=ft.ScrollMode.AUTO), texto_fecha, ft.Row([momento], scroll=ft.ScrollMode.AUTO),
        seccion("3. ¿Dónde lo dejas?"), zona_punto,
        ft.Row([boton("Publicar", enviar, ft.Icons.PUBLISH)]),
    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
