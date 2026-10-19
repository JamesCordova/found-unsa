-- Encontrado UNSA · 002 · Funciones de negocio (se llaman desde la app como /rpc/nombre)
-- Ejecutar DESPUÉS de 001_esquema.sql. Es seguro volver a ejecutarlo.
--
-- Todas son "security definer": se ejecutan con permisos del dueño, pero cada una verifica
-- primero quién llama (auth.uid()) y su rol. Los mensajes de error van directo al usuario.

-- ---------------------------------------------------------------- internas
create or replace function auditar(
  p_accion text, p_actor uuid, p_objeto uuid default null, p_reclamo uuid default null,
  p_antes text default null, p_despues text default null, p_detalle text default null
) returns void language sql security definer set search_path = public as $$
  insert into auditoria (objeto_id, reclamo_id, accion, estado_anterior, estado_nuevo, actor_id, detalle)
  values (p_objeto, p_reclamo, p_accion, p_antes, p_despues, p_actor, p_detalle);
$$;

create or replace function exigir_sesion() returns void language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null or not exists (select 1 from perfiles where id = auth.uid()) then
    raise exception 'Inicia sesión para continuar.';
  end if;
end $$;

create or replace function exigir_activo() returns void language plpgsql security definer set search_path = public as $$
begin
  perform exigir_sesion();
  if exists (select 1 from perfiles where id = auth.uid() and bloqueado) then
    raise exception 'Tu cuenta está bloqueada.';
  end if;
end $$;

create or replace function exigir_staff() returns void language plpgsql security definer set search_path = public as $$
begin
  if not es_staff() then
    raise exception 'Solo un funcionario o administrador puede hacer esto.';
  end if;
end $$;

create or replace function exigir_admin() returns void language plpgsql security definer set search_path = public as $$
begin
  if not es_admin() then
    raise exception 'Solo un administrador puede hacer esto.';
  end if;
end $$;

create or replace function generar_codigo() returns text language plpgsql as $$
declare
  alfabeto constant text := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';  -- sin 0, O, 1, I (RN-05)
  bytes bytea := decode(replace(gen_random_uuid()::text, '-', ''), 'hex');
  codigo text := '';
  i int;
begin
  for i in 0..5 loop
    codigo := codigo || substr(alfabeto, (get_byte(bytes, i) % 32) + 1, 1);
  end loop;
  return codigo;
end $$;

-- Vencimientos evaluados al consultar (RN-10, RN-11, RN-14, EN-04).
create or replace function limpiar_estados() returns void language plpgsql security definer set search_path = public as $$
declare r record;
begin
  for r in with u as (update reclamos set estado = 'vencido'
                      where estado = 'activo' and vence_en < now() returning id, objeto_id)
           select * from u loop
    perform auditar('reclamo_vencido', null, r.objeto_id, r.id, 'activo', 'vencido');
  end loop;
  for r in with u as (update objetos set estado = 'RECHAZADO', motivo = 'no llegó'
                      where estado = 'PENDIENTE_RECEPCION' and creado_en < now() - interval '7 days' returning id)
           select * from u loop
    perform auditar('publicacion_rechazada_auto', null, r.id, null, 'PENDIENTE_RECEPCION', 'RECHAZADO', 'no llegó');
  end loop;
  for r in with u as (update objetos set estado = 'ARCHIVADO'
                      where estado = 'EN_CUSTODIA' and recibido_en < now() - interval '60 days' returning id)
           select * from u loop
    perform auditar('objeto_archivado', null, r.id, null, 'EN_CUSTODIA', 'ARCHIVADO');
  end loop;
end $$;

-- ---------------------------------------------------------------- lecturas
create or replace function puntos_activos() returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform exigir_sesion();
  return coalesce((select jsonb_agg(to_jsonb(p) order by p.nombre) from puntos_entrega p where p.activo), '[]'::jsonb);
end $$;

