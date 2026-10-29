# Resultados reales P01–P18

Commit base: `4b13cab4475c072c38a8da6e43ee81852205251c`. Árbol modificado: False.
La huella del código ejecutado está en `codigo.json`; los cambios sin commit no se atribuyen al commit base.

| Caso | Fecha UTC | Esperado | Obtenido |
|---|---|---|---|
| P01 · Autenticación y permisos | 2026-10-29T01:12:48.123415+00:00 | Sesiones válidas funcionan; credenciales, sesiones y operaciones no autorizadas se rechazan | APROBADO |
| P02 · Importación repetible 12/46 | 2026-10-29T01:12:48.123429+00:00 | 12 niveles 1, 46 servicios de fuente y observaciones conservadas sin duplicados | APROBADO |
| P03 · CMDB reproducible | 2026-10-29T01:12:48.123435+00:00 | 5000 etiquetas distintas; segunda carga crea cero dispositivos | APROBADO |
| P04 · Correspondencia de fuentes y clasificación | 2026-10-29T01:12:48.123441+00:00 | Etiquetas y referencias de la fuente disponibles preservadas; padres inexistentes y ciclos rechazados; sin inventar niveles ausentes | APROBADO |
| P05 · Referencias de tickets | 2026-10-29T01:12:48.123446+00:00 | Alta válida; referencias inválidas y lectura ajena rechazadas | APROBADO |
| P06 · Roles y usuarios por cola | 2026-10-29T01:12:48.123452+00:00 | Acceso limitado por política, consulta permanece de lectura y no se revoca atención aún asignada | APROBADO |
| P07 · Ordenamiento y toma atómica | 2026-10-29T01:12:48.123456+00:00 | Orden prioridad/antigüedad/ID; resultados 200 y 409 y un solo responsable | APROBADO |
| P08 · Transferencia trazable | 2026-10-29T01:12:48.123460+00:00 | Transferencia válida con bitácora; destino incompatible y escalamiento incorrecto rechazados | APROBADO |
| P09 · Siete recorridos | 2026-10-29T01:12:48.123470+00:00 | Recorridos válidos llegan a cierre y transiciones ilegales se rechazan | APROBADO |
| P10 · Aprobaciones independientes | 2026-10-29T01:12:48.123475+00:00 | Ejecución sin aprobación y autoaprobación rechazadas; ciclo reabierto exige nueva decisión | APROBADO |
| P11 · Eventos E0–E3 | 2026-10-29T01:12:48.123481+00:00 | E0/E1 no generan incidentes; E2/E3 correlacionan sin duplicados; cola equivocada rechazada | APROBADO |
| P12 · Incidentes I0–I6 | 2026-10-29T01:12:48.123485+00:00 | Duraciones y evidencia validadas; prioridades mapeadas y redundancia registrada; contradicciones justificadas o rechazadas | APROBADO |
| P13 · Trazabilidad incidente–problema–cambio | 2026-10-29T01:12:48.123488+00:00 | Vínculos tipados recuperables; problema no se resuelve antes de su cambio | APROBADO |
| P14 · Grafo CI–servicio | 2026-10-29T01:12:48.123492+00:00 | Recorrido devuelve servicios potencialmente afectados; ciclos de dependencia se rechazan y conexiones admitidas se conservan | APROBADO |
| P15 · Resolución, reapertura y actor | 2026-10-29T01:12:48.123497+00:00 | No se omite resolución; nueva versión y bitácora con actor/fecha; ciclo anterior conservado | APROBADO |
| P16 · Paginación y mediciones | 2026-10-29T01:12:48.123502+00:00 | Cantidades/páginas esperadas y tiempos medidos con perf_counter, indicando entorno | APROBADO |
| P17 · Indicadores controlados | 2026-10-29T01:12:48.123508+00:00 | Promedios omiten pendientes, pausa descontada cero y ciclos/objetivos preservados por política de calendario | APROBADO |
| P18 · Reinicio sin pérdida | 2026-10-29T01:13:06.887523+00:00 | Mismos conteos y checksums; catálogo, 5000 dispositivos, tickets e historial conservados; API/frontend HTTP 200 | APROBADO |

Comandos, entradas, métodos, salidas y tiempos completos en `casos.json`.
P04 verifica el material disponible: C5/C6 y B4:U4. No hay árbol multinivel en el Excel y no se inventa uno.
