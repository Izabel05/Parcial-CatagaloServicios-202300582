# Catálogo de Servicios

Repositorio de la parte práctica del examen parcial 2.

El diseño de la ampliación Service Desk se documenta en
[`docs/MODELO.md`](docs/MODELO.md): fuentes originales, atributos y propuesta
CMDB. Ese documento distingue el esquema existente de las tablas aún propuestas
y registra las limitaciones de la jerarquía disponible.

La CMDB implementada se opera desde la pestaña **CMDB**. Consulta
[`docs/CMDB.md`](docs/CMDB.md) para migraciones, generación reproducible de
5,000 dispositivos, API, relaciones y pruebas aisladas.

La pestaña **Service Desk** incorpora tickets, colas y permisos. Sigue
[`docs/SERVICE_DESK.md`](docs/SERVICE_DESK.md) para cuentas de demostración,
roles combinados, toma de tickets, adjuntos y pruebas.

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

## Instalación en Fedora

La aplicación principal se ejecuta dentro de Docker; no es necesario instalar
PostgreSQL, Python ni Node.js en el equipo anfitrión. En una versión mantenida
de Fedora instala Docker Engine y el complemento Compose desde el repositorio
oficial de Docker:

```bash
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager addrepo --from-repofile https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
newgrp docker
docker run hello-world
docker compose version
```

