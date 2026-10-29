# Validación de tickets, colas y permisos

Fecha: 28 de octubre de 2026. Base Git:
`7255835b653ebd1b948d0c97a41cfffaacbb7a85`. Los cambios de esta ampliación
están en el árbol de trabajo posterior a ese commit; no se creó un commit
automáticamente. No se atribuyen al commit base las funcionalidades nuevas.

## Entorno

Ubuntu 24.04.4, Docker 29.3.0 y Compose v5.1.1 en el servidor autorizado;
contenedores Python 3.12, PostgreSQL 16, Node 22 y Playwright 1.63.0/Chromium.
Directorio remoto `/home/servidor/catalogo-desk-validacion`. Proyectos aislados:
`catalogo-desk-tests` y `catalogo-desk-app`, con volúmenes independientes.
Los demás proyectos del servidor no se modificaron.

La aplicación de verificación usó el mismo patrón de override de puertos de
la [línea base](BASE-PARCIAL-2026-10-28.md): frontend `127.0.0.1:15173`, API
`127.0.0.1:18000`, base de aplicación sin puerto público. Su archivo se llamó
`compose.validation.yaml`. No se incluyeron claves ni archivos de trabajo en Git.

## Comandos y resultados

```bash
docker compose -f compose.test.yaml -p catalogo-desk-tests run --build --rm backend-tests
docker compose -f compose.yaml -f compose.validation.yaml -p catalogo-desk-app up --build -d
docker compose -f compose.yaml -f compose.validation.yaml -p catalogo-desk-app exec -T backend python scripts/create_demo_users.py
docker compose -f compose.yaml -f compose.validation.yaml -p catalogo-desk-app exec -T backend python scripts/create_desk_demo.py
docker compose -f compose.yaml -f compose.validation.yaml -p catalogo-desk-app exec -T frontend npm run build
```

Se generó además un lote CMDB con semilla 202300582, 5,000 dispositivos y el
ID del administrador demo como responsable, para conservar las pruebas E2E de
CMDB. Las credenciales generadas se guardaron temporalmente con permisos 600
en el servidor y se suministraron mediante `--env-file`, sin imprimirlas en
los registros de evidencia.

```bash
docker run --rm --network host --env-file .e2e.env \
  -v "$PWD/frontend:/work" -w /work \
  mcr.microsoft.com/playwright:v1.63.0-noble \
  sh -c 'npm ci && npx playwright test --reporter=list'
bash scripts/verify_desk_persistence.sh
```

| Control | Entrada/resultado esperado | Resultado real | Salida |
|---|---|---|---|
| Backend final | Regresiones del parcial/CMDB y reglas Service Desk | 21 métodos aprobados, sin omisiones, 28.096 s | 0 |
| Arranque | Base, migraciones y API disponibles | Compose levantado, base/API saludables | 0 |
| Migración incremental | Aplicar 004 sobre la aplicación ya iniciada con 003 | Solo `004_ticket_resolucion.sql` aplicada; datos existentes conservados | 0 |
| Compilación | Nueva pestaña y regresiones React | 37 módulos, 1.76 s | 0 |
| Playwright | Portal, agente, consulta y pantallas anteriores | 10 aprobados, sin omisiones, 8.3 s | 0 |
| Toma concurrente | Dos agentes, mismo ticket abierto | Aserción de estados `[200,409]` y una única entrada `tomar` aprobadas | 0 |
| Consulta con concesiones de escritura | Roles adicionales y permisos de cola de atención/aprobación/administración | Creación, toma, comentarios, aprobación y baja rechazadas con 403 | 0 |
| Visibilidad interna | Solicitante/consulta leen ticket con nota y archivo internos | Contenido omitido de comentarios, archivos e historial; descarga interna 403 | 0 |
| Adjuntos | Texto público válido, PNG falso y archivo mayor de 5 MiB | Descarga propia correcta; tercero 403; PNG falso 409; exceso 413 | 0 |
| Concesión directa y revocación | Acceso solo al usuario concedido; agente aún asignado | Otro agente 403; revocar permiso/rol incompatible 403 con rollback | 0 |
| Reinicio completo de aplicación | Conservar catálogo, CMDB, colas, ticket, bitácora y bytes de archivo | Conteos y checksums de ticket/archivo idénticos; API recuperada | 0 |
| Script de persistencia de pruebas | Comparar datos y adjuntos del conjunto de integración | 11 tickets, cuatro colas, 39 acciones, dos comentarios y dos adjuntos conservados, con checksums idénticos | 0 |

