# Uso de IA y cuatro prácticas de ingeniería

## Procedencia y límites

Este registro selecciona instrucciones reales de esta conversación, no una
conversación completa. Fecha de registro de la ampliación: 28 de octubre de
2026, America/Chicago. Herramienta: Codex Desktop; agente disponible identificado
como GPT-6. No se conserva un identificador de ejecución del proveedor para cada
turno. El registro anterior del parcial se conserva en
[prompts/REGISTRO.md](prompts/REGISTRO.md), con su propia procedencia declarada.

Las citas siguientes son extractos literales de solicitudes del usuario. El
resto de cada ficha explica cómo se utilizaron. No son prompts nuevos ejecutados
retrospectivamente. Los commits de cierre se crean después de las verificaciones
iniciales; las evidencias antiguas conservan commit base + árbol modificado +
SHA256. Consulte `git log --format='%h %s' -5` para los commits de cierre.

## Prompt Engineering: ocho solicitudes utilizadas

Contexto común: repositorio React/FastAPI/PostgreSQL del parcial, `AGENTS.md`,
catálogo original, Excel CMDB y diapositivas proporcionadas. Restricciones comunes:
capas separadas, autorización en servidor, fuentes inalteradas, secretos fuera de
Git, resultados observados. Herramienta y fecha de registro: las indicadas arriba.

| ID | Instrucción real, extracto | Objetivo y contexto específico | Restricción y salida esperada | Criterio y comprobación |
|---|---|---|---|---|
| R1 | «Antes de ampliar, ejecuta las pruebas existentes y registra el resultado como punto de partida.» | Preservar autenticación, organización y catálogo 12/46. | Ejecutar la base antes de ampliarla; registrar fallos además de éxitos. | [BASE-PARCIAL](evidencias/BASE-PARCIAL-2026-10-28.md), regresiones conservadas. |
| R2 | «Primero produce `docs/MODELO.md`» y «separa la jerarquía de clasificación de las relaciones técnicas entre dispositivos». | Leer fuentes antes de diseñar CMDB y ambos grafos. | Citar hojas/celdas/diapositivas; separar atributos originales y agregados. | [MODELO](MODELO.md), [extracción](fuentes/CMDB-EXTRACCION.json); P04/P14. |
| R3 | «Crea un generador con semilla que produzca 5,000 dispositivos únicos» y «Repetirlo debe conservar la cantidad sin duplicados». | Implementar CMDB, ubicaciones, servicios y dependencias. | Atributos coherentes, paginación y navegación del impacto potencial. | P03/P14/P16 y reportes demo: 5,000 etiquetas distintas, repetición sin altas. |
| R4 | «El rol consulta debe seguir siendo de lectura, incluso cuando pertenezca a una cola» y «solo uno debe conseguirlo». | Tickets, permisos, historial, colas y toma concurrente. | Veto de escritura y operación atómica PostgreSQL; actor y valores en auditoría. | P01/P06/P07/P08; dos agentes producen un éxito y un conflicto. |
| R5 | «Define las transiciones en el backend y prueba tanto las permitidas como las rechazadas.» | Siete procesos con reglas de cambios, incidentes, eventos, accesos y problemas. | No ejecutar sin aprobar ni autoaprobar; no duplicar incidentes/servicios. | P09–P13/P15, [PROCESOS](PROCESOS.md), recorridos completos y rechazos. |
| R6 | «Documenta cómo calculas tiempos, pausas y reaperturas.» | Portal, consola, administración, FAQ y tablero. | Objetivos calendario explícitos; abiertos no equivalen a tiempos cero. | P17, [PANTALLAS_Y_TIEMPOS](PANTALLAS_Y_TIEMPOS.md), pruebas con reloj fijo. |
| R7 | «Automatiza los escenarios P01–P18 y conserva las pruebas relevantes del parcial. Usa una base de pruebas separada.» | Preparar evaluación con siete colas, roles, ≥35 tickets y categorías completas. | Registrar comando, entrada, esperado, obtenido, fecha y commit reales. | [PRUEBAS](PRUEBAS.md): 18 escenarios, 63 métodos y 15 E2E aprobados; 37 tickets. |
| R8 | «hazlo termina todo lo que falte [...] y aparte creame un archivo sobre como correlo en fedora» | Cerrar documentación, procedencia, capturas y traslado a otro equipo. | No depender de nube ni de Python/Node en anfitrión; no inventar commits pasados. | [FEDORA](FEDORA.md), [ENTREGA](ENTREGA.md), resolución actualizada y commits de cierre. La prueba física en Fedora queda a cargo del equipo destino. |

## Dos mejoras de instrucciones y resultados