Si el repositorio Fedora tiene una instalación anterior incompatible, revisa
los paquetes Docker existentes antes de instalar los oficiales. La guía
oficial es [Instalar Docker Engine en Fedora](https://docs.docker.com/engine/install/fedora/).

Clona y configura el proyecto:

```bash
git clone https://github.com/Izabel05/Parcial-CatagaloServicios-202300582.git
cd Parcial-CatagaloServicios-202300582
cp .env.example .env
sed -i "s|REEMPLAZAR_CON_UNA_CLAVE_BASE64_URLSAFE_DE_32_BYTES|$(openssl rand -base64 32 | tr -d '\\n')|" .env
docker compose up --build -d
docker compose ps
```

Abre `http://localhost:5173`, la API en `http://localhost:8000` y Swagger en
`http://localhost:8000/docs`. Crea las cuentas demo y conserva las contraseñas
que se imprimen únicamente en la terminal:

```bash
docker compose exec backend python scripts/create_demo_users.py
```

Para detener y reiniciar normalmente:

```bash
docker compose stop
docker compose start
```

Para consultar logs:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

No uses `docker compose down -v` salvo que quieras eliminar los datos de
prueba. `docker compose down` conserva el volumen `postgres_data`.

## Puesta en marcha con PostgreSQL

1. Copiar `.env.example` como `.env` y completar los valores necesarios.
2. Ejecutar `docker compose up --build -d`.
3. Revisar el estado con `docker compose ps`.
4. Abrir el frontend en `http://localhost:5173`.
5. Consultar la API en `http://localhost:8000` y su documentación en `http://localhost:8000/docs`.
6. Conectarse a PostgreSQL en `localhost:5432`, base `catalogo_servicios`, usuario `catalogo`.

El servicio `db` persiste sus datos en el volumen Docker `postgres_data`. El backend espera el healthcheck de PostgreSQL antes de iniciar, ejecuta el importador del Excel original y luego expone la API. El frontend espera el healthcheck del backend.

## Autenticación local

Generar la clave AES únicamente en el entorno local y guardarla en `.env`:

```powershell
python -c "import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

No usar el marcador de `.env.example` ni guardar la clave generada en Git.

Crear el primer usuario después de levantar la base:

```powershell
docker compose exec db psql -U catalogo -d catalogo_servicios -c "SELECT id, codigo, nombre FROM puestos WHERE activo ORDER BY id;"
docker compose exec backend python scripts/create_user.py --username admin --email admin@local.test --role administrador --display-name "Administrador" --puesto-id ID_PUESTO_ACTIVO
```

La aplicación valida usuario o correo contra PostgreSQL. Las contraseñas se almacenan con Argon2id y sal; nunca se guardan en texto plano ni se cifran de forma reversible. Los datos de perfil recuperables se cifran con AES-256-GCM usando `APP_ENCRYPTION_KEY`.

Endpoints:

- `POST /api/v1/auth/login`: inicia sesión.
- `POST /api/v1/auth/logout`: revoca la sesión actual.
- `GET /api/v1/auth/me`: devuelve el usuario autenticado.
- `GET /api/v1/services`: ruta protegida; requiere `Authorization: Bearer <token>`.
- `GET /api/v1/admin/users`: listado seguro de usuarios; solo `administrador`.
- `POST /api/v1/admin/users`: crea usuarios; solo `administrador`.
- `PATCH /api/v1/admin/users/{id}/status`: activa o desactiva usuarios; solo `administrador`.
- `PATCH /api/v1/admin/users/{id}/role`: cambia roles; solo `administrador`.
- `GET /api/v1/admin/organizations`: lectura para ambos roles.
- `POST/PATCH /api/v1/admin/organizations`: mantenimiento; solo `administrador`.
- `PUT /api/v1/admin/services/{code}`: mantenimiento del catálogo; solo `administrador`.

## Directorio organizacional

La jerarquía persistida es `Empresa → Área → Departamento → Sección → Puesto → Usuario`.
Las consultas de empresas, áreas, departamentos, secciones y puestos requieren autenticación y están disponibles para ambos roles. Las altas, modificaciones y bajas lógicas requieren `administrador`:

- `GET/POST/PATCH/DELETE /api/v1/empresas`
- `GET/POST/PATCH/DELETE /api/v1/areas`
- `GET/POST/PATCH/DELETE /api/v1/departamentos`
- `GET/POST/PATCH/DELETE /api/v1/secciones`
- `GET/POST/PATCH/DELETE /api/v1/puestos`
- `GET /api/v1/usuarios` permite lectura segura a ambos roles; `POST/PATCH/DELETE /api/v1/usuarios` requiere `administrador`.

Las entidades subordinadas usan códigos únicos dentro de su padre. Las claves foráneas son obligatorias y las asociaciones nuevas solo aceptan padres activos. `DELETE` no elimina filas: marca `activo=false` o `is_active=false`. No se permite desactivar una entidad con hijos activos; tampoco un puesto con usuarios activos. Por eso la desactivación se realiza de abajo hacia arriba y la reactivación de arriba hacia abajo.

## Servicios y catálogos

`/api/v1/services` devuelve resultados paginados y permite `search`, `level_1_code`, `active`, `service_class_id`, `criticality_id`, `service_type_id`, `page` y `page_size`. La búsqueda cubre código y nombre. `GET /api/v1/services/{code}` devuelve la ficha completa, incluyendo todos los campos importados, nivel 1, catálogos, trazabilidad y asignación responsable.

`GET /api/v1/services/catalog-options` entrega las opciones controladas para formularios. Los catálogos también se mantienen mediante `/api/v1/services/catalog/{classes|criticalities|types}`; las consultas son autenticadas y las modificaciones requieren `administrador`. El servidor valida referencias activas y `mínimo <= máximo`, conservando `NULL` cuando el dato está ausente.

Los servicios nuevos requieren nivel 1, clase, criticidad, tipo y sección responsable activos. El usuario responsable es opcional, pero si se informa debe estar activo y pertenecer a la sección seleccionada. Los 46 servicios importados pueden quedar sin asignación porque esas relaciones son datos nuevos del sistema. `scripts/create_demo_users.py` crea una jerarquía `DEMO` y asigna tres servicios importados a usuarios y sección válidos.

La autorización se valida en el backend mediante la sesión almacenada y revocable en PostgreSQL. Ocultar controles del frontend no concede permisos.

Roles:

- `administrador`: mantenimiento de usuarios, unidades organizativas y catálogo.
- `consulta`: lectura de servicios, estructura y datos públicos de usuarios; recibe `403` en operaciones administrativas.

Crear ambas cuentas de evaluación, sin guardar contraseñas en Git:

```powershell
docker compose exec backend python scripts/create_demo_users.py
```

El comando genera contraseñas temporales y las muestra solo una vez en la consola. También acepta `--admin-password` y `--consulta-password` para credenciales locales controladas.

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

Los siete procesos Service Desk ya tienen estados y reglas propios en el backend:
aprobaciones, evidencias de cambios, incidentes I0–I6, eventos E0–E3, problemas,
accesos y cumplimiento de solicitudes. Instrucciones y recorridos:
[docs/PROCESOS.md](docs/PROCESOS.md).

Service Desk separa **Portal del solicitante**, **Consola del agente** y
**Administración**. Las pestañas **FAQ** y **Tablero** incorporan autoservicio y
cantidades/tiempos con objetivos en minutos calendario. Consulte
[pantallas y cálculo de tiempos](docs/PANTALLAS_Y_TIEMPOS.md) para ámbitos,
pausas, reaperturas y objetivos por ciclo.

Para evaluar todos los roles y procesos con **37 tickets, siete colas y 5,000
dispositivos** ejecute `docker compose exec backend python scripts/prepare_demo.py`.
La carga es reproducible y no restablece tickets existentes. Claves, recorridos y
repetición: [DEMOSTRACION.md](docs/DEMOSTRACION.md).

La aceptación P01–P18 y las regresiones del parcial se ejecutan con
`bash scripts/run_acceptance.sh`, en una base separada. Matriz y formato de
evidencia: [PRUEBAS.md](docs/PRUEBAS.md).