create or replace function catalogo(p_categoria text default null, p_punto uuid default null, p_texto text default '')
returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform exigir_sesion();
  perform limpiar_estados();
  -- Nunca toca objetos_privado: el detalle oculto no sale por aquí (CA-04).
  return coalesce((
    select jsonb_agg(to_jsonb(t) order by t.recibido_en desc)
    from (
      select o.id, o.categoria, o.descripcion_publica, o.lugar_hallazgo, o.fecha_hallazgo, o.foto_url,
             o.recibido_en, o.publicado_por, o.punto_id, p.nombre as punto, p.ubicacion, p.horario
      from objetos o join puntos_entrega p on p.id = o.punto_id
      where o.estado = 'EN_CUSTODIA'
        and (coalesce(p_categoria, '') = '' or o.categoria = p_categoria)
        and (p_punto is null or o.punto_id = p_punto)
        and (trim(coalesce(p_texto, '')) = ''
             or o.descripcion_publica ilike '%' || trim(p_texto) || '%'
             or o.lugar_hallazgo ilike '%' || trim(p_texto) || '%')
    ) t), '[]'::jsonb);
end $$;

create or replace function mis_publicaciones() returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform exigir_sesion();
  perform limpiar_estados();
  return coalesce((
    select jsonb_agg(to_jsonb(t) order by t.creado_en desc)
    from (select o.id, o.categoria, o.descripcion_publica, o.lugar_hallazgo, o.fecha_hallazgo, o.foto_url,
                 o.estado, o.motivo, o.creado_en, p.nombre as punto
          from objetos o join puntos_entrega p on p.id = o.punto_id
          where o.publicado_por = auth.uid()) t), '[]'::jsonb);
end $$;

create or replace function pendientes() returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform exigir_staff();
  perform limpiar_estados();
  return coalesce((
    select jsonb_agg(to_jsonb(t) order by t.creado_en)
    from (select o.id, o.categoria, o.descripcion_publica, o.lugar_hallazgo, o.fecha_hallazgo, o.foto_url,
                 o.estado, o.creado_en, p.nombre as punto
          from objetos o join puntos_entrega p on p.id = o.punto_id
          where o.estado = 'PENDIENTE_RECEPCION') t), '[]'::jsonb);
end $$;

create or replace function mis_reclamos() returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform exigir_sesion();
  perform limpiar_estados();
  return coalesce((
    select jsonb_agg(to_jsonb(t) order by t.creado_en desc)
    from (select r.id, r.objeto_id, r.descripcion, r.codigo, r.vence_en, r.estado, r.motivo, r.creado_en,
                 o.descripcion_publica, o.categoria, o.foto_url, o.estado as estado_objeto,
                 p.nombre as punto, p.ubicacion, p.horario
          from reclamos r join objetos o on o.id = r.objeto_id join puntos_entrega p on p.id = o.punto_id
          where r.reclamante_id = auth.uid()) t), '[]'::jsonb);
end $$;

create or replace function bitacora(p_accion text default '') returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform exigir_staff();
  return coalesce((
    select jsonb_agg(to_jsonb(t) order by t.id desc)
    from (select a.id, a.accion, a.estado_anterior, a.estado_nuevo, a.detalle, a.creado_en, u.nombre as actor
          from auditoria a left join perfiles u on u.id = a.actor_id
          where a.accion ilike '%' || trim(coalesce(p_accion, '')) || '%'
          order by a.id desc limit 100) t), '[]'::jsonb);
end $$;

create or replace function usuarios() returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform exigir_admin();
  return coalesce((select jsonb_agg(to_jsonb(u) order by u.creado_en)
                   from (select id, email, nombre, rol, bloqueado, creado_en from perfiles) u), '[]'::jsonb);
end $$;

create or replace function puntos_todos() returns jsonb language plpgsql security definer set search_path = public as $$
begin
  perform exigir_admin();
  return coalesce((
    select jsonb_agg(to_jsonb(t) order by t.activo desc, t.nombre)
    from (select p.*, (select count(*) from objetos o where o.punto_id = p.id and o.estado = 'EN_CUSTODIA') as en_custodia
          from puntos_entrega p) t), '[]'::jsonb);
end $$;

-- ---------------------------------------------------------------- publicar y recibir
create or replace function publicar_objeto(
  p_categoria text, p_descripcion text, p_lugar text, p_fecha timestamptz, p_punto uuid, p_foto text default null
) returns void language plpgsql security definer set search_path = public as $$
declare
  v_desc text := trim(coalesce(p_descripcion, ''));
  v_lugar text := trim(coalesce(p_lugar, ''));
  v_foto text := nullif(trim(coalesce(p_foto, '')), '');
  v_id uuid;
