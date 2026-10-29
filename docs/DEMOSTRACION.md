# Preparar y recorrer la demostración

Los datos son sintéticos y la generación es explícita: no se ejecuta al arrancar
normalmente la aplicación y no elimina datos para conseguir los conteos esperados.

## Preparación desde el repositorio

1. Prepare `.env` y su clave como indica README. No reutilice la clave pública del
   harness de aceptación en una instalación normal.
2. Levante la aplicación y espere a que termine la carga del catálogo:

   ```powershell
   docker compose up --build -d --wait
   ```

3. Ejecute el generador dentro del backend:

   ```powershell
   docker compose exec backend python scripts/prepare_demo.py --seed 202300582
   ```

El JSON de salida contiene cantidades, IDs, estados, categorías, vínculos y
notificaciones. Las claves aleatorias de las cuentas nuevas se muestran **una
sola vez por stderr**, separadas del reporte sin secretos de stdout. Guárdelas
localmente para evaluar; no las copie a Git ni a las evidencias. En PostgreSQL se
guardan hashes Argon2id, nunca esas claves en texto plano.

## Cuentas y datos

| Usuario | Rol principal | Uso |
|---|---|---|
| demo-admin | administrador | Colas, permisos, catálogo, CMDB y FAQ. |
| demo-consulta | consulta | Comprobar lectura y rechazo de escrituras. |
| demo-solicitante | solicitante | Crear/consultar sus tickets y confirmar cumplimiento. |
| demo-agente1 | agente | Tomar, atender, asignar y transferir. |
| demo-agente2 | agente | Segundo agente para verificar competencia por la asignación. |
| demo-aprobador | aprobador | Aprobar/rechazar sin ser creador, solicitante ni beneficiario. |

Se crean siete colas `DEMO-<PROCESO>`, con permisos de consulta/atención/transferencia
para agentes, consulta/aprobación para aprobador y solo consulta para el rol consulta.
El administrador conserva su política general. Los objetivos iniciales son
60 minutos calendario para primera atención y 480 para resolución.

Se generan **37 tickets**, identificados por lote, proceso e índice:

| Proceso | Cantidad | Etapas de los ejemplos |
|---|---:|---|
| Nuevos servicios | 5 | solicitud, análisis, pendiente aprobación, implementación, cerrado |
| Cambios | 5 | solicitud, evaluación, pendiente aprobación, ejecución, cerrado |
| Incidentes | 7 | registro, clasificación, diagnóstico, atención, recuperado, resuelto, cerrado |
| Eventos | 5 | registro, evaluación, respondido, cerrado, clasificación |
| Problemas | 5 | registro, investigación, error conocido, solución definitiva, cerrado |
| Accesos | 5 | solicitud, validación, pendiente aprobación, provisión, cerrado |
| Servicios de tecnología | 5 | solicitud, validación, cumplimiento, confirmación, cerrado |

Los incidentes cubren I0–I6, duración estimada/real, prioridad y redundancia. Los
eventos cubren E0–E3; los E2/E3 respondidos se vinculan a incidentes existentes
del mismo servicio y registran notificación persistente. El E3 de ejemplo se
vincula con el incidente I6. Otro E2 permanece antes de su respuesta para evaluar
el avance. Los problemas vinculan incidentes y un cambio correctivo cerrado.
Los nuevos servicios del conjunto vinculan uno ya existente, por lo que no
duplican el catálogo original; la prueba automatizada también cubre crear uno.

Los tickets se crean y recorren con los servicios de negocio y actores de cada
rol, sin escribir estados directamente en SQL ni desactivar las validaciones.
Las evidencias de implementación, pruebas o provisión son simuladas y están
rotuladas como sintéticas; no se ejecutan operaciones en dispositivos reales.
Sus marcas horarias proceden de la transacción de generación y no representan
mediciones de desempeño humano. Los tiempos P16 sí se miden durante las pruebas.
La duración registrada de un incidente es un dato distinto del tiempo de atención
del ticket y puede describir un hecho anterior a su creación.

Se prepara un lote de **5,000 dispositivos** del generador `hardware-v1`, dos
dependencias técnicas para recorrer el grafo y los enlaces CI–servicio. El
reporte separa cantidad total y etiquetas distintas, y muestra distribución por
nivel y clase. Los únicos nombres observados en la fuente son Hardware y Software;
se conservan como raíces mientras no exista otro árbol verificable. Los dispositivos
físicos de este lote son Hardware; Software no se cuenta artificialmente como
dispositivo para alcanzar el mínimo.

## Repetición y recuperación

Repetir el mismo comando usa `(semilla, versión, proceso, índice)` y reutiliza los
37 tickets. No restablece sus etapas, responsables, comentarios, aprobaciones ni
las claves de las cuentas ya existentes. Los dispositivos de la misma semilla se
actualizan conforme a la política del generador CMDB sin duplicarse. Otra semilla
crea otro conjunto identificado y puede incrementar los totales.

Una transacción protege el lote y todos sus tickets; un fallo en los recorridos
revierte ese bloque. La preparación previa de cuentas, colas y CMDB puede haber
quedado realizada y se reutiliza al reintentar. Existe una prueba que introduce
deliberadamente una excepción para demostrar el rollback de tickets y lote.

Para recuperar claves demo perdidas, de forma **explícita**:

```powershell
docker compose exec backend python scripts/prepare_demo.py --seed 202300582 --rotate-passwords
```

Esto rota únicamente las seis cuentas demo y revoca sus sesiones. No lo haga
durante una evaluación con sesiones abiertas. Si una cuenta existe con otro rol
o está inactiva, o una cola se cambió de proceso/desactivó, el generador se detiene
sin sobrescribir esa decisión. El borrado de datos queda fuera del generador.

## Recorrido sugerido

1. Solicitante: buscar `[DEMO 202300582]`, abrir una solicitud y consultar su historia.
2. Agente: revisar sus colas, tomar un ticket inicial y avanzar hasta que falte una evidencia.
3. Aprobador: decidir un cambio o acceso pendiente; mostrar que el solicitante no puede hacerlo.
4. Eventos: consultar E0/E1 y las correlaciones/notificaciones de E2/E3 del reporte.
5. Problemas: navegar sus incidentes y el cambio correctivo.
6. CMDB: buscar un dispositivo del lote, revisar sus atributos y recorrer dependencias.
7. FAQ y Tablero: buscar una respuesta y comparar tickets abiertos, ciclos y objetivos calendario.

Las pruebas se ejecutan en **otra base**, nunca sobre este conjunto. Instrucciones
y matriz P01–P18: [PRUEBAS.md](PRUEBAS.md).

Ejecución comprobada y reportes reales:
[37 tickets, 5,000 dispositivos y repetición sin duplicados](evidencias/DEMO-ACEPTACION-2026-10-28.md).
