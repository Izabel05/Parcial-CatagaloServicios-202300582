# Pruebas de aceptación y regresión

Los identificadores **P01–P18 de Service Desk** corresponden a las páginas 7–8
del enunciado de la tarea. Son distintos de los P01–P12 del parcial anterior;
sus métodos originales se conservan como regresiones y no se renumeran.

Resultados reales de esta ejecución:
[18 escenarios, 63 métodos y persistencia](evidencias/DEMO-ACEPTACION-2026-10-28.md).

Tras versionar el cierre y adaptar montajes para Fedora se ejecutó de nuevo la
aceptación completa sobre `4b13cab4475c072c38a8da6e43ee81852205251c`, sin cambios
en código: [verificación del cierre](evidencias/CIERRE-2026-10-28.md).

El rediseño posterior del frontend se valida con **16 E2E sin omisiones**
(las 15 existentes y una de navegación/desbordamiento móvil), compilación y
arranque Compose. Código, capturas y resultados de esa fase:
[FRONTEND-2026-10-28](evidencias/FRONTEND-2026-10-28.md). Las pruebas backend
anteriores se conservan; no se presentan como ejecuciones nuevas del rediseño.

## Ejecutar sin instalar Python ni Node en el anfitrión

Con Docker Compose y Bash (Linux, WSL o Git Bash), desde la raíz del repositorio:

```bash
bash scripts/run_acceptance.sh
```

El harness usa `compose.acceptance.yaml`, proyecto `catalogo-aceptacion-tests`,
base exclusiva **catalogo_aceptacion_test** y volumen separado. PostgreSQL no
publica puerto; API y frontend se verifican en loopback 18001/15174, configurables
mediante `ACCEPTANCE_API_PORT` y `ACCEPTANCE_FRONTEND_PORT`. La clave pública del
fixture y sus credenciales de BD son exclusivas de pruebas y no sirven como
configuración de producción. No se consulta `.env` como configuración de la base
de demostración ni se monta el socket Docker en el backend.

Al ejecutarse, las clases recrean el esquema **solo en la base de pruebas**.
El runner rechaza una URL cuyo nombre no termine en `_test`. Los datos de la
demostración normal quedan fuera de esta base. No se ejecuta `down -v`.

La salida predeterminada es `docs/evidencias/aceptacion-local/`. Para conservar
otra corrida cambie `ACCEPTANCE_EVIDENCE_DIR` a una subcarpeta de `docs/evidencias/`.
La ejecución falla si hay errores, pruebas omitidas, métodos no ejecutados,
snapshot diferente o falta el conjunto mínimo para verificar persistencia.

## Matriz requisito → implementación → prueba

