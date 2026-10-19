"""Vencimientos evaluados al consultar (RN-10, RN-11, EN-04)."""
from datetime import timedelta
from .auditoria import auditar
from .conexion import a_texto, hora_actual
from .config import DIAS_ARCHIVADO, DIAS_PENDIENTE


def limpiar_estados(con) -> None:
    """RN-10, RN-11 y EN-04: los vencimientos se evalúan al consultar."""
    ahora = a_texto(hora_actual())
    for r in con.execute("SELECT id FROM reclamos WHERE estado='activo' AND vence_en < ?", (ahora,)).fetchall():
        con.execute("UPDATE reclamos SET estado='vencido' WHERE id=?", (r["id"],))
        auditar(con, "reclamo_vencido", None, reclamo_id=r["id"], antes="activo", despues="vencido")
    limite = a_texto(hora_actual() - timedelta(days=DIAS_PENDIENTE))
    for r in con.execute("SELECT id FROM objetos WHERE estado='PENDIENTE_RECEPCION' AND creado_en < ?", (limite,)).fetchall():
        con.execute("UPDATE objetos SET estado='RECHAZADO', motivo='no llegó' WHERE id=?", (r["id"],))
        auditar(con, "publicacion_rechazada_auto", None, r["id"], "PENDIENTE_RECEPCION", "RECHAZADO", detalle="no llegó")
    limite = a_texto(hora_actual() - timedelta(days=DIAS_ARCHIVADO))
    for r in con.execute("SELECT id FROM objetos WHERE estado='EN_CUSTODIA' AND recibido_en < ?", (limite,)).fetchall():
        con.execute("UPDATE objetos SET estado='ARCHIVADO' WHERE id=?", (r["id"],))
        auditar(con, "objeto_archivado", None, r["id"], "EN_CUSTODIA", "ARCHIVADO")