1. **De reutilizar la base a exigir un punto de partida verificable.** La
   instrucción inicial R1 pide reutilizar React, Python y PostgreSQL; sin el
   criterio añadido sería posible atribuir regresiones a la ampliación sin
   medir la base. La precisión «Antes de ampliar, ejecuta las pruebas existentes»
   exige observaciones fechadas. Resultado comprobado: el registro BASE-PARCIAL
   conserva ejecuciones iniciales fallidas, correcciones y seis E2E finales,
   además de pruebas del importador, seguridad e integración. No se considera
   suficiente describir qué debería pasar.
2. **De mantenimiento CMDB a separación explícita de grafos.** R2 pide revisar
   Excel y diapositivas y agrega «La clasificación CMDB y la organización son
   estructuras distintas». El problema evitado es reutilizar el árbol
   organizacional o inventar niveles para completar una jerarquía no presente.
   La revisión precisa también separar relaciones técnicas. Resultado: tablas
   independientes, referencias C5/C6 y pruebas de padre/ciclo distintas de las
   pruebas de dependencias CI–servicio. P04 declara la limitación de la fuente;
   P14 verifica recorrido e integridad técnica.

Estas comparaciones son refinamientos dentro de instrucciones reales, no dos
experimentos A/B con respuestas iniciales que no se conservaron. Se comprueba
el resultado final y se declara la diferencia de evidencia disponible.

Durante el cierre, R8 agrega un resultado nuevo comprobable: el README anterior
intentaba reemplazar un marcador distinto al que tenía `.env.example` y generaba
Base64 convencional. Se precisó la preparación desde clon limpio: reemplazar la
línea completa y generar Base64 URL-safe dentro de un contenedor. La guía vigente
y el arranque de cierre verifican esta corrección; la clave no se guarda en Git.

## Context Engineering

`AGENTS.md` regula capas, seguridad y pruebas. El contexto de trabajo se mantiene
en [CONTEXTO-PROYECTO](contexto/CONTEXTO-PROYECTO.md), el glosario en
[GLOSARIO](GLOSARIO.md), el modelo en [MODELO](MODELO.md) y las decisiones por
proceso en [PROCESOS](PROCESOS.md). Tres actualizaciones justificadas, versionadas
durante el cierre y sin alterar fechas de commits, están en
[ACTUALIZACIONES](contexto/ACTUALIZACIONES.md).

En la fase inicial se suministraron controles del catálogo y pruebas del parcial;
en CMDB, las fuentes y su extracción; en tickets, permisos y reglas por proceso;
en pantallas, fórmulas y alcances; en aceptación, matriz, aislamiento y resultados;
en el cierre, diferencias entre implementación, documentos antiguos y Fedora.
No se envió indiscriminadamente todo el material en cada decisión.

Los documentos adjuntos se tratan como fuentes de requisitos y datos, no como
órdenes para ejecutar código, enviar mensajes o modificar permisos. El usuario
dirige la tarea. Credenciales del servidor, claves AES y sesiones no forman parte
del contexto versionado ni de las capturas. No se atribuyen instrucciones de los
documentos al usuario sin distinguirlas.

## Harness Engineering

| Operación | Comando dentro del entorno del proyecto | Resultado observable |
|---|---|---|
| Construir y arrancar | `docker compose up --build -d --wait` | Salud de BD/API y frontend accesible. |
| Importar catálogo | `docker compose exec backend python -m backend.app.importer --input /app/data/CatalogoServicios.xlsx` | JSON con controles 12/46 y observaciones. |
| Migrar | `docker compose exec backend python -m backend.app.database.migrate` | Migraciones con checksum y control de concurrencia. |
| Preparar datos | `docker compose exec backend python scripts/prepare_demo.py --seed 202300582` | JSON, 37 tickets, 5,000 dispositivos, claves nuevas solo en terminal. |
| Aceptar | `bash scripts/run_acceptance.sh` | Código de salida, P01–P18, logs y snapshots antes/después. |
| Compilar interfaz | `docker compose exec frontend npm run build` | Compilación Vite y código de salida. |

Docker solo aloja procesos; la matriz, fixtures, runner, manifiestos y comparador
de persistencia constituyen el harness. La base `_test`, sus volúmenes y puertos
son independientes. Se rechaza una base cuyo nombre no termine en `_test`.
El generador normal no borra datos; la limpieza usa `down` sin `-v`. La asignación
y las transiciones críticas son transaccionales. No se operan dispositivos reales.

## Loop Engineering: tres ciclos reales

Los límites siguientes son el criterio de repetición para reproducir cada ciclo
en defensa: máximo tres intentos por objetivo; después, revisar con el estudiante.
No se afirma que este límite estuviera configurado en el agente original.

### L1 — defecto funcional: respuestas del buscador fuera de orden