begin
  perform exigir_sesion();
  if p_categoria is null or p_categoria not in
     ('Electrónicos', 'Documentos y tarjetas', 'Llaves', 'Ropa y accesorios', 'Útiles y libros', 'Otros') then
    raise exception 'Elige una categoría.';
  end if;
  if v_desc = '' or char_length(v_desc) > 280 then
    raise exception 'La descripción pública es obligatoria (máximo 280 caracteres).';
  end if;
  if v_lugar = '' then raise exception 'Indica dónde lo encontraste.'; end if;
  if p_punto is null or not exists (select 1 from puntos_entrega where id = p_punto and activo) then
    raise exception 'Elige el punto de entrega.';
  end if;
  if p_categoria = 'Documentos y tarjetas' then
    v_foto := null;  -- PU-03: en documentos no se muestra foto
  elsif v_foto is not null and (v_foto !~* '^https?://' or char_length(v_foto) > 500) then
    raise exception 'El enlace de la foto debe empezar con http:// o https:// (máximo 500 caracteres).';
  end if;
  if p_fecha is null then raise exception 'Indica cuándo lo encontraste.'; end if;
  if p_fecha > now() + interval '10 minutes' then
    raise exception 'La fecha del hallazgo no puede ser futura.';
  end if;
  perform exigir_activo();
  insert into objetos (categoria, descripcion_publica, lugar_hallazgo, fecha_hallazgo, foto_url, publicado_por, punto_id)
  values (p_categoria, v_desc, v_lugar, least(p_fecha, now()), v_foto, auth.uid(), p_punto)
  returning id into v_id;
  perform auditar('publicacion_creada', auth.uid(), v_id, null, null, 'PENDIENTE_RECEPCION');
end $$;

create or replace function cancelar_publicacion(p_id uuid) returns void language plpgsql security definer set search_path = public as $$
declare o objetos;
begin
  perform exigir_sesion();
  select * into o from objetos where id = p_id and publicado_por = auth.uid() for update;
  if not found or o.estado <> 'PENDIENTE_RECEPCION' then
    raise exception 'Solo puedes cancelar publicaciones pendientes de recepción.';
  end if;
  update objetos set estado = 'RECHAZADO', motivo = 'cancelada por el hallador' where id = p_id;
  perform auditar('publicacion_cancelada', auth.uid(), p_id, null, 'PENDIENTE_RECEPCION', 'RECHAZADO');
end $$;

create or replace function confirmar_recepcion(p_id uuid, p_detalle text, p_notas text default null)
returns void language plpgsql security definer set search_path = public as $$
declare o objetos;
begin
  if trim(coalesce(p_detalle, '')) = '' then
    raise exception 'Registra al menos un detalle oculto de verificación.';
  end if;
  perform exigir_staff();
  select * into o from objetos where id = p_id for update;
  if not found or o.estado <> 'PENDIENTE_RECEPCION' then
    raise exception 'La publicación ya no está pendiente de recepción.';
  end if;
  update objetos set estado = 'EN_CUSTODIA', recibido_por = auth.uid(), recibido_en = now() where id = p_id;
  insert into objetos_privado (objeto_id, detalle_oculto, notas_internas)
  values (p_id, trim(p_detalle), nullif(trim(coalesce(p_notas, '')), ''))
  on conflict (objeto_id) do update set detalle_oculto = excluded.detalle_oculto, notas_internas = excluded.notas_internas;
  perform auditar('recepcion_confirmada', auth.uid(), p_id, null, 'PENDIENTE_RECEPCION', 'EN_CUSTODIA');
end $$;

create or replace function rechazar_publicacion(p_id uuid, p_motivo text) returns void
language plpgsql security definer set search_path = public as $$
declare o objetos;
begin
  if trim(coalesce(p_motivo, '')) = '' then raise exception 'El motivo es obligatorio.'; end if;
  perform exigir_staff();
  select * into o from objetos where id = p_id for update;
  if not found or o.estado <> 'PENDIENTE_RECEPCION' then
    raise exception 'La publicación ya no está pendiente de recepción.';
  end if;
  update objetos set estado = 'RECHAZADO', motivo = trim(p_motivo) where id = p_id;
  perform auditar('recepcion_rechazada', auth.uid(), p_id, null, 'PENDIENTE_RECEPCION', 'RECHAZADO', trim(p_motivo));
