# Resolución

## Objetivo

Construir un catálogo de servicios con un cliente web y una API organizada para facilitar la consulta y futura administración de los servicios.

## Decisiones iniciales

- Frontend: React con Vite y JavaScript.
- Backend: Python con FastAPI.
- Arquitectura: MVC por capas.
- Datos de desarrollo: `data/CatalogoServicios.xlsx`.
- Ejecución: Docker Compose.
- Persistencia: PostgreSQL con el volumen Docker `postgres_data`.

## Base de datos

La hoja `Servicios Externos` se importa desde `A5:L101` mediante `python -m backend.app.importer`. El archivo original permanece en `data/CatalogoServicios.xlsx` y el importador nunca lo guarda ni lo modifica.

### Reglas de importación y casos reales

1. **Celdas combinadas.** El importador construye un índice de rangos combinados y recupera el valor de la celda ancla únicamente dentro de ese rango. Una fila hija de `C5:C7`, por ejemplo, se registra como `MERGED_CONTINUATION` y no crea otro servicio.
2. **Conflicto `SE.12`.** Se usa `Suministrar Analitica` como nombre canónico porque es el primer valor explícito de la fila 99. `Mantener Tableros de Control`, observado en la fila 100, se conserva en `name_variants` y genera una observación `LEVEL_1_NAME_CONFLICT`. Solo existe un registro para `SE.12`.
3. **Códigos.** `SE.12.1`, `SE.12.2` y `SE.12.3` se conservan como texto en `code` y `original_code`. La transformación registrada es únicamente `trim_only`.
4. **Atributos incompletos.** Los servicios de las filas 99 a 101 se importan con `NULL` en los campos ausentes y `review_status='REVIEW'`. No se inventan clase, criticidad, tipo, métrica ni estado activo.
5. **Continuaciones y opciones.** Las filas hijas de rangos combinados se omiten con `MERGED_CONTINUATION`. Las listas `E112:H122` se omiten como `OPTION_LIST`; no se asignan a ningún servicio. Cualquier fila con datos dentro del rango de servicios que no tenga `COD.N2` queda como `NO_SERVICE_CODE`.
6. **Trazabilidad.** Cada nivel y servicio conserva hoja, fila, rango, código original y `transformations`. Cada ejecución se guarda en `import_runs`; cada conflicto, omisión o dato incompleto se guarda en `import_observations`.

La única regla explícita fuera de un rango combinado se aplica a `SE.12.3`: como está inmediatamente después de `SE.12.2`, se asocia a `SE.12` mediante `immediate_previous_explicit_level_1`, y la inferencia queda observada. No se realiza propagación general a filas ajenas.

El importador valida los controles de importación:

- 97 filas físicas analizadas.
- 12 códigos distintos de nivel 1.
- 46 códigos explícitos distintos de nivel 2.

La base se inicializa con `backend/db/00_schema.sql`; después el backend ejecuta el importador. El resultado esperado es 12 códigos de nivel 1 y 46 servicios de nivel 2.

## Autenticación y protección

La aplicación implementa autenticación local contra PostgreSQL, sin proveedores externos. El usuario puede identificarse por `username` o `email`. Las contraseñas se procesan con Argon2id, que genera y almacena su propia sal dentro del hash. No se usa AES para contraseñas.

Los datos de perfil que necesitan recuperarse se almacenan con AES-256-GCM, nonce aleatorio y datos asociados autenticados. La clave se configura con `APP_ENCRYPTION_KEY` y no debe compartirse ni versionarse fuera de `.env.example`.

El login crea una sesión opaca; PostgreSQL conserva únicamente el SHA-256 del token, su vencimiento y su revocación. El logout marca la sesión como revocada. Las rutas `/api/v1/auth/me` y `/api/v1/services` exigen `Authorization: Bearer <token>` mediante una dependencia del servidor. La interfaz solo mejora la experiencia y no reemplaza esta autorización.

### Roles y cuentas de evaluación

`administrador` mantiene usuarios, unidades organizativas y catálogo mediante rutas administrativas. `consulta` puede leer servicios, estructura y datos públicos de usuarios, pero no puede crear usuarios, cambiar roles, activar o desactivar cuentas ni modificar catálogos. La validación se ejecuta con `require_roles` en el servidor y no depende de botones ocultos.

El comando `scripts/create_demo_users.py` crea o actualiza `demo-admin` y `demo-consulta`, revoca sesiones anteriores y muestra credenciales temporales solo en la salida de consola. Si no se proporcionan contraseñas por argumentos, se generan aleatoriamente. Ninguna credencial demo se guarda en Git.

## Directorio organizacional

Se implementó la jerarquía `Empresa → Área → Departamento → Sección → Puesto → Usuario` con tablas separadas, claves foráneas obligatorias y restricciones `UNIQUE` compuestas para los códigos subordinados. Un usuario solo referencia un puesto; la empresa se obtiene recorriendo las relaciones del puesto y no se guarda una empresa redundante en el usuario.

Las rutas de consulta de la estructura requieren sesión y están disponibles para `administrador` y `consulta`. Las altas, modificaciones y bajas lógicas requieren `administrador`. El usuario se administra con `name`, `username`, `email`, `role`, `puesto_id`, estado y hash Argon2id; los endpoints de usuarios no retornan `password_hash` ni perfiles cifrados.

