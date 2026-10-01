# Catálogo de Servicios

Repositorio de la parte práctica del examen parcial 2.

## Estructura

- `frontend/`: aplicación web cliente basada en React y Vite.
- `backend/`: API Python organizada con MVC por capas.
- `backend/db/`: esquema PostgreSQL y controles de importación.
- `src/`: código fuente compartido o transversal al proyecto.
- `tests/`: pruebas automatizadas del frontend, backend y flujos de integración.
- `scripts/`: utilidades de desarrollo, validación y generación de datos.
- `data/CatalogoServicios.xlsx`: plantilla inicial del catálogo de servicios.
- `docs/`: resolución, contexto, prompts y evidencias del proyecto.

## Requisitos

- Docker Engine 24 o superior.
- Docker Compose v2.20 o superior.
- Para ejecutar únicamente el frontend: Node.js 22 o superior y npm.

## Puesta en marcha con PostgreSQL

1. Copiar `.env.example` como `.env` y completar los valores necesarios.
2. Ejecutar `docker compose up --build -d`.
3. Revisar el estado con `docker compose ps`.
4. Abrir el frontend en `http://localhost:5173`.
5. Consultar la API en `http://localhost:8000` y su documentación en `http://localhost:8000/docs`.
6. Conectarse a PostgreSQL en `localhost:5432`, base `catalogo_servicios`, usuario `catalogo`.

El servicio `db` persiste sus datos en el volumen Docker `postgres_data`. El backend espera el healthcheck de PostgreSQL antes de iniciar, ejecuta el importador del Excel original y luego expone la API. El frontend espera el healthcheck del backend.

## Autenticación local

Crear el primer usuario después de levantar la base:

```powershell
docker compose exec backend python scripts/create_user.py --username admin --email admin@local.test --display-name "Administrador"
```

La aplicación valida usuario o correo contra PostgreSQL. Las contraseñas se almacenan con Argon2id y sal; nunca se guardan en texto plano ni se cifran de forma reversible. Los datos de perfil recuperables se cifran con AES-256-GCM usando `APP_ENCRYPTION_KEY`.

Endpoints:

- `POST /api/v1/auth/login`: inicia sesión.
- `POST /api/v1/auth/logout`: revoca la sesión actual.
- `GET /api/v1/auth/me`: devuelve el usuario autenticado.
- `GET /api/v1/services`: ruta protegida; requiere `Authorization: Bearer <token>`.

La autorización se valida en el backend mediante la sesión almacenada y revocable en PostgreSQL. Ocultar controles del frontend no concede permisos.

## Importador idempotente

El comando ejecutable es:

```powershell
python -m backend.app.importer --input data/CatalogoServicios.xlsx
```

Para validar el archivo sin escribir en PostgreSQL:

```powershell
python -m backend.app.importer --dry-run
```

En Docker, el backend ejecuta automáticamente el importador al arrancar. La primera ejecución esperada informa 46 servicios creados; una repetición sobre el mismo archivo informa 46 sin cambios y no duplica registros. El resumen incluye `created`, `updated`, `unchanged`, `omitted`, `observed`, `level_1` y `level_2`.

Para repetirlo manualmente dentro del contenedor:

```powershell
docker compose exec backend python -m backend.app.importer --input /app/data/CatalogoServicios.xlsx
```

Para consultar el último resumen y sus observaciones:

```powershell
docker compose exec db psql -U catalogo -d catalogo_servicios -c "SELECT id, status, created_count, updated_count, unchanged_count, omitted_count, observed_count, level_1_count, level_2_count FROM import_runs ORDER BY id DESC LIMIT 1;"
docker compose exec db psql -U catalogo -d catalogo_servicios -c "SELECT reason, code, source_range, message FROM import_observations WHERE import_run_id = (SELECT id FROM import_runs ORDER BY id DESC LIMIT 1) ORDER BY id;"
```

## Operación diaria

Ver logs:

```powershell
docker compose logs -f db
docker compose logs -f backend
docker compose logs -f frontend
```

Apagado normal, conservando contenedores y datos:

```powershell
docker compose stop
```

Reinicio normal:

```powershell
docker compose start
```

También se puede detener y retirar contenedores sin eliminar el volumen:

```powershell
docker compose down
```

## Reinicio destructivo de datos de prueba

Este procedimiento elimina el volumen `postgres_data`, la base y todos sus datos. Úsalo únicamente para reconstruir el catálogo desde los scripts SQL:

```powershell
docker compose down -v
docker compose up --build -d
```

El esquema `backend/db/00_schema.sql` se ejecuta cuando PostgreSQL inicia con un volumen vacío. La carga de datos siempre la realiza el importador y queda registrada en `import_runs` e `import_observations`.

La implementación del backend se mantiene separada por configuración, modelos, repositorios, servicios, controladores, rutas y esquemas para facilitar las pruebas y el mantenimiento.
