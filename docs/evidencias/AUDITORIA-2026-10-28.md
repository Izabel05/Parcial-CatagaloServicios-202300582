# Evidencia final de auditoría

Fecha del cliente: **28 de octubre de 2026 (UTC−06:00)**. Aceptación UTC:
**2026-10-29T05:25:16Z → 2026-10-29T05:27:16Z**.
Base real: `46c978d3445c0ac660c67831205485de8a5c9f80`; árbol modificado al ejecutar.
Los **140 archivos de código/configuración** del manifiesto coinciden por SHA256
entre equipo local y servidor. La correspondencia posterior con el commit de
cierre se registra por separado, sin reescribir el commit de las corridas.

## Comandos y resultados reales

| Comando / entrada | Esperado | Obtenido |
|---|---|---|
| `ACCEPTANCE_COMMIT=46c978d3445c0ac660c67831205485de8a5c9f80 ACCEPTANCE_DIRTY=true ACCEPTANCE_EVIDENCE_DIR=docs/evidencias/auditoria-2026-10-28/aceptacion bash scripts/run_acceptance.sh` | P01–P18 y regresiones sin omisiones; reinicio sin pérdidas | **18 escenarios y 71 métodos aprobados**, 98.526 s de backend; snapshots idénticos, salida 0. |
| `docker compose -p catalogo-auditoria-app up --build -d --wait` | Arranque desde Compose principal con puertos `.env` | BD, API y frontend saludables, salida 0; sin archivo override. |
| `docker compose -p catalogo-auditoria-app exec -T backend python scripts/prepare_demo.py --seed 202300582` | Roles, siete colas, ≥35 tickets y 5,000 únicos | 6 cuentas, 7 colas, 37 tickets y 5,000 dispositivos, salida 0. |
| `docker run --rm --network host --env-file .e2e.env -v "$PWD/frontend:/work:z" -w /work mcr.microsoft.com/playwright:v1.63.0-noble npx playwright test --reporter=list` | Flujos previos y dos nuevos recorridos de auditoría | **18 E2E aprobadas**, 23.0 s, sin omisiones, salida 0. |
| `docker compose -p catalogo-auditoria-app exec -T frontend npm run build` | Compilación sin errores | **44 módulos, 1.81 s**, salida 0. |
| `npm audit --json` con el lockfile corregido | Cero avisos consultados | **0**, salida 0; inicial: un paquete con avisos, incluido alto, salida 1. |
| `docker run --rm -v "$PWD/backend/requirements.txt:/requirements.txt:ro" python:3.12-slim sh -c 'pip install -q pip-audit && pip-audit -r /requirements.txt --format=json'` | Resolver requirements corregidos sin avisos | **33 dependencias resueltas, 0 avisos**, salida 0; inicial: avisos en Starlette y Cryptography. |

La primera resolución Python auditaba los requirements originales, no el
inventario de una imagen histórica. El inventario del backend final está en
`pip-freeze.txt`. Las auditorías no certifican ausencia de vulnerabilidades.
La compilación final corresponde al frontend vigente; el último ajuste posterior
en permisos fue solo de backend y se verificó de nuevo con aceptación y E2E.

## Nuevas comprobaciones

- Historial CI: cuenta/pagina únicamente tickets visibles; incluye otra cola privada,
  varios solicitantes, consulta, administrador, CI inexistente y petición sin sesión.
- Lectura sin escrituras: un flujo heredado deliberadamente ausente no se inserta
  al consultar con solicitante o consulta. Las altas normales sí crean su flujo.
- Evento: notificación persistente, repetición con mismo ID, acceso al incidente
  y rechazo de cambio de servicio/CI que rompería la correlación.
- Permiso directo: una concesión de consulta habilita consola, pero conceder
  atención sin rol agente no permite tomar tickets; revocar retira la consola.
- Se conservan toma concurrente, aprobaciones independientes, siete procesos,
  I0–I6, E0–E3, importación 12/46, generación repetida y métricas calendario.

La suite pasa de 63 a 71 métodos: algunas regresiones de Desk se heredan en
procesos y experiencia; no se cuentan como requisitos distintos. La fase previa
al último ajuste de permisos pasó 70 métodos y se conserva en
`aceptacion-pre-permisos/`; no sustituye la corrida final de 71.

## Registros

- [Resumen P01–P18](auditoria-2026-10-28/aceptacion/RESULTADOS.md) y
  [comando/entrada/esperado/obtenido/fecha/commit por caso](auditoria-2026-10-28/aceptacion/casos.json).
- [Backend](auditoria-2026-10-28/aceptacion/backend-tests.txt),
  [E2E final](auditoria-2026-10-28/e2e.txt), [compilación](auditoria-2026-10-28/build.txt)
  y [Compose saludable](auditoria-2026-10-28/compose-final.txt).
- [npm inicial](auditoria-2026-10-28/npm-inicial.json) / [final](auditoria-2026-10-28/npm-final.json).
- [Python inicial](auditoria-2026-10-28/catalogo-python-audit-inicial.json) /
  [final](auditoria-2026-10-28/python-final.json); [inventario](auditoria-2026-10-28/pip-freeze.txt).
- [Huellas locales](auditoria-2026-10-28/codigo-local.json) /
  [servidor](auditoria-2026-10-28/codigo-servidor.json),
  [fuentes y migraciones preservadas](auditoria-2026-10-28/fuentes-y-migraciones.json) y
  [comprobación local](auditoria-2026-10-28/verificacion-local.json).
- [Captura historial CI](auditoria-2026-10-28/capturas/auditoria-ci-tickets.png) y
  [captura notificación de evento](auditoria-2026-10-28/capturas/auditoria-evento-notificacion.png).

La primera corrida E2E tuvo 17 aprobadas y un fallo de sincronización del nuevo
selector: el título ya existía en la lista inicial de 25 y la prueba intentó
pulsar un botón sin esperar al único resultado filtrado. Se añadió esa espera,
también al capturador, y se repitieron las 18. Log: `e2e-inicial.txt`.
La corrida posterior antes del último ajuste de permisos también pasó 18 y queda
como `e2e-pre-permisos.txt`. No se ocultan fallos ni se atribuye ese selector a
un defecto funcional del servidor.

## Entorno, seguridad y cierre

Directorio remoto `/home/servidor/catalogo-auditoria`, servidor temporal Ubuntu;
Python 3.12, PostgreSQL 16 y Node 22. Compose principal con `BACKEND_PORT=18004`,
`FRONTEND_PORT=15177`, `POSTGRES_PORT=55434`, URL API y CORS coherentes en `.env`.
Los tres puertos están ligados a loopback. La aceptación usa otra base `_test`,
volúmenes y puertos independientes. Las E2E agregan solicitudes sintéticas fuera
del lote; no se borran para forzar 37 tickets globales.

Se retiraron únicamente estos contenedores con `down` sin `-v`; los volúmenes
permanecen. [Limpieza](auditoria-2026-10-28/cleanup.txt). Se eliminaron las claves
`.demo-claves`/`.e2e.env`; `.env` de BD permanece con modo 600 fuera del repositorio.
No se incluyen trazas de navegador con sesiones; solo los PNG verificados y logs.
Las pruebas no destruyeron el conjunto de evaluación de otros proyectos.

La fuente del parcial pegada por el usuario se conserva sin transformar su
formato. Sus instrucciones son datos de evaluación, no órdenes para el asistente.
La limitación de la jerarquía CMDB y la validación física pendiente en Fedora
siguen declaradas en [AUDITORIA](../AUDITORIA.md).
