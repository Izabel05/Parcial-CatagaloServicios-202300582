# tests

Pruebas automatizadas del proyecto.

- Las pruebas del backend pueden organizarse en `tests/backend/`.
- Las pruebas del frontend pueden organizarse en `tests/frontend/`.
- Las pruebas de integración pueden organizarse en `tests/integration/`.

Prueba de reglas del importador:

```powershell
python -m unittest tests.backend.test_importer_rules tests.backend.test_security
```
# Estrategia de pruebas

Las pruebas separan datos y responsabilidades:

- **Unitarias:** `tests/backend/test_importer_rules.py` valida P06 y P08 sobre una copia de lectura del Excel; `tests/backend/test_security.py` valida Argon2id y AES-256-GCM sin base de datos.
- **Integración:** `tests/integration/test_scenarios.py` cubre P01–P05 y P09–P11 contra una base indicada por `TEST_DATABASE_URL`. El módulo recrea únicamente el esquema de esa base de pruebas, inserta usuarios y jerarquía de prueba, ejecuta dos importaciones y comprueba las respuestas HTTP. No usa el volumen de evaluación.
- **Persistencia de Compose:** `scripts/verify_persistence.ps1` ejecuta P12 en el proyecto Compose aislado `catalogo-servicios-tests`, escribe un marcador, reinicia el contenedor PostgreSQL y verifica que el volumen conserva el dato. Termina con `down` sin `-v`, por lo que no elimina el volumen de pruebas ni toca el volumen normal.
- **Extremo a extremo:** `tests/e2e/catalogo.spec.js` usa Playwright contra el frontend real y cubre P01, P02, P03, P09 y P10: login, mensajes de error, cierre de sesión, visibilidad por rol, búsqueda y validación de rangos. Requiere backend, frontend y cuentas locales de demostración; si faltan variables de entorno, los casos quedan omitidos explícitamente.

## Ejecución unitaria

Desde la raíz del repositorio:

```powershell
docker compose exec backend python -m unittest tests.backend.test_importer_rules tests.backend.test_security
```

En Fedora se puede usar el mismo comando desde Bash. Así no se requiere
instalar Python ni las dependencias del backend en el equipo anfitrión.

## Ejecución de integración

Usar una base PostgreSQL exclusiva para pruebas. Por ejemplo, con el contenedor
de pruebas levantado:

```powershell
docker compose -f compose.test.yaml -p catalogo-servicios-tests up -d db
$env:TEST_DATABASE_URL = "postgresql://catalogo_test:catalogo_test@localhost:55432/catalogo_servicios_test"
python -m unittest tests.integration.test_scenarios
```

La URL apunta al puerto `55432` de la base de pruebas, no a la base de evaluación. No se debe cambiar `POSTGRES_PORT` de la instalación normal para ejecutar estas pruebas.

## P12

```bash
bash scripts/verify_persistence.sh
```

En Windows se puede usar `scripts/verify_persistence.ps1`; en Fedora se usa el
script Bash. Ambos utilizan una definición Compose y un volumen distintos del
sistema normal. No ejecutar `docker compose down -v` sobre la instalación de
evaluación.

## Ejecución E2E de interfaz

Con la aplicación normal levantada y las cuentas creadas localmente:

```powershell
cd frontend
npm install
npx playwright install chromium
$env:E2E_ADMIN_USER = "admin"
$env:E2E_ADMIN_PASSWORD = "la-clave-local-del-admin"
$env:E2E_CONSULTA_USER = "consulta"
$env:E2E_CONSULTA_PASSWORD = "la-clave-local-de-consulta"
npm run test:e2e
```

Se puede cambiar la URL con `$env:E2E_BASE_URL`. Los casos E2E no crean jerarquías ni reutilizan la base de pruebas; P09 solo envía un alta inválida y no deja registros.
