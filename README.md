# Encontrado UNSA (Flet)

App multiplataforma (Python + Flet) para devolver objetos perdidos del campus mediante un punto de custodia.
Persistencia local en SQLite (`encontrado.db`, se crea sola).

## Ejecutar
    uv venv --python 3.11 && uv pip install -r requirements.txt
    .venv\Scripts\python main.py            # ventana de escritorio
    .venv\Scripts\flet run --web main.py    # en el navegador
    .venv\Scripts\flet run --android main.py  # en el celular, con la app Flet instalada

## Cuentas de demostración (contraseña `1234`)
usuario@ · otro@ (usuarios) · funcionario@ · admin@ + `unsa.edu.pe`

## Recorrido
1. `usuario`: Publicar → llave en "Portería principal".
2. `funcionario`: Recepción → confirmar con detalle oculto.
3. `otro`: Catálogo → Es mío → copiar el código en Mis reclamos.
4. `funcionario`: Entrega → código, marcar verificación de DNI → Entregar. Ver Bitácora.

## Estructura
    main.py                  punto de entrada
    app/datos/               SQLite y reglas de negocio (una responsabilidad por archivo)
      config.py conexion.py esquema.py permisos.py auditoria.py vencimientos.py
      cuentas.py publicaciones.py catalogo.py reclamos.py entregas.py administracion.py
    app/ui/
      aplicacion.py          sesión, navegación por rol y render
      tema.py componentes.py colores de estado, fuentes, tema; widgets reutilizables
      pantallas/             una pantalla por archivo
