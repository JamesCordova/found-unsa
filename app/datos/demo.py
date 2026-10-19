"""Datos de demostración: objetos con imágenes de ejemplo (enlaces a placehold.co, no se guardan archivos)."""
from datetime import timedelta
from urllib.parse import quote

from .auditoria import auditar
from .conexion import a_texto, hora_actual


def _foto(texto: str, fondo: str) -> str:
    return f"https://placehold.co/600x400/{fondo}/ffffff/png?text={quote(texto)}"


# (categoría, descripción pública, lugar, días atrás, punto, foto, detalle oculto, estado)
DEMO = [
    ("Llaves", "Llavero con tres llaves y un pequeño peluche de zorro", "Biblioteca central, 2.º piso", 1, 0,
     _foto("Llavero", "4f46e5"), "El peluche tiene un parche azul en la oreja izquierda", "EN_CUSTODIA"),
    ("Electrónicos", "Audífonos inalámbricos negros con su estuche de carga", "Pabellón de Ingeniería", 2, 1,
     _foto("Audífonos", "0f766e"), "Estuche con una calcomanía de un rayo en la tapa", "EN_CUSTODIA"),
    ("Ropa y accesorios", "Casaca azul marino talla M con capucha", "Comedor universitario", 3, 0,
     _foto("Casaca", "b45309"), "Etiqueta cosida con las iniciales J.R.", "EN_CUSTODIA"),
    ("Útiles y libros", "Calculadora científica y un cuaderno cuadriculado", "Aula 204", 5, 1,
     _foto("Calculadora", "be185d"), "Primera página del cuaderno con un dibujo de un cohete", "EN_CUSTODIA"),
    ("Documentos y tarjetas", "Carné universitario hallado en el patio central", "Patio central", 1, 0,
     None, "Carrera impresa en el carné: Ingeniería de Sistemas", "EN_CUSTODIA"),
    ("Otros", "Paraguas negro grande con mango de madera", "Entrada principal", 0, 0,
     _foto("Paraguas", "475569"), None, "PENDIENTE_RECEPCION"),
]


def sembrar_demo(con) -> None:
    ids = {r["email"]: r["id"] for r in con.execute("SELECT id, email FROM perfiles")}
    puntos = [r["id"] for r in con.execute("SELECT id FROM puntos_entrega ORDER BY id")]
    autor, staff = ids.get("usuario@unsa.edu.pe"), ids.get("funcionario@unsa.edu.pe")
    if not (autor and staff and len(puntos) >= 2):
        return
    ahora = hora_actual()
    for cat, desc, lugar, dias, punto, foto, oculto, estado in DEMO:
        hallado = ahora - timedelta(days=dias, hours=2)
        recibido = a_texto(hallado + timedelta(hours=3)) if estado == "EN_CUSTODIA" else None
        cur = con.execute(
            "INSERT INTO objetos(categoria,descripcion_publica,lugar_hallazgo,fecha_hallazgo,estado,foto_url,"
            "publicado_por,punto_id,recibido_por,recibido_en,creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (cat, desc, lugar, a_texto(hallado), estado, foto, autor, puntos[punto],
             staff if recibido else None, recibido, a_texto(hallado)))
        oid = cur.lastrowid
        auditar(con, "publicacion_creada", autor, oid, despues="PENDIENTE_RECEPCION")
        if oculto:
            con.execute("INSERT INTO objetos_privado(objeto_id, detalle_oculto) VALUES (?,?)", (oid, oculto))
            auditar(con, "recepcion_confirmada", staff, oid, antes="PENDIENTE_RECEPCION", despues="EN_CUSTODIA")
