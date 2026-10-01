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

## Operación

El procedimiento normal es `docker compose stop` para detener y `docker compose start` para reiniciar conservando datos. `docker compose down` retira contenedores y red, pero conserva el volumen. El procedimiento destructivo es `docker compose down -v`, seguido de `docker compose up --build -d`; elimina la base de prueba y vuelve a importar el Excel original.

Este documento se ampliará con los requisitos, casos de uso y resultados del parcial.
