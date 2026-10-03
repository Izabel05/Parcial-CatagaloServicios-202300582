# Evidencia de validación

## Resultados ejecutados

| Control | Comando | Resultado |
|---|---|---|
| Sintaxis Python | `python -m compileall -q backend scripts tests` | OK |
| Sintaxis JavaScript de pruebas | `node --check frontend/tests/e2e/catalogo.spec.js` | OK |
| Importación sin escritura | `python -m backend.app.importer --dry-run` | 12 nivel 1, 46 nivel 2, 63 omitidas, 57 observadas |
| Unitarias | `python -m unittest tests.backend.test_importer_rules tests.backend.test_security` | 4 OK, 2 omitidas por dependencias del entorno |
| Integración | `docker compose -f compose.test.yaml -p catalogo-servicios-tests run --build --rm backend-tests` | 1 prueba aprobada (`OK`) |
| E2E | `npx playwright test tests/e2e/catalogo.spec.js` | 6 omitidas; falta repetir con credenciales E2E exportadas |
| SQL | comprobación de restricciones y bloques `DO` | OK |

## Fotografías disponibles

### Construcción y arranque Docker

![Construcción de imágenes y contenedores saludables](../Imagenes/DockerEjecucion.png)

La captura muestra el build terminado y los contenedores `db`, `backend` y
`frontend` iniciados; debe conservarse sin pestañas o terminales que expongan
claves.

### Preparación de la base de pruebas

![Creación de la base aislada de pruebas](../Imagenes/EjecucionPrueba.png)

Esta captura demuestra la creación del volumen y contenedor de pruebas, pero no
el resultado de las pruebas de integración.

### Persistencia P12

![P12 aprobado](../Imagenes/P12Ejecuccion.png)

Esta evidencia sí demuestra que el marcador sobrevivió al reinicio sin eliminar
el volumen.

### Integración aprobada

![Prueba de integración aprobada](../Imagenes/PruebaIntegracion.png)

La captura muestra el contenedor aislado `backend-tests`, PostgreSQL saludable y
el resultado `Ran 1 test ... OK`. Esta evidencia sustituye la captura anterior
de integración omitida.

### E2E ejecutado pero omitido

![Ejecución E2E omitida](../Imagenes/PruebaE2EOmitida.png)

La captura muestra los seis escenarios Playwright como `skipped`. El harness sí
inició, pero faltaban una o más variables `E2E_ADMIN_USER`,
`E2E_ADMIN_PASSWORD`, `E2E_CONSULTA_USER` y `E2E_CONSULTA_PASSWORD`; por ello no
se presenta como resultado aprobado.

### Captura que debe reemplazarse

![Prueba omitida](../Imagenes/PruebaUnitariaPyhton.png)

Esta captura ejecuta `tests.integration.test_scenarios` y reporta `OK
(skipped=1)`. No es una prueba unitaria aprobada; debe repetirse con:

```bash
docker compose -f compose.test.yaml -p catalogo-servicios-tests run --build --rm backend-tests
docker compose exec backend python -m unittest tests.backend.test_importer_rules tests.backend.test_security
```

Toma una captura adicional de las pruebas unitarias y otra de E2E con seis casos
aprobados. No publiques contraseñas demo, claves AES ni valores completos de
`.env` en las fotografías.

## Pendientes de ejecución en Fedora/Docker

La evidencia que todavía falta capturar es:

```bash
docker compose up --build -d
docker compose exec backend python -m unittest tests.backend.test_importer_rules tests.backend.test_security
bash scripts/verify_persistence.sh
cd frontend
npx playwright test tests/e2e/catalogo.spec.js
```

La prueba de integración debe usar únicamente `TEST_DATABASE_URL` apuntando al
puerto `55432`; nunca debe apuntar al volumen normal de evaluación.

## Evidencia de ciclo de corrección

El historial técnico registrado fue: tarea de importación → fallo al separar
bloques SQL `DO` → corrección del parser → validación de sintaxis, esquema y
prueba en seco satisfactoria. La evidencia final debe enlazar el commit que
contenga esta corrección y una captura o salida de consola sin secretos.
