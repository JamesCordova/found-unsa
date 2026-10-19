"""Tablas, triggers y migración de la base."""
from .demo import sembrar_demo
from .conexion import a_texto, conectar, hash_clave, hora_actual


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
  motivo TEXT, foto_url TEXT, publicado_por INTEGER NOT NULL REFERENCES perfiles(id),
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


def crear_base(con) -> None:
    """Crea las tablas y, la primera vez, las cuentas y puntos de demostración."""
    con.executescript(SCHEMA)
    if con.execute("SELECT COUNT(*) FROM perfiles").fetchone()[0]:
        return
    ahora = a_texto(hora_actual())
    for email, nombre, rol in [
        ("usuario@unsa.edu.pe", "Ana Usuario", "usuario"),
        ("otro@unsa.edu.pe", "Luis Usuario", "usuario"),
        ("funcionario@unsa.edu.pe", "Rosa Portería", "funcionario"),
        ("admin@unsa.edu.pe", "Admin UNSA", "admin"),
    ]:
        con.execute(
            "INSERT INTO perfiles(email,nombre,clave,rol,creado_en) VALUES (?,?,?,?,?)",
            (email, nombre, hash_clave("1234"), rol, ahora),
        )
    for nombre, ubic, horario in [
        ("Portería principal", "Ingreso por la Av. Independencia", "Lun-Vie 7:00-19:00"),
        ("Secretaría de Ingeniería", "Pabellón de Ingeniería, 1.er piso", "Lun-Vie 8:00-16:00"),
    ]:
        con.execute(
            "INSERT INTO puntos_entrega(nombre,ubicacion,horario) VALUES (?,?,?)",
            (nombre, ubic, horario),
        )


def asegurar_esquema(con) -> None:
    """Crea la base si falta, agrega columnas nuevas a bases antiguas y siembra datos de demostración."""
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='perfiles'").fetchone():
        crear_base(con)
    elif "foto_url" not in {r[1] for r in con.execute("PRAGMA table_info(objetos)")}:
        con.execute("ALTER TABLE objetos ADD COLUMN foto_url TEXT")
    if not con.execute("SELECT 1 FROM objetos").fetchone() and not con.execute("SELECT 1 FROM auditoria").fetchone():
        sembrar_demo(con)


def iniciar() -> None:
    with conectar():  # conectar() crea la base si falta
        pass
