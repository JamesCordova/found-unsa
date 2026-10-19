"""Capa de datos y reglas de negocio de Encontrado UNSA (SQLite).

Todas las reglas de estado y permisos viven aquí, no en la interfaz,
igual que en la especificación (donde viven en la base de datos).
"""
import hashlib
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).with_name("encontrado.db")
DOMINIO = "@unsa.edu.pe"
CATEGORIAS = [
    "Electrónicos",
    "Documentos y tarjetas",
    "Llaves",
    "Ropa y accesorios",
    "Útiles y libros",
    "Otros",
]
ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0, O, 1, I
HORAS_CODIGO = 48
MAX_RECLAMOS_ACTIVOS = 3
MIN_DESC_RECLAMO = 20
DIAS_PENDIENTE = 7
DIAS_ARCHIVADO = 60


class ReglaError(Exception):
    """Operación rechazada por una regla de negocio; el mensaje va al usuario."""


def _ahora() -> datetime:
    return datetime.now().replace(microsecond=0)


def _fmt(dt: datetime) -> str:
    return dt.isoformat(sep=" ")


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


@contextmanager
def conectar():
    """Abre la base, confirma al salir (o revierte si hubo error) y siempre cierra."""
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        with con:
            yield con
    finally:
        con.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS perfiles (
  id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL,
  clave TEXT NOT NULL, rol TEXT NOT NULL DEFAULT 'usuario'
    CHECK (rol IN ('usuario','funcionario','admin')),
  bloqueado INTEGER NOT NULL DEFAULT 0, creado_en TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS puntos_entrega (
  id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, ubicacion TEXT NOT NULL,
  horario TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS objetos (
  id INTEGER PRIMARY KEY, categoria TEXT NOT NULL, descripcion_publica TEXT NOT NULL,
  lugar_hallazgo TEXT NOT NULL, fecha_hallazgo TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'PENDIENTE_RECEPCION'
    CHECK (estado IN ('PENDIENTE_RECEPCION','EN_CUSTODIA','ENTREGADO','RECHAZADO','ARCHIVADO')),
  motivo TEXT, publicado_por INTEGER NOT NULL REFERENCES perfiles(id),
  punto_id INTEGER NOT NULL REFERENCES puntos_entrega(id),
  recibido_por INTEGER REFERENCES perfiles(id), recibido_en TEXT,
  creado_en TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS objetos_privado (
  objeto_id INTEGER PRIMARY KEY REFERENCES objetos(id),
  detalle_oculto TEXT NOT NULL, notas_internas TEXT);
CREATE TABLE IF NOT EXISTS reclamos (
  id INTEGER PRIMARY KEY, objeto_id INTEGER NOT NULL REFERENCES objetos(id),
  reclamante_id INTEGER NOT NULL REFERENCES perfiles(id), descripcion TEXT NOT NULL,
  codigo TEXT NOT NULL, vence_en TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'activo'
    CHECK (estado IN ('activo','entregado','rechazado','vencido','cancelado')),
  resuelto_por INTEGER REFERENCES perfiles(id), resuelto_en TEXT, motivo TEXT,
  creado_en TEXT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS ux_reclamo_activo
  ON reclamos(objeto_id, reclamante_id) WHERE estado = 'activo';
CREATE TABLE IF NOT EXISTS auditoria (
  id INTEGER PRIMARY KEY, objeto_id INTEGER, reclamo_id INTEGER, accion TEXT NOT NULL,
  estado_anterior TEXT, estado_nuevo TEXT, actor_id INTEGER, detalle TEXT,
  creado_en TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS auditoria_sin_update BEFORE UPDATE ON auditoria
  BEGIN SELECT RAISE(ABORT, 'La bitácora es inmutable'); END;
CREATE TRIGGER IF NOT EXISTS auditoria_sin_delete BEFORE DELETE ON auditoria
  BEGIN SELECT RAISE(ABORT, 'La bitácora es inmutable'); END;
"""


def iniciar() -> None:
    """Crea las tablas y, la primera vez, las cuentas y puntos de demostración."""
    with conectar() as con:
        con.executescript(SCHEMA)
        if con.execute("SELECT COUNT(*) FROM perfiles").fetchone()[0]:
            return
        ahora = _fmt(_ahora())
        for email, nombre, rol in [
            ("usuario@unsa.edu.pe", "Ana Usuario", "usuario"),
            ("otro@unsa.edu.pe", "Luis Usuario", "usuario"),
            ("funcionario@unsa.edu.pe", "Rosa Portería", "funcionario"),
            ("admin@unsa.edu.pe", "Admin UNSA", "admin"),
        ]:
            con.execute(
                "INSERT INTO perfiles(email,nombre,clave,rol,creado_en) VALUES (?,?,?,?,?)",
                (email, nombre, _hash("1234"), rol, ahora),
            )
        for nombre, ubic, horario in [
            ("Portería principal", "Ingreso por la Av. Independencia", "Lun-Vie 7:00-19:00"),
            ("Secretaría de Ingeniería", "Pabellón de Ingeniería, 1.er piso", "Lun-Vie 8:00-16:00"),
        ]:
            con.execute(
                "INSERT INTO puntos_entrega(nombre,ubicacion,horario) VALUES (?,?,?)",
                (nombre, ubic, horario),
            )


def _auditar(con, accion, actor_id, objeto_id=None, reclamo_id=None, antes=None, despues=None, detalle=None):
    con.execute(
        "INSERT INTO auditoria(objeto_id,reclamo_id,accion,estado_anterior,estado_nuevo,actor_id,detalle,creado_en)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (objeto_id, reclamo_id, accion, antes, despues, actor_id, detalle, _fmt(_ahora())),
    )


def _exigir_staff(con, actor_id):
    p = con.execute("SELECT rol, bloqueado FROM perfiles WHERE id=?", (actor_id,)).fetchone()
    if not p or p["rol"] not in ("funcionario", "admin") or p["bloqueado"]:
        raise ReglaError("Solo un funcionario o administrador puede hacer esto.")


def _exigir_admin(con, actor_id):
    p = con.execute("SELECT rol FROM perfiles WHERE id=?", (actor_id,)).fetchone()
    if not p or p["rol"] != "admin":
        raise ReglaError("Solo un administrador puede hacer esto.")


# ---------- Cuenta ----------

def registrar(nombre: str, email: str, clave: str) -> None:
    email = email.strip().lower()
    if not email.endswith(DOMINIO):
        raise ReglaError(f"Solo se aceptan correos institucionales ({DOMINIO}).")
    if not nombre.strip() or len(nombre) > 60:
        raise ReglaError("El nombre es obligatorio (máximo 60 caracteres).")
    if len(clave) < 4:
        raise ReglaError("La contraseña debe tener al menos 4 caracteres.")
    try:
        with conectar() as con:
            con.execute(
                "INSERT INTO perfiles(email,nombre,clave,creado_en) VALUES (?,?,?,?)",
                (email, nombre.strip(), _hash(clave), _fmt(_ahora())),
            )
    except sqlite3.IntegrityError:
        raise ReglaError("Ya existe una cuenta con ese correo.")


def iniciar_sesion(email: str, clave: str) -> dict:
    email = email.strip().lower()
    if not email.endswith(DOMINIO):
        raise ReglaError(f"Solo se aceptan correos institucionales ({DOMINIO}).")
    with conectar() as con:
        p = con.execute("SELECT * FROM perfiles WHERE email=?", (email,)).fetchone()
    if not p or p["clave"] != _hash(clave):
        raise ReglaError("Correo o contraseña incorrectos.")
    return dict(p)


def perfil(uid: int) -> dict:
    with conectar() as con:
        return dict(con.execute("SELECT * FROM perfiles WHERE id=?", (uid,)).fetchone())


# ---------- Publicación y recepción ----------

def puntos_activos() -> list[dict]:
    with conectar() as con:
        return [dict(r) for r in con.execute("SELECT * FROM puntos_entrega WHERE activo=1")]


def publicar(uid, categoria, descripcion, lugar, fecha_txt, punto_id) -> None:
    descripcion, lugar = descripcion.strip(), lugar.strip()
    if categoria not in CATEGORIAS:
        raise ReglaError("Elige una categoría.")
    if not descripcion or len(descripcion) > 280:
        raise ReglaError("La descripción pública es obligatoria (máximo 280 caracteres).")
    if not lugar:
        raise ReglaError("Indica dónde lo encontraste.")
    if not punto_id:
        raise ReglaError("Elige el punto de entrega.")
    try:
        fecha = datetime.strptime(fecha_txt.strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        raise ReglaError("La fecha debe tener el formato AAAA-MM-DD HH:MM.")
    if fecha > _ahora():
        raise ReglaError("La fecha del hallazgo no puede ser futura.")
    with conectar() as con:
        p = con.execute("SELECT bloqueado FROM perfiles WHERE id=?", (uid,)).fetchone()
        if p["bloqueado"]:
            raise ReglaError("Tu cuenta está bloqueada.")
        cur = con.execute(
            "INSERT INTO objetos(categoria,descripcion_publica,lugar_hallazgo,fecha_hallazgo,"
            "publicado_por,punto_id,creado_en) VALUES (?,?,?,?,?,?,?)",
            (categoria, descripcion, lugar, _fmt(fecha), uid, punto_id, _fmt(_ahora())),
        )
        _auditar(con, "publicacion_creada", uid, cur.lastrowid, despues="PENDIENTE_RECEPCION")


def _limpiar_estados(con) -> None:
    """RN-10, RN-11 y EN-04: los vencimientos se evalúan al consultar."""
    ahora = _fmt(_ahora())
    for r in con.execute("SELECT id FROM reclamos WHERE estado='activo' AND vence_en < ?", (ahora,)).fetchall():
        con.execute("UPDATE reclamos SET estado='vencido' WHERE id=?", (r["id"],))
        _auditar(con, "reclamo_vencido", None, reclamo_id=r["id"], antes="activo", despues="vencido")
    limite = _fmt(_ahora() - timedelta(days=DIAS_PENDIENTE))
    for r in con.execute("SELECT id FROM objetos WHERE estado='PENDIENTE_RECEPCION' AND creado_en < ?", (limite,)).fetchall():
        con.execute("UPDATE objetos SET estado='RECHAZADO', motivo='no llegó' WHERE id=?", (r["id"],))
        _auditar(con, "publicacion_rechazada_auto", None, r["id"], "PENDIENTE_RECEPCION", "RECHAZADO", detalle="no llegó")
    limite = _fmt(_ahora() - timedelta(days=DIAS_ARCHIVADO))
    for r in con.execute("SELECT id FROM objetos WHERE estado='EN_CUSTODIA' AND recibido_en < ?", (limite,)).fetchall():
        con.execute("UPDATE objetos SET estado='ARCHIVADO' WHERE id=?", (r["id"],))
        _auditar(con, "objeto_archivado", None, r["id"], "EN_CUSTODIA", "ARCHIVADO")


def mis_publicaciones(uid) -> list[dict]:
    with conectar() as con:
        _limpiar_estados(con)
        return [dict(r) for r in con.execute(
            "SELECT o.*, p.nombre AS punto FROM objetos o JOIN puntos_entrega p ON p.id=o.punto_id "
            "WHERE publicado_por=? ORDER BY o.id DESC", (uid,))]


def cancelar_publicacion(uid, oid) -> None:
    with conectar() as con:
        o = con.execute("SELECT * FROM objetos WHERE id=? AND publicado_por=?", (oid, uid)).fetchone()
        if not o or o["estado"] != "PENDIENTE_RECEPCION":
            raise ReglaError("Solo puedes cancelar publicaciones pendientes de recepción.")
        con.execute("UPDATE objetos SET estado='RECHAZADO', motivo='cancelada por el hallador' WHERE id=?", (oid,))
        _auditar(con, "publicacion_cancelada", uid, oid, "PENDIENTE_RECEPCION", "RECHAZADO")


def pendientes() -> list[dict]:
    with conectar() as con:
        _limpiar_estados(con)
        return [dict(r) for r in con.execute(
            "SELECT o.*, p.nombre AS punto FROM objetos o JOIN puntos_entrega p ON p.id=o.punto_id "
            "WHERE estado='PENDIENTE_RECEPCION' ORDER BY o.id")]


def confirmar_recepcion(actor, oid, detalle_oculto, notas="") -> None:
    if not detalle_oculto.strip():
        raise ReglaError("Registra al menos un detalle oculto de verificación.")
    with conectar() as con:
        _exigir_staff(con, actor)
        o = con.execute("SELECT estado FROM objetos WHERE id=?", (oid,)).fetchone()
        if not o or o["estado"] != "PENDIENTE_RECEPCION":
            raise ReglaError("La publicación ya no está pendiente de recepción.")
        con.execute(
            "UPDATE objetos SET estado='EN_CUSTODIA', recibido_por=?, recibido_en=? WHERE id=?",
            (actor, _fmt(_ahora()), oid),
        )
        con.execute(
            "INSERT OR REPLACE INTO objetos_privado(objeto_id,detalle_oculto,notas_internas) VALUES (?,?,?)",
            (oid, detalle_oculto.strip(), notas.strip() or None),
        )
        _auditar(con, "recepcion_confirmada", actor, oid, "PENDIENTE_RECEPCION", "EN_CUSTODIA")


def rechazar_publicacion(actor, oid, motivo) -> None:
    if not motivo.strip():
        raise ReglaError("El motivo es obligatorio.")
    with conectar() as con:
        _exigir_staff(con, actor)
        o = con.execute("SELECT estado FROM objetos WHERE id=?", (oid,)).fetchone()
        if not o or o["estado"] != "PENDIENTE_RECEPCION":
            raise ReglaError("La publicación ya no está pendiente de recepción.")
        con.execute("UPDATE objetos SET estado='RECHAZADO', motivo=? WHERE id=?", (motivo.strip(), oid))
        _auditar(con, "recepcion_rechazada", actor, oid, "PENDIENTE_RECEPCION", "RECHAZADO", motivo.strip())


# ---------- Catálogo ----------

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
        _limpiar_estados(con)
        return [dict(r) for r in con.execute(sql, args)]


# ---------- Reclamos ----------

def crear_reclamo(uid, oid, descripcion) -> dict:
    descripcion = descripcion.strip()
    if len(descripcion) < MIN_DESC_RECLAMO:
        raise ReglaError(f"Describe el objeto con al menos {MIN_DESC_RECLAMO} caracteres.")
    with conectar() as con:
        _limpiar_estados(con)
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
        vence = _fmt(_ahora() + timedelta(hours=HORAS_CODIGO))
        try:
            cur = con.execute(
                "INSERT INTO reclamos(objeto_id,reclamante_id,descripcion,codigo,vence_en,creado_en)"
                " VALUES (?,?,?,?,?,?)", (oid, uid, descripcion, codigo, vence, _fmt(_ahora())))
        except sqlite3.IntegrityError:
            raise ReglaError("Ya tienes un reclamo activo sobre este objeto.")
        _auditar(con, "reclamo_creado", uid, oid, cur.lastrowid, None, "activo")
        return {"id": cur.lastrowid, "codigo": codigo, "vence_en": vence}


def mis_reclamos(uid) -> list[dict]:
    with conectar() as con:
        _limpiar_estados(con)
        return [dict(r) for r in con.execute(
            "SELECT r.*, o.descripcion_publica, o.estado AS estado_objeto, p.nombre AS punto, "
            "p.ubicacion, p.horario FROM reclamos r JOIN objetos o ON o.id=r.objeto_id "
            "JOIN puntos_entrega p ON p.id=o.punto_id WHERE r.reclamante_id=? ORDER BY r.id DESC", (uid,))]


def cancelar_reclamo(uid, rid) -> None:
    with conectar() as con:
        r = con.execute("SELECT * FROM reclamos WHERE id=? AND reclamante_id=?", (rid, uid)).fetchone()
        if not r or r["estado"] != "activo":
            raise ReglaError("Solo puedes cancelar reclamos activos.")
        con.execute("UPDATE reclamos SET estado='cancelado' WHERE id=?", (rid,))
        _auditar(con, "reclamo_cancelado", uid, r["objeto_id"], rid, "activo", "cancelado")


# ---------- Entrega ----------

def buscar_codigo(actor, codigo) -> dict:
    """Mensaje distinto para código inexistente, usado, vencido o de objeto no custodiado."""
    codigo = codigo.strip().upper()
    with conectar() as con:
        _exigir_staff(con, actor)
        _limpiar_estados(con)
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
        raise ReglaError("Debes confirmar que verificaste el carné o DNI (RN-07).")
    with conectar() as con:
        _exigir_staff(con, actor)
        con.execute("BEGIN IMMEDIATE")  # evita doble entrega simultánea
        r = con.execute("SELECT * FROM reclamos WHERE id=?", (rid,)).fetchone()
        if not r or r["estado"] != "activo" or r["vence_en"] < _fmt(_ahora()):
            raise ReglaError("El reclamo ya no está activo.")
        o = con.execute("SELECT estado FROM objetos WHERE id=?", (r["objeto_id"],)).fetchone()
        if o["estado"] != "EN_CUSTODIA":
            raise ReglaError("El objeto no está en custodia.")
        ahora = _fmt(_ahora())
        con.execute("UPDATE reclamos SET estado='entregado', resuelto_por=?, resuelto_en=? WHERE id=?",
                    (actor, ahora, rid))
        con.execute("UPDATE objetos SET estado='ENTREGADO' WHERE id=?", (r["objeto_id"],))
        _auditar(con, "objeto_entregado", actor, r["objeto_id"], rid, "EN_CUSTODIA", "ENTREGADO",
                 f"entregado a usuario {r['reclamante_id']}; identidad verificada")
        # RN-03: los demás reclamos activos pasan a rechazado
        for otro in con.execute("SELECT id FROM reclamos WHERE objeto_id=? AND estado='activo' AND id<>?",
                                (r["objeto_id"], rid)).fetchall():
            con.execute("UPDATE reclamos SET estado='rechazado', motivo='objeto entregado', "
                        "resuelto_por=?, resuelto_en=? WHERE id=?", (actor, ahora, otro["id"]))
            _auditar(con, "reclamo_rechazado", actor, r["objeto_id"], otro["id"], "activo", "rechazado",
                     "objeto entregado")


def rechazar_reclamo(actor, rid, motivo) -> None:
    if not motivo.strip():
        raise ReglaError("El motivo es obligatorio.")
    with conectar() as con:
        _exigir_staff(con, actor)
        r = con.execute("SELECT * FROM reclamos WHERE id=?", (rid,)).fetchone()
        if not r or r["estado"] != "activo":
            raise ReglaError("El reclamo ya no está activo.")
        con.execute("UPDATE reclamos SET estado='rechazado', motivo=?, resuelto_por=?, resuelto_en=? WHERE id=?",
                    (motivo.strip(), actor, _fmt(_ahora()), rid))
        _auditar(con, "reclamo_rechazado", actor, r["objeto_id"], rid, "activo", "rechazado", motivo.strip())


def bitacora(actor, accion="") -> list[dict]:
    with conectar() as con:
        _exigir_staff(con, actor)
        sql = ("SELECT a.*, u.nombre AS actor FROM auditoria a LEFT JOIN perfiles u ON u.id=a.actor_id")
        args: list = []
        if accion:
            sql += " WHERE a.accion LIKE ?"
            args.append(f"%{accion}%")
        return [dict(r) for r in con.execute(sql + " ORDER BY a.id DESC LIMIT 100", args)]


# ---------- Administración ----------

def usuarios(actor) -> list[dict]:
    with conectar() as con:
        _exigir_admin(con, actor)
        return [dict(r) for r in con.execute("SELECT id,email,nombre,rol,bloqueado FROM perfiles ORDER BY id")]


def cambiar_rol(actor, uid, rol) -> None:
    if rol not in ("usuario", "funcionario", "admin"):
        raise ReglaError("Rol inválido.")
    with conectar() as con:
        _exigir_admin(con, actor)
        if uid == actor:
            raise ReglaError("No puedes cambiar tu propio rol.")
        antes = con.execute("SELECT rol FROM perfiles WHERE id=?", (uid,)).fetchone()["rol"]
        con.execute("UPDATE perfiles SET rol=? WHERE id=?", (rol, uid))
        _auditar(con, "rol_cambiado", actor, None, None, antes, rol, f"usuario {uid}")


def bloquear(actor, uid, bloqueado: bool) -> None:
    with conectar() as con:
        _exigir_admin(con, actor)
        if uid == actor:
            raise ReglaError("No puedes bloquearte a ti mismo.")
        con.execute("UPDATE perfiles SET bloqueado=? WHERE id=?", (int(bloqueado), uid))
        if bloqueado:  # los reclamos activos se cancelan
            for r in con.execute("SELECT id, objeto_id FROM reclamos WHERE reclamante_id=? AND estado='activo'",
                                 (uid,)).fetchall():
                con.execute("UPDATE reclamos SET estado='cancelado' WHERE id=?", (r["id"],))
                _auditar(con, "reclamo_cancelado", actor, r["objeto_id"], r["id"], "activo", "cancelado", "usuario bloqueado")
        _auditar(con, "usuario_bloqueado" if bloqueado else "usuario_desbloqueado", actor, detalle=f"usuario {uid}")