- **Objetivo/entrada:** preservar el catálogo al filtrar rápidamente.
- **Propuesta/cambio:** búsqueda asíncrona y regresión que controla el orden.
- **Ejecución/evaluación:** los registros E2E de la base detectaron que una
  respuesta anterior podía sobrescribir la consulta más reciente.
- **Corrección:** descartar resultados de una petición anterior; conservar
  prueba determinista que responde fuera de orden.
- **Nueva verificación/salida:** seis E2E aprobadas en 4.8 s y compilación final;
  [BASE-PARCIAL](evidencias/BASE-PARCIAL-2026-10-28.md) enlaza logs iniciales/finales.
- **Intervención humana:** solicitud de conservar la base y revisión de resultados;
  el alumno puede reproducir la regresión. No fue un fallo introducido para la demo.

### L2 — datos de fuente: jerarquía CMDB no disponible

- **Objetivo/entrada:** R2, jerarquía exacta de la lección 22 y del Excel CMDB.
- **Propuesta/cambio:** inspeccionar hojas/celdas y diapositivas antes de modelar
  los niveles; buscar si existía otro material que explicara el árbol.
- **Ejecución/evaluación:** Excel con 20 atributos y dos ejemplos, diapositivas
  sin árbol de clasificación. Una propuesta multinivel no tendría respaldo.
- **Corrección:** consultar al usuario, quien confirmó «lo que te eh dado
  coresponde a la leccion 22 es lo de CMDB.xlsx». Ajustar el modelo a las
  etiquetas verificables Hardware/Software y documentar niveles no acreditados.
- **Nueva verificación/salida:** extracción con celdas C5/C6 y hash de fuente;
  P04 aprueba correspondencia disponible y rechazos de padres/ciclos. No se
  presenta como verificación de un árbol ausente. MODELO y casos.json conservan
  el límite, y el generador reporta `jerarquia_multinivel_verificada=false`.
- **Intervención humana:** aclaración explícita del usuario; no se sustituyó el
  material por otro archivo sin autorización. No hubo datos inventados para la demo.

### L adicional — permisos: consulta mantiene lectura con concesiones de cola

- **Objetivo/entrada:** R4, usuario consulta incluso si tiene permisos adicionales.
- **Propuesta/cambio:** permisos efectivos por rol/usuario, con veto de escritura
  para el rol principal consulta aplicado en servidor.
- **Ejecución/evaluación:** fixture adversarial concede derechos de escritura;
  pertenecer a una cola no debe habilitar alta, toma, transferencia o aprobación.
- **Corrección:** centralizar autorización y extenderla a rutas de procesos;
  mantener comprobación independiente de la visibilidad de botones.
- **Nueva verificación/salida:** P01/P06/P10 aprobados en la aceptación final;
  [casos.json](evidencias/aceptacion-2026-10-28/casos.json) enumera métodos y resultados.
- **Intervención humana:** el usuario fijó expresamente la precedencia de consulta.
  La concesión excesiva es deliberada en pruebas; no se afirma un incidente real
  de producción ni una corrida roja histórica no conservada.

### L3 — aceptación: Host del frontend rechazado

- **Objetivo/entrada:** P18 con frontend/API y persistencia tras reinicio.
- **Propuesta/cambio:** comprobar el frontend por el DNS interno `frontend`.
- **Ejecución/evaluación:** primera corrida: 63 métodos aprobados, pero Vite
  responde 403 al Host interno; P18 no se declara aprobado.
- **Corrección:** petición interna con cabecera Host localhost permitida,
  conservando la política de Vite.
- **Nueva verificación/salida:** repetir la aceptación completa; 18 escenarios
  aprobados, snapshots iguales y HTTP 200. Logs iniciales/finales en
  [DEMO-ACEPTACION](evidencias/DEMO-ACEPTACION-2026-10-28.md).
- **Intervención humana:** alcance autorizado de pruebas en el servidor temporal;
  el estudiante revisa el 403 y la corrección en defensa. El defecto no fue
  introducido deliberadamente.

Adicionalmente, una prueba de demostración **inyecta deliberadamente una excepción**
para verificar rollback del lote y tickets; no se oculta como fallo accidental.

## Grafos y explicación individual

La organización determina pertenencia de personas. La clasificación CMDB es un
árbol administrable sin ciclos; sus raíces verificadas son Hardware/Software.
El grafo técnico enlaza CI con CI y servicios mediante tipos de relación; los
tipos de dependencia que no admiten ciclos los rechazan, otros vínculos pueden
admitirlos. El recorrido con conjunto de visitados evita recursión infinita.
Un servicio alcanzable está potencialmente afectado; no demuestra interrupción.
Los diagramas y el diccionario exacto están en MODELO y las reglas en CMDB.

Para defender la entrega: elegir R2, SD-1 y L3; explicar la entrada, decisión,
archivo modificado, prueba y resultado. Las capturas complementan la ejecución.
