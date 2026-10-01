# Backend

API en Python con FastAPI y una arquitectura MVC por capas.

## Capas

- `config/`: configuración y variables de entorno.
- `models/`: modelos de dominio.
- `repositories/`: persistencia y acceso a datos.
- `services/`: reglas de negocio.
- `controllers/`: coordinación de casos de uso y respuestas HTTP.
- `routes/`: definición de endpoints.
- `schemas/`: contratos de entrada y salida.
- `views/`: serialización o representaciones para la respuesta.
- `db/`: esquema PostgreSQL y trazabilidad de importaciones.
- `app/importer/`: importador idempotente del Excel original.

## Ejecución local

```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

## Importación

Con PostgreSQL disponible y las dependencias instaladas:

```bash
python -m backend.app.importer --input data/CatalogoServicios.xlsx
```

El comando imprime un resumen de registros creados, actualizados, sin cambios, omitidos y observados. Repetirlo con el mismo archivo no duplica registros. `--dry-run` valida celdas combinadas, controles y observaciones sin escribir en la base.

## Autenticación

Crear usuarios locales desde el contenedor:

```bash
python scripts/create_user.py --username admin --email admin@local.test --display-name "Administrador"
```

El inicio de sesión acepta usuario o correo. `POST /api/v1/auth/login` crea un token de sesión opaco, cuyo hash se almacena en `user_sessions`; `POST /api/v1/auth/logout` revoca el token. Las contraseñas usan Argon2id con sal y el perfil sensible usa AES-256-GCM. Las rutas protegidas dependen de la sesión en servidor.
