"""Pantalla: entrega (funcionario)."""
import flet as ft

from app import datos as db
from app.datos import ReglaError
from app.ui.componentes import boton, caja_aviso, campo, imagen_objeto, titulo


def pantalla_entrega(app) -> ft.Control:
    codigo = campo("Código de reclamo", capitalization=ft.TextCapitalization.CHARACTERS, max_length=6,
                   hint_text="Ej.: K7MQ4X", prefix_icon=ft.Icons.KEY)
    resultado = ft.Column(spacing=8)

    def buscar(_=None):
        resultado.controls.clear()
        try:
            r = db.buscar_codigo(app.user["id"], codigo.value or "")
        except ReglaError as e:
            resultado.controls.append(ft.Container(
                ft.Row([ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.ERROR),
                        ft.Text(str(e), size=16, color=ft.Colors.ERROR, expand=True)], spacing=8), padding=10))
            app.page.update()
            return
        verificado = ft.Checkbox(label="Verifiqué el carné o DNI de la persona")
        motivo = campo("Motivo (solo si rechazas)")

        def entregar(_):
            app.confirmar(
                "¿Registrar la entrega?",
                f"Se entregará el objeto a {r['reclamante']} y los demás reclamos pasarán a rechazados.",
                lambda: app.hacer(lambda: db.entregar(app.user["id"], r["id"], bool(verificado.value)),
                                  "Entrega registrada en la bitácora.", app.render), "Entregar")

        def rechazar(_):
            app.confirmar(
                "¿Rechazar este reclamo?", "El objeto seguirá en custodia.",
                lambda: app.hacer(lambda: db.rechazar_reclamo(app.user["id"], r["id"], motivo.value or ""),
                                  "Reclamo rechazado.", app.render), "Rechazar")

        resultado.controls = [ft.Card(ft.Container(ft.Column([
            ft.Row([imagen_objeto(r, 72, 72, 10),
                    ft.Column([ft.Text(f"{r['categoria']} · {r['punto']}", weight="bold", size=16),
                               ft.Text(r["descripcion_publica"], size=15)], spacing=2, expand=True)], spacing=12),
            ft.Divider(),
            ft.Text(f"Reclamante: {r['reclamante']} ({r['reclamante_email']})", size=14),
            ft.Text("Según el reclamante:", size=14, weight="bold"),
            ft.Text(r["descripcion"], size=16),
            caja_aviso(ft.Text("Detalle oculto (solo funcionario)", size=14, weight="bold"),
                       ft.Text(r["detalle_oculto"] or "—", size=16)),
            verificado,
            ft.Row([boton("Entregar", entregar, ft.Icons.HANDSHAKE)]),
            motivo,
            ft.Row([ft.OutlinedButton("Rechazar reclamo", icon=ft.Icons.CLOSE, height=48, expand=True,
                                      on_click=rechazar)]),
        ], spacing=8), padding=14))]
        app.page.update()

    codigo.on_submit = buscar
    return ft.Column([titulo("Entrega", "Valida el código y verifica la identidad"), codigo,
                      ft.Row([boton("Validar código", buscar, ft.Icons.SEARCH)]), resultado], spacing=12)
