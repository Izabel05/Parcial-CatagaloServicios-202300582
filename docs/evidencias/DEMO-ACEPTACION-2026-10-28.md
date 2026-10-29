# Demostración y aceptación P01–P18

Ejecución del 28 de octubre de 2026 en la zona America/Chicago; las marcas UTC
de esta corrida corresponden al **29 de octubre**. Fin de aceptación:
`2026-10-29T00:15:42.290434+00:00`.

Commit base real: `7255835b653ebd1b948d0c97a41cfffaacbb7a85`.
El árbol tiene cambios sin commit. No se atribuyen al commit base las funciones
nuevas: `codigo.json` identifica por SHA256 los **135 archivos de código y
configuración ejecutados**, comprobados contra las copias locales.

## Demostración real

Comando dentro de `/home/servidor/catalogo-demo-validacion`:

```bash
docker compose -p catalogo-demo-app -f compose.yaml -f compose.validation.yaml up -d --build --wait
docker compose -p catalogo-demo-app -f compose.yaml -f compose.validation.yaml exec -T backend python scripts/prepare_demo.py
```

La salida estándar se guardó en JSON; las claves nuevas de stderr se guardaron
solo temporalmente con permisos 600 y se eliminaron al terminar, sin incluirlas
en estos registros.

| Entrada | Esperado | Obtenido | Fecha UTC |
|---|---|---|---|
| Semilla predeterminada 202300582, primera preparación | Siete colas, roles completos, ≥35 tickets y ≥5,000 dispositivos únicos | Siete colas, seis usuarios, 37 tickets y 5,000 etiquetas distintas | 2026-10-29 00:03:52.118703+00:00 |
| Mismo comando y semilla | Cero tickets nuevos; mismos IDs y categorías | Cero altas de tickets; IDs iguales; dispositivos totales/únicos 5,000 | Fecha exacta en `demo-repetida.json` |
| Misma semilla después de las pruebas de interfaz | Conservar el lote y las solicitudes de evaluación ya creadas | Cero altas del lote; sus 37 IDs conservados y dos notificaciones existentes | 2026-10-29 00:17:57.441234+00:00 |

Distribución del lote: accesos 5, cambios 5, eventos 5, incidentes 7, nuevos
servicios 5, problemas 5 y servicios de tecnología 5. Cubre E0–E3 e I0–I6 y
etapas iniciales, intermedias y finales. El E3 se vincula con el I6; E2/E3
respondidos tienen dos notificaciones persistentes y no se duplican al repetir.

La distribución CMDB reportada es Hardware, nivel 0: **5,000 dispositivos**;
Software, nivel 0: **0 dispositivos**. Se conservan ambas clases observadas en
el Excel, sin inventar niveles ni contar Software como dispositivos físicos.
El catálogo de fuente conserva sus controles **12/46**.

El lote identifica solo sus 37 tickets; las E2E crean solicitudes adicionales
con prefijo `E2E-`, sin agregarlas a ese lote ni restablecerlo. Las fechas y
contenidos de atención son sintéticos, no mediciones de trabajo humano.

## Aceptación real

La copia del servidor no tiene `.git`; se suministró el commit base comprobado
localmente y se declaró el árbol modificado:

```bash
ACCEPTANCE_COMMIT=7255835b653ebd1b948d0c97a41cfffaacbb7a85 \
ACCEPTANCE_DIRTY=true \
ACCEPTANCE_EVIDENCE_DIR=docs/evidencias/aceptacion-2026-10-28 \
bash scripts/run_acceptance.sh
```

| Verificación | Esperado | Obtenido | Salida |
|---|---|---|---|
| Backend y regresiones | Métodos aprobados sin omisiones | **63 métodos aprobados**, 91.590 s, cero omisiones | 0 |
| Matriz Service Desk | P01–P18 con registros reales | **18 aprobados, cero fallidos** | 0 |
| P18 | Reiniciar BD, backend y frontend y conservar datos | Snapshots idénticos y API/frontend HTTP 200 | 0 |
| Protección del conjunto demo | Base de pruebas independiente | `catalogo_aceptacion_test`, volumen y proyecto propios | 0 |
| Repetición de demostración | Sin duplicar ni restablecer tickets | IDs conservados; avance del evaluador preservado en la prueba de integración | 0 |
| Fallo deliberado | Revertir lote y tickets de una generación interrumpida | Excepción inyectada capturada y rollback verificado | 0 |

