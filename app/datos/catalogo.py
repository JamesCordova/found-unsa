"""Catálogo público de objetos en custodia."""
from .conexion import conectar
from .vencimientos import limpiar_estados


def catalogo(categoria=None, punto_id=None, texto="") -> list[dict]:
    """Solo objetos EN_CUSTODIA. Nunca toca objetos_privado (CA-04)."""
    sql = ("SELECT o.id, o.categoria, o.descripcion_publica, o.lugar_hallazgo, o.fecha_hallazgo, "
           "o.publicado_por, o.punto_id, p.nombre AS punto, p.ubicacion, p.horario "
           "FROM objetos o JOIN puntos_entrega p ON p.id=o.punto_id WHERE o.estado='EN_CUSTODIA'")
    args: list = []
    if categoria:
        sql += " AND o.categoria=?"
        args.append(categoria)
    if punto_id:
        sql += " AND o.punto_id=?"
        args.append(int(punto_id))
    if texto.strip():
        sql += " AND o.descripcion_publica LIKE ?"
        args.append(f"%{texto.strip()}%")
    sql += " ORDER BY o.recibido_en DESC"
    with conectar() as con:
        limpiar_estados(con)
        return [dict(r) for r in con.execute(sql, args)]
