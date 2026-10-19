# Encontrado UNSA (Flet + Supabase)

App multiplataforma (Python + Flet) para devolver objetos perdidos del campus mediante un punto de custodia.
Datos y cuentas en Supabase (Postgres + Auth); las fotos son enlaces, no se guardan archivos.

## Preparar
1. Ejecuta en Supabase (SQL Editor) los archivos de `supabase/` en orden — ver [supabase/LEEME.md](supabase/LEEME.md).
2. Copia `.env.example` a `.env` y completa `SUPABASE_URL` y `SUPABASE_KEY` (clave publicable).
3. Instala:

       uv venv --python 3.11
       uv pip install -r requirements.txt

## Ejecutar
    .venv\Scripts\python main.py              # ventana de escritorio
    .venv\Scripts\flet run --web main.py      # en el navegador
    .venv\Scripts\flet run --android main.py  # en el celular, con la app Flet instalada (misma red Wi-Fi)

## Cuentas de demostración (contraseña `Demo#2026`)
usuario@ · otro@ (usuarios) · funcionario@ · admin@ + `unsa.edu.pe`. Con `DEMO_CLAVE` en `.env` el login muestra un acceso rápido.

## Recorrido
1. `usuario`: Publicar → llavero en «Portería principal».
2. `funcionario`: Recepción → confirmar con detalle oculto.
3. `otro`: Catálogo → Es mío → copiar el código en Mis reclamos.
4. `funcionario`: Entrega → código, marcar verificación de DNI → Entregar. Ver Bitácora.

## Estructura
    main.py                  punto de entrada
    supabase/                base de datos: migraciones SQL, datos de ejemplo e instrucciones
    app/datos/               cliente de Supabase (Auth + API REST) y funciones que usa la interfaz
    app/ui/
      aplicacion.py          sesión, navegación por rol, render y aviso de sin conexión
      tema.py componentes.py colores de estado, fuentes, tema; widgets reutilizables
      pantallas/             una pantalla por archivo
    _respaldo_sqlite/        primera versión con SQLite, archivada sin usar