La tabla por caso con fecha/esperado/obtenido está en
[RESULTADOS.md](aceptacion-2026-10-28/RESULTADOS.md).
**Comando, entrada, esperado, obtenido, fecha y commit de cada escenario** están
en [casos.json](aceptacion-2026-10-28/casos.json), junto con los métodos que lo
respaldan, su estado real y su salida. Los snapshots completos y la huella del
código están en la misma carpeta.

P04 verifica el material disponible y los controles de padres/ciclos. Su
limitación permanece explícita: el Excel no contiene un árbol multinivel, por
lo que estas pruebas no afirman haber verificado niveles externos inexistentes.

## Tiempos P16 observados

Entorno indicado por la prueba: FastAPI TestClient, Docker Python 3.12 y
PostgreSQL 16, con 5,000 dispositivos activos. No es una prueba de carga ni una
medición de latencia del navegador.

| Consulta | Filas/total observado | Segundos observados |
|---|---:|---:|
| Página 2, tamaño 25, dispositivos activos | 25 / 5,000 | 0.050643 |
| Búsqueda `000123`, tamaño 10 | 1 / 1 | 0.055387 |
| Clase Hardware, dispositivos activos, tamaño 17 | 17 / 5,000 | 0.081323 |
| Búsqueda más detalle del CI | Un CI sobre 5,000 dispositivos | 0.1025 |

Estas cifras provienen del `perf_counter` ejecutado y guardado en P16, no de
estimaciones. Los límites/duraciones de I0–I6 y los objetivos SLA no se usan
como supuestas mediciones de rendimiento.

## Pantallas sobre el conjunto demo

```bash
docker compose -p catalogo-demo-app -f compose.yaml -f compose.validation.yaml exec -T frontend npm run build
docker run --rm --network host --env-file .e2e.env -v "$PWD/frontend:/work" -w /work mcr.microsoft.com/playwright:v1.63.0-noble sh -c 'npm ci && npx playwright test --reporter=list'
```

Resultado: **41 módulos compilados en 1.84 s y 15 E2E aprobadas en 19.0 s**, sin
omisiones. Se incluyeron el portal, consola, administración, FAQ y tablero con
cantidades por proceso/prioridad además de cola/estado. La captura del tablero
se revisó visualmente; muestra el corte durante las E2E, por lo que puede incluir
sus solicitudes adicionales.

Registros: [demo-2026-10-28](demo-2026-10-28/), con los tres reportes de generación,
verificación de IDs, compilación, E2E, capturas y limpieza. La corrida inicial de
aceptación está en `aceptacion-2026-10-28-inicial`: sus 63 métodos pasaron, pero
Vite rechazó el alias interno `frontend` en la comprobación HTTP. Se corrigió
la petición del harness usando el Host localhost permitido, sin abrir
`allowedHosts`, y se repitió la aceptación completa hasta obtener salida 0.

## Entorno y cierre

Servidor autorizado, directorio `/home/servidor/catalogo-demo-validacion`.
La aplicación demo usó loopback 18000/15173 y su base no publicó puerto.
La aceptación usó loopback 18001/15174 y base separada sin puerto publicado.
Los demás proyectos del servidor no se modificaron.

Se retiraron únicamente los contenedores de estos proyectos, sin borrar
volúmenes. Los datos demo y de aceptación permanecen conservados. Las claves
temporales demo/E2E se eliminaron y `.env` remoto conserva permisos 600. No se
hizo un despliegue público. Los avisos de dependencias de desarrollo ya
registrados en las etapas anteriores permanecen en los logs; no se modificaron
las versiones para preparar esta demostración.
