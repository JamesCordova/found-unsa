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