La suite tiene seis métodos unitarios, siete de la clase parcial/CMDB y ocho
de la clase parcial/Service Desk. Los escenarios P01–P11 del parcial se ejecutan
en ambas clases, sobre esquemas de prueba recreados por separado. No se suman
las aserciones individuales como si fueran métodos de prueba independientes.

La base de aplicación/E2E conservó al reiniciar: **46 servicios, 5,000
dispositivos, siete colas, un ticket, 19 entradas de historial, dos comentarios
y un adjunto**. Los checksums del ticket y del contenido del archivo coinciden
antes/después. El historial incluye la configuración inicial de colas/permisos,
por eso no corresponde todo a acciones del único ticket.

## Cobertura y registros

- [Backend final](service-desk-2026-10-28/backend-final.txt): referencias válidas,
  aislamiento entre solicitantes, permisos por rol/usuario, roles combinados,
  orden reproducible, concurrencia, transferencias y escalamiento, bajas
  protegidas, comentarios/archivos, vínculos, aprobación sin autoaprobación,
  resolución/cierre/reapertura y edición auditada.
- [Interfaz](service-desk-2026-10-28/e2e.txt): usuario solicitante crea ticket,
  agrega comentario y TXT; agente toma y registra nota interna; solicitante
  vuelve a entrar y no ve esa nota; consulta no obtiene formularios de escritura.
  Incluye los ocho casos anteriores de catálogo/CMDB.
- [Arranque](service-desk-2026-10-28/startup.txt),
  [compilación](service-desk-2026-10-28/frontend-build.txt) y
  [migración incremental](service-desk-2026-10-28/migrations.txt).
- [Reinicio de aplicación](service-desk-2026-10-28/persistence.txt) y
  [persistencia del entorno de pruebas](service-desk-2026-10-28/persistence-tests.txt).
- [Auditoría npm de dependencias de ejecución](service-desk-2026-10-28/npm-runtime-audit.txt).
  La instalación también reportó una advertencia de vulnerabilidad en el
  conjunto con dependencias de desarrollo, ya presente en la línea base;
  no se modificaron versiones de paquetes en esta etapa.
- [Hashes del código validado](service-desk-2026-10-28/source-hashes.json) y
  [apagado de verificación](service-desk-2026-10-28/shutdown.txt).

Se contrastaron los 94 archivos de código y configuración del manifiesto contra
el árbol local: todos los hashes coinciden. Se verificaron los enlaces locales
de la documentación y la ausencia de credenciales generadas en los registros.

No se introdujeron fallos deliberados ni se inventan ciclos de corrección. La
primera ejecución de backend tuvo 20 métodos; luego se agregó la comprobación
de concesión directa/revocación/edición y se ejecutó la suite final de 21.
La migración 004 se agregó para reforzar que CHECK rechace resolución NULL;
no se alteró el checksum de la migración 003 ya aplicada.

Las trazas de navegador y archivos de credenciales no se incorporan a Git.
Los contenedores de verificación se retiran al terminar sin eliminar volúmenes.
La base común aún no implementa las siete máquinas de estados especializadas,
automatización de eventos, indicadores ni los 35 tickets de demostración de
los procesos completos. Su alcance está descrito en [SERVICE_DESK.md](../SERVICE_DESK.md).
