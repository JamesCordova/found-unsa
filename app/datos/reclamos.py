"""Reclamos con código de un solo uso."""
from datetime import timedelta
import secrets
import sqlite3
from .auditoria import auditar
from .conexion import ReglaError, a_texto, conectar, hora_actual
from .config import ALFABETO_CODIGO, HORAS_CODIGO, MAX_RECLAMOS_ACTIVOS, MIN_DESC_RECLAMO
from .vencimientos import limpiar_estados


def crear_reclamo(uid, oid, descripcion) -> dict:
    descripcion = descripcion.strip()
    if len(descripcion) < MIN_DESC_RECLAMO:
        raise ReglaError(f"Describe el objeto con al menos {MIN_DESC_RECLAMO} caracteres.")
    with conectar() as con:
        limpiar_estados(con)
        u = con.execute("SELECT rol, bloqueado FROM perfiles WHERE id=?", (uid,)).fetchone()
        if u["bloqueado"]:
            raise ReglaError("Tu cuenta está bloqueada.")
        if u["rol"] != "usuario":
            raise ReglaError("Los funcionarios no pueden reclamar con su cuenta de funcionario.")
        o = con.execute("SELECT estado, publicado_por FROM objetos WHERE id=?", (oid,)).fetchone()
        if not o or o["estado"] != "EN_CUSTODIA":
            raise ReglaError("El objeto ya no está en custodia.")
        if o["publicado_por"] == uid:
            raise ReglaError("No puedes reclamar un objeto que tú publicaste.")
        activos = con.execute(
            "SELECT COUNT(*) FROM reclamos WHERE reclamante_id=? AND estado='activo'", (uid,)).fetchone()[0]
        if activos >= MAX_RECLAMOS_ACTIVOS:
            raise ReglaError(f"Ya tienes {MAX_RECLAMOS_ACTIVOS} reclamos activos.")
        codigo = "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(6))
        vence = a_texto(hora_actual() + timedelta(hours=HORAS_CODIGO))
        try:
            cur = con.execute(
                "INSERT INTO reclamos(objeto_id,reclamante_id,descripcion,codigo,vence_en,creado_en)"
                " VALUES (?,?,?,?,?,?)", (oid, uid, descripcion, codigo, vence, a_texto(hora_actual())))
        except sqlite3.IntegrityError:
            raise ReglaError("Ya tienes un reclamo activo sobre este objeto.")
        auditar(con, "reclamo_creado", uid, oid, cur.lastrowid, None, "activo")
        return {"id": cur.lastrowid, "codigo": codigo, "vence_en": vence}


def mis_reclamos(uid) -> list[dict]:
    with conectar() as con:
        limpiar_estados(con)
        return [dict(r) for r in con.execute(
            "SELECT r.*, o.descripcion_publica, o.categoria, o.foto_url, o.estado AS estado_objeto, p.nombre AS punto, "
            "p.ubicacion, p.horario FROM reclamos r JOIN objetos o ON o.id=r.objeto_id "
            "JOIN puntos_entrega p ON p.id=o.punto_id WHERE r.reclamante_id=? ORDER BY r.id DESC", (uid,))]


def cancelar_reclamo(uid, rid) -> None:
    with conectar() as con:
        r = con.execute("SELECT * FROM reclamos WHERE id=? AND reclamante_id=?", (rid, uid)).fetchone()
        if not r or r["estado"] != "activo":
            raise ReglaError("Solo puedes cancelar reclamos activos.")
        con.execute("UPDATE reclamos SET estado='cancelado' WHERE id=?", (rid,))
        auditar(con, "reclamo_cancelado", uid, r["objeto_id"], rid, "activo", "cancelado")
