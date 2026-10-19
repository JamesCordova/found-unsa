-- Encontrado UNSA · datos de demostración
-- Ejecutar DESPUÉS de 001 y 002. Es seguro volver a ejecutarlo: no duplica nada.
--
-- Crea 4 cuentas ya confirmadas (contraseña: Demo#2026), 2 puntos de entrega y 6 objetos de ejemplo
-- con imágenes de relleno (enlaces a placehold.co; no se guarda ningún archivo).
-- CAMBIA O BORRA estas cuentas después de la evaluación: el admin de demostración tiene una contraseña conocida.

do $$
declare
  rec record;
  v_id uuid;
begin
  for rec in select * from (values
      ('usuario@unsa.edu.pe', 'Ana Usuario', 'usuario'),
      ('otro@unsa.edu.pe', 'Luis Usuario', 'usuario'),
      ('funcionario@unsa.edu.pe', 'Rosa Portería', 'funcionario'),
      ('admin@unsa.edu.pe', 'Admin UNSA', 'admin')) as t(email, nombre, rol)
  loop
    select id into v_id from auth.users where email = rec.email;
    if v_id is null then
      v_id := gen_random_uuid();
      insert into auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
                              raw_app_meta_data, raw_user_meta_data, created_at, updated_at,
                              confirmation_token, recovery_token, email_change_token_new, email_change)
      values ('00000000-0000-0000-0000-000000000000', v_id, 'authenticated', 'authenticated', rec.email,
              extensions.crypt('Demo#2026', extensions.gen_salt('bf')), now(),
              '{"provider":"email","providers":["email"]}', jsonb_build_object('nombre', rec.nombre),
              now(), now(), '', '', '', '');
      insert into auth.identities (id, user_id, identity_data, provider, provider_id, last_sign_in_at, created_at, updated_at)
      values (gen_random_uuid(), v_id,
              jsonb_build_object('sub', v_id::text, 'email', rec.email, 'email_verified', true),
              'email', v_id::text, now(), now(), now());
    end if;
    update perfiles set rol = rec.rol, nombre = rec.nombre where id = v_id;  -- el trigger ya creó el perfil
  end loop;
end $$;

insert into puntos_entrega (nombre, ubicacion, horario)
select * from (values
  ('Portería principal', 'Ingreso por la Av. Independencia', 'Lun-Vie 7:00-19:00'),
  ('Secretaría de Ingeniería', 'Pabellón de Ingeniería, 1.er piso', 'Lun-Vie 8:00-16:00')) as v(nombre, ubicacion, horario)
where not exists (select 1 from puntos_entrega where lower(puntos_entrega.nombre) = lower(v.nombre));

do $$
declare
  rec record;
  v_autor uuid := (select id from perfiles where email = 'usuario@unsa.edu.pe');
  v_staff uuid := (select id from perfiles where email = 'funcionario@unsa.edu.pe');
  v_punto uuid;
  v_obj uuid;
  v_hallado timestamptz;
begin
  if exists (select 1 from objetos) or v_autor is null or v_staff is null then return; end if;
  for rec in select * from (values
    ('Llaves', 'Llavero con tres llaves y un pequeño peluche de zorro', 'Biblioteca central, 2.º piso', 1,
       'Portería principal', 'https://placehold.co/600x400/4f46e5/ffffff/png?text=Llavero',
       'El peluche tiene un parche azul en la oreja izquierda', 'EN_CUSTODIA'),
    ('Electrónicos', 'Audífonos inalámbricos negros con su estuche de carga', 'Pabellón de Ingeniería', 2,
       'Secretaría de Ingeniería', 'https://placehold.co/600x400/0f766e/ffffff/png?text=Aud%C3%ADfonos',
       'Estuche con una calcomanía de un rayo en la tapa', 'EN_CUSTODIA'),
    ('Ropa y accesorios', 'Casaca azul marino talla M con capucha', 'Comedor universitario', 3,
       'Portería principal', 'https://placehold.co/600x400/b45309/ffffff/png?text=Casaca',
       'Etiqueta cosida con las iniciales J.R.', 'EN_CUSTODIA'),
    ('Útiles y libros', 'Calculadora científica y un cuaderno cuadriculado', 'Aula 204', 5,
       'Secretaría de Ingeniería', 'https://placehold.co/600x400/be185d/ffffff/png?text=Calculadora',
       'Primera página del cuaderno con un dibujo de un cohete', 'EN_CUSTODIA'),
    ('Documentos y tarjetas', 'Carné universitario hallado en el patio central', 'Patio central', 1,
       'Portería principal', null,
       'Carrera impresa en el carné: Ingeniería de Sistemas', 'EN_CUSTODIA'),
    ('Otros', 'Paraguas negro grande con mango de madera', 'Entrada principal', 0,
       'Portería principal', 'https://placehold.co/600x400/475569/ffffff/png?text=Paraguas',
       null, 'PENDIENTE_RECEPCION')
  ) as t(categoria, descripcion, lugar, dias, punto, foto, oculto, estado)
  loop
    select id into v_punto from puntos_entrega where nombre = rec.punto;
    v_hallado := now() - make_interval(days => rec.dias, hours => 2);
    insert into objetos (categoria, descripcion_publica, lugar_hallazgo, fecha_hallazgo, estado, foto_url,
                         publicado_por, punto_id, recibido_por, recibido_en, creado_en)
    values (rec.categoria, rec.descripcion, rec.lugar, v_hallado, rec.estado, rec.foto, v_autor, v_punto,
            case when rec.estado = 'EN_CUSTODIA' then v_staff end,
            case when rec.estado = 'EN_CUSTODIA' then v_hallado + interval '3 hours' end,
            v_hallado)
    returning id into v_obj;
    perform auditar('publicacion_creada', v_autor, v_obj, null, null, 'PENDIENTE_RECEPCION');
    if rec.oculto is not null then
      insert into objetos_privado (objeto_id, detalle_oculto) values (v_obj, rec.oculto);
      perform auditar('recepcion_confirmada', v_staff, v_obj, null, 'PENDIENTE_RECEPCION', 'EN_CUSTODIA');
    end if;
  end loop;
end $$;