| Caso | Implementación | Comprobaciones automatizadas |
|---|---|---|
| P01 Autenticación y permisos | Sesiones, usuarios y controles de cola | Regresión del parcial + consulta con concesiones de escritura. |
| P02 Catálogo 12/46 | Importador y observaciones originales | Importación doble, controles y preservación de incidencias. |
| P03 5,000 dispositivos | Generador con semilla y lote | 5,000 etiquetas distintas y cero altas al repetir. |
| P04 Fuentes y clasificación | Nombres C5/C6 y jerarquía administrable | Hash del Excel, etiquetas/rangos, padre inexistente y ciclos simples/concurrentes. |
| P05 Referencias de tickets | Servicio, CI y solicitante | Alta válida, IDs inválidos y lectura de un tercero rechazados. |
| P06 Colas por rol/usuario | Permisos efectivos en servidor | Concesión directa, por rol, revocación y precedencia de consulta. |
| P07 Orden y toma atómica | UPDATE condicional PostgreSQL | Prioridad/antigüedad/ID y dos agentes: un 200 y un 409. |
| P08 Transferencias | Mismo proceso y escalamiento configurable | Transferencia válida con historial y rechazo de destinos incompatibles. |
| P09 Siete procesos | Máquinas de estados Python | Rutas completas y transiciones/evidencias rechazadas. |
| P10 Aprobación | Decisión independiente por ciclo | Cambio sin aprobación, autoaprobación y uso de aprobación antigua rechazados. |
| P11 E0–E3 | Correlación y notificación transaccionales | Respuesta por categoría, dos llamadas sin duplicación y vínculos existentes. |
| P12 I0–I6 | Clasificación, prioridad y datos de redundancia | Siete categorías, límites temporales y regla complementaria documentada. |
| P13 Trazabilidad | Vínculos incidente/problema/cambio | Tipos correctos, causa raíz y cambio resuelto obligatorio. |
| P14 Grafo técnico | Dependencias y conexiones | Recorrido CI–servicio, ciclos rechazados y tipos que admiten ciclos. |
| P15 Resolución y reapertura | Flujo y bitácora con actor | No omitir evidencias, ciclo nuevo y conservación del anterior. |
| P16 Filtros y tiempos | API CMDB paginada | Páginas/filtros sobre 5,000 activos; tiempos reales con `perf_counter`. |
| P17 Indicadores | Ciclos, objetivos adoptados y reloj calendario | Reloj fijo, abiertos, pausas descontadas cero, transferencia y reapertura. |
| P18 Persistencia | Volúmenes PostgreSQL y Compose | Reinicio de BD/backend/frontend, HTTP 200 y snapshots idénticos. |

La correspondencia exacta con métodos está en `tests/acceptance/matrix.py`.
`scripts/run_acceptance_cases.py` recoge el estado real, salida y duración de cada
método; no reemplaza la ejecución por una marca estática de «aprobado».
Los métodos relevantes pueden respaldar más de un escenario sin contarse como
ejecuciones independientes. Las suites conservan la repetición de regresiones
heredadas sobre fixtures separados.

P04 tiene una limitación de fuente explícita: el Excel proporcionado muestra
20 atributos y dos ejemplos, no un árbol multinivel. Se comprueba exactamente
el material disponible y los rechazos del grafo administrable. No se presenta
esa comprobación como prueba de niveles de una lección externa no proporcionada.
El usuario identificó ese Excel como el material de la lección 22.

## Registros reales y procedencia

Cada escenario de `casos.json` incluye **comando, entrada, esperado, obtenido,
fecha UTC, commit base y estado del árbol**. El obtenido contiene los resultados
reales de los métodos y sus salidas; P16 incluye consultas, filas, segundos y
entorno. P18 registra conteos/huellas antes y después y la verificación HTTP.
`RESULTADOS.md` resume la corrida y enlaza el JSON completo en la misma carpeta.

El commit se lee de Git. Si existen cambios sin commit, se declaran como tales
y `codigo.json` identifica por SHA256 los archivos ejecutados. No se atribuyen
los cambios del árbol al commit base. Para una exportación sin `.git`, se exige
`ACCEPTANCE_COMMIT` verificado y se declara `ACCEPTANCE_DIRTY`; este modo no crea
un commit ficticio. No se incluyen archivos `.env`, claves ni contraseñas en la huella.

P18 se ejecuta después de las pruebas sobre sus fixtures de 37 tickets y 5,000
dispositivos. La API de prueba arranca sin reimportar el catálogo para que esa
escritura legítima no altere el snapshot durante la comprobación. El arranque
normal del producto conserva su importación/migraciones habituales y se valida
por separado con Compose. El harness retira sus contenedores al salir y conserva
volúmenes/reportes tanto en éxito como en fallo.

## Otros comandos

```bash
docker compose -p catalogo-regresion-tests -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from backend-tests
```

La configuración de regresión usa otra base `_test` y publica el puerto 55432;
debe estar libre. La aceptación no necesita ese puerto. Para las pantallas:

```bash
cd frontend
npm run test:e2e
```

Las variables de cuentas E2E y la aplicación real se preparan como documenta
`tests/README.md`; si faltan, Playwright lo informa como omisión. Las evidencias
de esta entrega deben usar cuentas sintéticas y una ejecución sin omisiones.