end $$;

-- ---------------------------------------------------------------- reclamos
create or replace function crear_reclamo(p_objeto uuid, p_descripcion text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_desc text := trim(coalesce(p_descripcion, ''));
  u perfiles;
  o objetos;
  v_codigo text;
  v_vence timestamptz := now() + interval '48 hours';
  v_id uuid;
  intento int := 0;
begin
  if char_length(v_desc) < 20 then
    raise exception 'Describe el objeto con al menos 20 caracteres.';
  end if;
  perform exigir_sesion();
  perform limpiar_estados();
  select * into u from perfiles where id = auth.uid() for update;  -- serializa los reclamos de un mismo usuario
  if u.bloqueado then raise exception 'Tu cuenta está bloqueada.'; end if;
  if u.rol <> 'usuario' then
    raise exception 'Los funcionarios no pueden reclamar con su cuenta de funcionario.';
  end if;
  select * into o from objetos where id = p_objeto;
  if not found or o.estado <> 'EN_CUSTODIA' then raise exception 'El objeto ya no está en custodia.'; end if;
  if o.publicado_por = u.id then raise exception 'No puedes reclamar un objeto que tú publicaste.'; end if;
  if (select count(*) from reclamos where reclamante_id = u.id and estado = 'activo') >= 3 then
    raise exception 'Ya tienes 3 reclamos activos.';
  end if;
  loop
    v_codigo := generar_codigo();
    begin
      insert into reclamos (objeto_id, reclamante_id, descripcion, codigo, vence_en)
      values (p_objeto, u.id, v_desc, v_codigo, v_vence) returning id into v_id;
      exit;
    exception when unique_violation then
      if exists (select 1 from reclamos where objeto_id = p_objeto and reclamante_id = u.id and estado = 'activo') then
        raise exception 'Ya tienes un reclamo activo sobre este objeto.';
      end if;
      intento := intento + 1;  -- el código chocó con otro activo: se genera otro
      if intento > 5 then raise exception 'No se pudo generar el código. Inténtalo de nuevo.'; end if;
    end;
  end loop;
  perform auditar('reclamo_creado', u.id, p_objeto, v_id, null, 'activo');
  return jsonb_build_object('id', v_id, 'codigo', v_codigo, 'vence_en', v_vence);
end $$;

create or replace function cancelar_reclamo(p_id uuid) returns void language plpgsql security definer set search_path = public as $$
declare r reclamos;
begin
  perform exigir_sesion();
  select * into r from reclamos where id = p_id and reclamante_id = auth.uid() for update;
  if not found or r.estado <> 'activo' then raise exception 'Solo puedes cancelar reclamos activos.'; end if;
  update reclamos set estado = 'cancelado' where id = p_id;
  perform auditar('reclamo_cancelado', auth.uid(), r.objeto_id, p_id, 'activo', 'cancelado');
end $$;

-- ---------------------------------------------------------------- entrega
create or replace function buscar_codigo(p_codigo text) returns jsonb language plpgsql security definer set search_path = public as $$
declare t jsonb;
begin
  perform exigir_staff();
  perform limpiar_estados();
  select to_jsonb(x) into t
  from (select r.*, u.nombre as reclamante, u.email as reclamante_email, o.categoria, o.foto_url,
               o.descripcion_publica, o.estado as estado_objeto, p.nombre as punto, op.detalle_oculto
        from reclamos r
        join perfiles u on u.id = r.reclamante_id
        join objetos o on o.id = r.objeto_id
        join puntos_entrega p on p.id = o.punto_id
        left join objetos_privado op on op.objeto_id = o.id
        where r.codigo = upper(trim(coalesce(p_codigo, '')))
        order by r.creado_en desc limit 1) x;
  if t is null then raise exception 'El código no existe.'; end if;
  case t ->> 'estado'
    when 'entregado' then raise exception 'Este código ya se usó: el objeto ya fue entregado.';
    when 'vencido' then raise exception 'El código venció. El usuario debe reclamar de nuevo.';
    when 'activo' then null;
    else raise exception 'El reclamo está en estado «%».', t ->> 'estado';
  end case;
  if t ->> 'estado_objeto' <> 'EN_CUSTODIA' then raise exception 'El objeto no está en custodia.'; end if;
  return t;
end $$;

create or replace function entregar(p_reclamo uuid, p_identidad boolean) returns void
language plpgsql security definer set search_path = public as $$
declare r reclamos; o objetos; otro record;
begin
  if not coalesce(p_identidad, false) then
    raise exception 'Debes confirmar que verificaste el carné o DNI.';
  end if;
  perform exigir_staff();
  select * into r from reclamos where id = p_reclamo for update;  -- la segunda llamada simultánea espera y falla
  if not found or r.estado <> 'activo' or r.vence_en < now() then raise exception 'El reclamo ya no está activo.'; end if;
  select * into o from objetos where id = r.objeto_id for update;
  if o.estado <> 'EN_CUSTODIA' then raise exception 'El objeto no está en custodia.'; end if;
  update reclamos set estado = 'entregado', resuelto_por = auth.uid(), resuelto_en = now() where id = p_reclamo;
  update objetos set estado = 'ENTREGADO' where id = o.id;
  perform auditar('objeto_entregado', auth.uid(), o.id, p_reclamo, 'EN_CUSTODIA', 'ENTREGADO',
                  'entregado a usuario ' || r.reclamante_id || '; identidad verificada');
  for otro in update reclamos set estado = 'rechazado', motivo = 'objeto entregado',
                                  resuelto_por = auth.uid(), resuelto_en = now()
              where objeto_id = o.id and estado = 'activo' and id <> p_reclamo returning id loop  -- RN-03
    perform auditar('reclamo_rechazado', auth.uid(), o.id, otro.id, 'activo', 'rechazado', 'objeto entregado');
  end loop;
end $$;

create or replace function rechazar_reclamo(p_id uuid, p_motivo text) returns void
language plpgsql security definer set search_path = public as $$
declare r reclamos;
begin
  if trim(coalesce(p_motivo, '')) = '' then raise exception 'El motivo es obligatorio.'; end if;
  perform exigir_staff();
  select * into r from reclamos where id = p_id for update;
  if not found or r.estado <> 'activo' then raise exception 'El reclamo ya no está activo.'; end if;
  update reclamos set estado = 'rechazado', motivo = trim(p_motivo), resuelto_por = auth.uid(), resuelto_en = now()
  where id = p_id;
  perform auditar('reclamo_rechazado', auth.uid(), r.objeto_id, p_id, 'activo', 'rechazado', trim(p_motivo));
end $$;

-- ---------------------------------------------------------------- administración
create or replace function cambiar_rol(p_usuario uuid, p_rol text) returns void
language plpgsql security definer set search_path = public as $$
declare v_antes text;
begin
  if p_rol is null or p_rol not in ('usuario', 'funcionario', 'admin') then raise exception 'Rol inválido.'; end if;
  perform exigir_admin();
  if p_usuario = auth.uid() then raise exception 'No puedes cambiar tu propio rol.'; end if;
  select rol into v_antes from perfiles where id = p_usuario for update;
  if not found then raise exception 'El usuario no existe.'; end if;
  update perfiles set rol = p_rol where id = p_usuario;
  perform auditar('rol_cambiado', auth.uid(), null, null, v_antes, p_rol, 'usuario ' || p_usuario);
end $$;

create or replace function bloquear(p_usuario uuid, p_bloqueado boolean) returns void
language plpgsql security definer set search_path = public as $$
declare r record;
begin
  perform exigir_admin();
  if p_usuario = auth.uid() then raise exception 'No puedes bloquearte a ti mismo.'; end if;
  update perfiles set bloqueado = p_bloqueado where id = p_usuario;
  if not found then raise exception 'El usuario no existe.'; end if;
  if p_bloqueado then  -- los reclamos activos se cancelan
    for r in update reclamos set estado = 'cancelado' where reclamante_id = p_usuario and estado = 'activo'
             returning id, objeto_id loop
      perform auditar('reclamo_cancelado', auth.uid(), r.objeto_id, r.id, 'activo', 'cancelado', 'usuario bloqueado');
    end loop;
  end if;
  perform auditar(case when p_bloqueado then 'usuario_bloqueado' else 'usuario_desbloqueado' end,
                  auth.uid(), null, null, null, null, 'usuario ' || p_usuario);
end $$;

create or replace function guardar_punto(p_nombre text, p_ubicacion text, p_horario text, p_id uuid default null)
returns void language plpgsql security definer set search_path = public as $$
declare
  v_nombre text := trim(coalesce(p_nombre, ''));
  v_ubic text := trim(coalesce(p_ubicacion, ''));
  v_hor text := trim(coalesce(p_horario, ''));
  v_nuevo uuid;
begin
  if v_nombre = '' or char_length(v_nombre) > 60 then
    raise exception 'El nombre es obligatorio (máximo 60 caracteres).';
  end if;
  if v_ubic = '' or v_hor = '' then raise exception 'Indica la ubicación y el horario de atención.'; end if;
  perform exigir_admin();
  if exists (select 1 from puntos_entrega where lower(nombre) = lower(v_nombre) and id is distinct from p_id) then
    raise exception 'Ya existe un punto de entrega con ese nombre.';
  end if;
  if p_id is null then
    insert into puntos_entrega (nombre, ubicacion, horario) values (v_nombre, v_ubic, v_hor) returning id into v_nuevo;
    perform auditar('punto_creado', auth.uid(), null, null, null, null, 'punto ' || v_nuevo || ': ' || v_nombre);
  else
    update puntos_entrega set nombre = v_nombre, ubicacion = v_ubic, horario = v_hor where id = p_id;
    if not found then raise exception 'El punto no existe.'; end if;
    perform auditar('punto_editado', auth.uid(), null, null, null, null, 'punto ' || p_id || ': ' || v_nombre);
  end if;
end $$;

create or replace function activar_punto(p_id uuid, p_activo boolean) returns void
language plpgsql security definer set search_path = public as $$
begin
  perform exigir_admin();
  if not p_activo and not exists (select 1 from puntos_entrega where activo and id <> p_id) then
    raise exception 'Debe quedar al menos un punto de entrega activo.';
  end if;
  update puntos_entrega set activo = p_activo where id = p_id;
  if not found then raise exception 'El punto no existe.'; end if;
  perform auditar(case when p_activo then 'punto_activado' else 'punto_desactivado' end,
                  auth.uid(), null, null, null, null, 'punto ' || p_id);
end $$;

-- ---------------------------------------------------------------- permisos de ejecución
-- Por defecto Postgres deja ejecutar todo a PUBLIC; aquí solo los usuarios con sesión pueden llamar a las funciones públicas.
do $$
declare f record;
begin
  for f in select p.oid::regprocedure as firma, p.proname
           from pg_proc p join pg_namespace n on n.oid = p.pronamespace
           where n.nspname = 'public'
             and p.proname in ('puntos_activos', 'catalogo', 'mis_publicaciones', 'pendientes', 'mis_reclamos',
                               'bitacora', 'usuarios', 'puntos_todos', 'publicar_objeto', 'cancelar_publicacion',
                               'confirmar_recepcion', 'rechazar_publicacion', 'crear_reclamo', 'cancelar_reclamo',
                               'buscar_codigo', 'entregar', 'rechazar_reclamo', 'cambiar_rol', 'bloquear',
                               'guardar_punto', 'activar_punto')
  loop
    execute format('revoke all on function %s from public, anon', f.firma);
    execute format('grant execute on function %s to authenticated', f.firma);
  end loop;
  -- Funciones internas: nadie las llama desde la API.
  for f in select p.oid::regprocedure as firma
           from pg_proc p join pg_namespace n on n.oid = p.pronamespace
           where n.nspname = 'public'
             and p.proname in ('auditar', 'exigir_sesion', 'exigir_activo', 'exigir_staff', 'exigir_admin',
                               'generar_codigo', 'limpiar_estados', 'validar_dominio_institucional', 'crear_perfil',
                               'auditoria_inmutable')
  loop
    execute format('revoke all on function %s from public, anon, authenticated', f.firma);
  end loop;
end $$;

notify pgrst, 'reload schema';
