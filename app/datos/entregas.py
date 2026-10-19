"""Validación de código y entrega presencial."""
from .auditoria import auditar
from .conexion import ReglaError, a_texto, conectar, hora_actual
from .permisos import exigir_staff
from .vencimientos import limpiar_estados


def buscar_codigo(actor, codigo) -> dict:
    """Mensaje distinto para código inexistente, usado, vencido o de objeto no custodiado."""
    codigo = codigo.strip().upper()
    with conectar() as con:
        exigir_staff(con, actor)
        limpiar_estados(con)
        r = con.execute(
            "SELECT r.*, u.nombre AS reclamante, u.email AS reclamante_email, o.categoria, "
            "o.descripcion_publica, o.estado AS estado_objeto, p.nombre AS punto, op.detalle_oculto "
            "FROM reclamos r JOIN perfiles u ON u.id=r.reclamante_id JOIN objetos o ON o.id=r.objeto_id "
            "JOIN puntos_entrega p ON p.id=o.punto_id "
            "LEFT JOIN objetos_privado op ON op.objeto_id=o.id WHERE r.codigo=? ORDER BY r.id DESC",
            (codigo,)).fetchone()
        if not r:
            raise ReglaError("El código no existe.")
        if r["estado"] == "entregado":
            raise ReglaError("Este código ya se usó: el objeto ya fue entregado.")
        if r["estado"] == "vencido":
            raise ReglaError("El código venció. El usuario debe reclamar de nuevo.")
        if r["estado"] != "activo":
            raise ReglaError(f"El reclamo está en estado «{r['estado']}».")
        if r["estado_objeto"] != "EN_CUSTODIA":
            raise ReglaError("El objeto no está en custodia.")
        return dict(r)


def entregar(actor, rid, identidad_verificada: bool) -> None:
    if not identidad_verificada:
        raise ReglaError("Debes confirmar que verificaste el carné o DNI.")
    with conectar() as con:
        exigir_staff(con, actor)
        con.execute("BEGIN IMMEDIATE")  # evita doble entrega simultánea
        r = con.execute("SELECT * FROM reclamos WHERE id=?", (rid,)).fetchone()
        if not r or r["estado"] != "activo" or r["vence_en"] < a_texto(hora_actual()):
            raise ReglaError("El reclamo ya no está activo.")
        o = con.execute("SELECT estado FROM objetos WHERE id=?", (r["objeto_id"],)).fetchone()
        if o["estado"] != "EN_CUSTODIA":
            raise ReglaError("El objeto no está en custodia.")
        ahora = a_texto(hora_actual())
        con.execute("UPDATE reclamos SET estado='entregado', resuelto_por=?, resuelto_en=? WHERE id=?",
                    (actor, ahora, rid))
        con.execute("UPDATE objetos SET estado='ENTREGADO' WHERE id=?", (r["objeto_id"],))
        auditar(con, "objeto_entregado", actor, r["objeto_id"], rid, "EN_CUSTODIA", "ENTREGADO",
                 f"entregado a usuario {r['reclamante_id']}; identidad verificada")
        # RN-03: los demás reclamos activos pasan a rechazado
        for otro in con.execute("SELECT id FROM reclamos WHERE objeto_id=? AND estado='activo' AND id<>?",
                                (r["objeto_id"], rid)).fetchall():
            con.execute("UPDATE reclamos SET estado='rechazado', motivo='objeto entregado', "
                        "resuelto_por=?, resuelto_en=? WHERE id=?", (actor, ahora, otro["id"]))
            auditar(con, "reclamo_rechazado", actor, r["objeto_id"], otro["id"], "activo", "rechazado",
                     "objeto entregado")


def rechazar_reclamo(actor, rid, motivo) -> None:
    if not motivo.strip():
        raise ReglaError("El motivo es obligatorio.")
    with conectar() as con:
        exigir_staff(con, actor)
        r = con.execute("SELECT * FROM reclamos WHERE id=?", (rid,)).fetchone()
        if not r or r["estado"] != "activo":
            raise ReglaError("El reclamo ya no está activo.")
        con.execute("UPDATE reclamos SET estado='rechazado', motivo=?, resuelto_por=?, resuelto_en=? WHERE id=?",
                    (motivo.strip(), actor, a_texto(hora_actual()), rid))
        auditar(con, "reclamo_rechazado", actor, r["objeto_id"], rid, "activo", "rechazado", motivo.strip())
