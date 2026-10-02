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
python scripts/create_user.py --username admin --email admin@local.test --role administrador --display-name "Administrador" --puesto-id ID_PUESTO_ACTIVO
```

El inicio de sesión acepta usuario o correo. `POST /api/v1/auth/login` crea un token de sesión opaco, cuyo hash se almacena en `user_sessions`; `POST /api/v1/auth/logout` revoca el token. Las contraseñas usan Argon2id con sal y el perfil sensible usa AES-256-GCM. Las rutas protegidas dependen de la sesión en servidor.

Los roles disponibles son `administrador` y `consulta`. El administrador puede usar `/api/v1/admin/users`, `/api/v1/admin/organizations` y `PUT /api/v1/admin/services/{code}`. El rol consulta solo puede leer `/api/v1/services` y `/api/v1/admin/organizations`; el servidor rechaza las operaciones administrativas con `403`.

## Directorio organizacional

La jerarquía es `empresas → areas → departamentos → secciones → puestos → users`. Los endpoints `GET /api/v1/empresas`, `GET /api/v1/areas`, `GET /api/v1/departamentos`, `GET /api/v1/secciones` y `GET /api/v1/puestos` permiten consultar la estructura a los roles autenticados. Las operaciones `POST`, `PATCH` y `DELETE` de esas rutas requieren `administrador`. `DELETE` es una baja lógica.

Los códigos subordinados son únicos dentro de su padre. Las claves foráneas son obligatorias. El servicio rechaza padres inactivos, desactivación con hijos activos y desactivación de puestos con usuarios activos. Las sesiones de usuarios dados de baja se revocan.

Los usuarios se administran con `GET/POST/PATCH/DELETE /api/v1/usuarios`. El `GET` es lectura segura para ambos roles; `POST/PATCH/DELETE` requiere `administrador`. Las respuestas nunca incluyen `password_hash` ni datos secretos.

## Servicios de nivel 1 y nivel 2

`GET /api/v1/services` admite búsqueda (`search`), nivel 1, estado, clase, criticidad, tipo y paginación (`page`, `page_size`). `GET /api/v1/services/{code}` devuelve la ficha completa con los campos del Excel, nivel 1, trazabilidad y asignación responsable. `POST/PATCH/DELETE /api/v1/services` requiere `administrador`; `DELETE` es baja lógica.

Los niveles 1 se consultan y mantienen en `/api/v1/services/level-1`. Cada servicio de nivel 2 conserva `level_1_code` como referencia obligatoria y los códigos son únicos. Los catálogos controlados se consultan en `/api/v1/services/catalog-options` y se mantienen en `/api/v1/services/catalog/classes`, `/criticalities` y `/types`.

Las altas exigen clase, criticidad, tipo y sección responsable activos. El usuario responsable es opcional y se valida contra la sección. La importación no inventa asignaciones; el script de demostración crea una estructura `DEMO` independiente y asigna tres servicios válidos.

Un usuario desactivado no puede iniciar sesión y sus sesiones activas se revocan inmediatamente. Para crear cuentas demo sin versionar secretos:

```bash
python scripts/create_demo_users.py
```
