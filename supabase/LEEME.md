# Base de datos (Supabase)

## Instalar (una sola vez)

En el panel de tu proyecto: **SQL Editor → New query**, pega el contenido del archivo y pulsa **Run**. En este orden:

1. `migrations/001_esquema.sql` — tablas, restricciones, triggers y seguridad por fila (RLS).
2. `migrations/002_funciones.sql` — funciones de negocio (publicar, recibir, reclamar, entregar, administrar).
3. `seed.sql` — 4 cuentas de demostración, 2 puntos de entrega y 6 objetos de ejemplo.

Cada archivo se puede volver a ejecutar sin duplicar datos. Si Supabase muestra «Success. No rows returned», salió bien.

## Cuentas de demostración

Contraseña de las cuatro: `Demo#2026` (ya están confirmadas, sin correo de verificación).

| Correo | Rol |
| --- | --- |
| usuario@unsa.edu.pe | usuario |
| otro@unsa.edu.pe | usuario |
| funcionario@unsa.edu.pe | funcionario |
| admin@unsa.edu.pe | admin |

**Cámbialas o bórralas después de la evaluación**: el administrador de demostración tiene una contraseña conocida.

## Seguridad

- La app usa solo la **clave publicable** (`SUPABASE_KEY` en `.env`). Es pública por diseño: lo que protege los datos son las políticas RLS y las funciones, no el secreto de la clave.
- **Nunca** pongas la `service_role` ni la contraseña de la base en el proyecto ni en el chat.
- Las tablas solo se leen; toda escritura pasa por funciones que verifican el rol de quien llama.

## Correos de confirmación

Supabase confirma el correo al registrarse (Auth → Providers → Email → *Confirm email*). El servicio de correo gratuito tiene un límite bajo de envíos por hora: crea las cuentas que necesites antes de una demostración o configura tu propio servicio de correo (Auth → SMTP Settings).