La política de dependencias es conservadora: no se crean hijos bajo padres inexistentes o inactivos; no se puede reactivar una entidad si su padre está inactivo; una empresa, área, departamento o sección no puede darse de baja mientras tenga hijos activos; un puesto no puede darse de baja mientras tenga usuarios activos. Primero deben desactivarse las dependencias y luego el padre. Las bajas solo cambian el estado y conservan la información para auditoría. Al desactivar un usuario se revocan sus sesiones.

## Servicios, catálogos y asignaciones

Los servicios de nivel 1 se mantienen en `service_level_1` y los de nivel 2 en `services`, con `level_1_code` como relación obligatoria y código único por entidad. El modelo conserva los campos del Excel: código original, nombre, estado, clase, criticidad, tipo, descripción, métrica, mínimo, máximo, estado de revisión, hoja, fila, rango y transformaciones.

Las clases, criticidades y tipos se mantienen en catálogos controlados con claves foráneas. Los formularios deben consultar `/api/v1/services/catalog-options`; el servidor rechaza referencias inexistentes o inactivas. Los datos faltantes permanecen como `NULL`, y se valida `mínimo <= máximo` solo cuando ambos valores existen.

La consulta de servicios admite búsqueda por código/nombre, filtros por nivel 1, estado y catálogos, y paginación. La ficha devuelve la relación y el nombre del nivel 1, todos los atributos importados y la trazabilidad. La alta manual exige sección responsable activa; el usuario responsable es opcional y debe pertenecer a esa sección. Los servicios importados pueden quedar sin asignación. `create_demo_users.py` agrega una jerarquía `DEMO` y crea tres asignaciones válidas como datos de demostración nuevos, separados de la fuente Excel.

La interfaz `OrganizationPanel.jsx` presenta la jerarquía en cinco columnas
encadenadas. Ambos roles pueden explorar los registros y ver los usuarios de un
puesto; el administrador dispone de alta, edición y baja lógica. Los formularios
solo ofrecen padres activos, pero la API vuelve a comprobar la relación, por lo
que la interfaz no sustituye la autorización ni las reglas de negocio.

## Operación

El procedimiento normal es `docker compose stop` para detener y `docker compose start` para reiniciar conservando datos. `docker compose down` retira contenedores y red, pero conserva el volumen. El procedimiento destructivo es `docker compose down -v`, seguido de `docker compose up --build -d`; elimina la base de prueba y vuelve a importar el Excel original.

## Context, prompts y harness

El contexto versionado, sus actualizaciones y la regla para tratar el Excel
como fuente externa no confiable están en
`docs/contexto/CONTEXTO-PROYECTO.md` y `docs/contexto/ACTUALIZACIONES.md`.
El registro de seis prompts realmente utilizados, junto con dos iteraciones de
mejora, está en `docs/prompts/REGISTRO.md`.

El harness está compuesto por `compose.yaml`, `compose.test.yaml`, el esquema
SQL, el importador, `scripts/create_demo_users.py`,
`scripts/verify_persistence.sh`/`scripts/verify_persistence.ps1`, las pruebas
unitarias, de integración y E2E.
Los datos de integración viven en una base y volumen separados; el procedimiento
destructivo nunca apunta al volumen normal. Las credenciales demo se generan o
se reciben localmente y no se guardan en el repositorio.

## Matriz requisito → implementación → prueba → evidencia

| Requisito | Implementación | Prueba o control | Evidencia |
|---|---|---|---|
| Login, logout y roles | `auth_service.py`, dependencias y rutas | P01–P03 integración/E2E | `tests/integration/test_scenarios.py`, `tests/e2e/catalogo.spec.js` |
| Jerarquía y bajas lógicas | `directory_service.py`, `hierarchy_repository.py` | P04–P05 y P11 | `tests/integration/test_scenarios.py` |
| Catálogo y filtros | `service_service.py`, `service_routes.py`, `ServiceBrowser.jsx` | P09–P10 | pruebas de integración/E2E |
| Importación 12/46 | `catalog_importer.py` | P06–P08 y `--dry-run` | `tests/backend/test_importer_rules.py`, `RESULTADOS-2026-10-01.md` |
| Idempotencia | `upsert_level` y `upsert_service` | P07 | `tests/integration/test_scenarios.py` |
| Persistencia | volumen `postgres_data` | P12 | `scripts/verify_persistence.ps1` |
| Docker y arranque ordenado | healthchecks y `depends_on` | `docker compose up --build -d` | `README.md`, `compose.yaml` |

## Resultados y limitaciones de esta revisión

La ejecución en seco y las pruebas unitarias fueron comprobadas el 2026-10-01.
El entorno de revisión no tenía Docker ni `node_modules`, por lo que las
pruebas de integración contra PostgreSQL y E2E deben ejecutarse en Fedora o en
un equipo con Docker, siguiendo `tests/README.md`. No se declaran como
aprobadas hasta obtener su salida real.

La entrega final todavía debe completar el SHA del commit entregado, crear la
etiqueta `parcial-v2.0`, verificar el acceso del usuario GitHub
`maldanap-usac` y adjuntar capturas o salidas de consola sin secretos en
`docs/evidencias/`.

## Limitaciones conocidas y decisiones humanas

- El script P12 está escrito en PowerShell; en Fedora se ejecuta con `pwsh`.
- Las asignaciones `DEMO` son datos de demostración y no forman parte del Excel.
- El administrador debe revisar los servicios importados con `REVIEW` antes de
  considerarlos datos completos.
- La revisión humana debe validar que las contraseñas demo no se copien al Git,
  que el Excel permanezca sin modificaciones y que el commit entregado sea el
  mismo que se evaluará.
