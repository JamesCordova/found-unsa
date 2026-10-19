-- Encontrado UNSA · 001 · Tablas, restricciones, triggers y seguridad por fila (RLS)
-- Pegar completo en Supabase → SQL Editor → Run. Es seguro volver a ejecutarlo.
--
-- Principio: la seguridad se aplica en la base, no en la app. Las tablas solo se pueden LEER
-- (con RLS); toda escritura pasa por las funciones de 002_funciones.sql.

-- ---------------------------------------------------------------- tablas
create table if not exists perfiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  nombre text not null check (char_length(nombre) between 1 and 60),
  rol text not null default 'usuario' check (rol in ('usuario', 'funcionario', 'admin')),
  bloqueado boolean not null default false,
  creado_en timestamptz not null default now()
);

create table if not exists puntos_entrega (
  id uuid primary key default gen_random_uuid(),
  nombre text not null check (char_length(nombre) between 1 and 60),
  ubicacion text not null,
  horario text not null,
  activo boolean not null default true
);
create unique index if not exists ux_puntos_nombre on puntos_entrega (lower(nombre));

create table if not exists objetos (
  id uuid primary key default gen_random_uuid(),
  categoria text not null check (categoria in
    ('Electrónicos', 'Documentos y tarjetas', 'Llaves', 'Ropa y accesorios', 'Útiles y libros', 'Otros')),
  descripcion_publica text not null check (char_length(descripcion_publica) between 1 and 280),
  lugar_hallazgo text not null,
  fecha_hallazgo timestamptz not null,
  foto_url text check (foto_url is null or (foto_url ~* '^https?://' and char_length(foto_url) <= 500)),
  estado text not null default 'PENDIENTE_RECEPCION' check (estado in
    ('PENDIENTE_RECEPCION', 'EN_CUSTODIA', 'ENTREGADO', 'RECHAZADO', 'ARCHIVADO')),
  motivo text,
  publicado_por uuid references perfiles(id) on delete set null,  -- si la cuenta se elimina, la publicación se conserva
  punto_id uuid not null references puntos_entrega(id),
  recibido_por uuid references perfiles(id) on delete set null,
  recibido_en timestamptz,
  creado_en timestamptz not null default now()
);
create index if not exists ix_objetos_estado on objetos (estado, creado_en desc);
create index if not exists ix_objetos_categoria on objetos (categoria);

-- Solo funcionarios y administradores pueden leerla (detalle oculto de verificación).
create table if not exists objetos_privado (
  objeto_id uuid primary key references objetos(id) on delete cascade,
  detalle_oculto text not null,
  notas_internas text
);

create table if not exists reclamos (
  id uuid primary key default gen_random_uuid(),
  objeto_id uuid not null references objetos(id) on delete cascade,
  reclamante_id uuid not null references perfiles(id) on delete cascade,
  descripcion text not null check (char_length(descripcion) >= 20),
  codigo text not null,
  vence_en timestamptz not null,
  estado text not null default 'activo' check (estado in ('activo', 'entregado', 'rechazado', 'vencido', 'cancelado')),
  resuelto_por uuid references perfiles(id) on delete set null,
  resuelto_en timestamptz,
  motivo text,
  creado_en timestamptz not null default now()
);
create index if not exists ix_reclamos_objeto on reclamos (objeto_id, estado);
create unique index if not exists ux_reclamo_activo on reclamos (objeto_id, reclamante_id) where estado = 'activo';
create unique index if not exists ux_codigo_activo on reclamos (codigo) where estado = 'activo';

create table if not exists auditoria (
  id bigint generated always as identity primary key,
  objeto_id uuid,
  reclamo_id uuid,
  accion text not null,
  estado_anterior text,
  estado_nuevo text,
  actor_id uuid,
  detalle text,
  creado_en timestamptz not null default now()
);

-- ---------------------------------------------------------------- bitácora inmutable
create or replace function auditoria_inmutable() returns trigger language plpgsql as $$
begin
  raise exception 'La bitácora es inmutable';
end $$;

drop trigger if exists auditoria_sin_cambios on auditoria;
create trigger auditoria_sin_cambios before update or delete on auditoria
  for each row execute function auditoria_inmutable();

-- ---------------------------------------------------------------- roles auxiliares
create or replace function es_staff() returns boolean
language sql security definer stable set search_path = public as $$
  select exists (select 1 from perfiles where id = auth.uid() and rol in ('funcionario', 'admin') and not bloqueado);
$$;

create or replace function es_admin() returns boolean
language sql security definer stable set search_path = public as $$
  select exists (select 1 from perfiles where id = auth.uid() and rol = 'admin' and not bloqueado);
$$;

-- ---------------------------------------------------------------- registro: dominio y perfil
-- El dominio se valida en el servidor (CU-01): aunque alguien llame directo a la API, se rechaza.
create or replace function validar_dominio_institucional() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if lower(new.email) not like '%@unsa.edu.pe' then
    raise exception 'Solo se aceptan correos institucionales (@unsa.edu.pe).';
  end if;
  return new;
end $$;

create or replace function crear_perfil() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into perfiles (id, email, nombre)
  values (new.id, lower(new.email),
          left(coalesce(nullif(trim(new.raw_user_meta_data ->> 'nombre'), ''), split_part(new.email, '@', 1)), 60))
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists validar_dominio on auth.users;
create trigger validar_dominio before insert on auth.users
  for each row execute function validar_dominio_institucional();

drop trigger if exists crear_perfil_al_registrarse on auth.users;
create trigger crear_perfil_al_registrarse after insert on auth.users
  for each row execute function crear_perfil();

-- ---------------------------------------------------------------- RLS
alter table perfiles enable row level security;
alter table puntos_entrega enable row level security;
alter table objetos enable row level security;
alter table objetos_privado enable row level security;
alter table reclamos enable row level security;
alter table auditoria enable row level security;

drop policy if exists perfiles_ver on perfiles;
create policy perfiles_ver on perfiles for select to authenticated
  using (id = auth.uid() or es_staff());

drop policy if exists puntos_ver on puntos_entrega;
create policy puntos_ver on puntos_entrega for select to authenticated using (true);

-- El catálogo solo muestra objetos en custodia; el hallador ve los suyos y el staff ve todo (RN-01).
drop policy if exists objetos_ver on objetos;
create policy objetos_ver on objetos for select to authenticated
  using (estado = 'EN_CUSTODIA' or publicado_por = auth.uid() or es_staff());

drop policy if exists privado_ver on objetos_privado;
create policy privado_ver on objetos_privado for select to authenticated using (es_staff());

drop policy if exists reclamos_ver on reclamos;
create policy reclamos_ver on reclamos for select to authenticated
  using (reclamante_id = auth.uid() or es_staff());

drop policy if exists auditoria_ver on auditoria;
create policy auditoria_ver on auditoria for select to authenticated using (es_staff());

-- Sin políticas de insert/update/delete: nadie puede escribir directo, solo las funciones.

-- ---------------------------------------------------------------- permisos de tabla (defensa en profundidad)
revoke all on perfiles, puntos_entrega, objetos, objetos_privado, reclamos, auditoria from anon, authenticated;
grant select on perfiles, puntos_entrega, objetos, objetos_privado, reclamos, auditoria to authenticated;

revoke execute on function es_staff(), es_admin() from public, anon;
grant execute on function es_staff(), es_admin() to authenticated;

notify pgrst, 'reload schema';
