# Auditoría de cumplimiento, seguridad y reproducción

Revisión del 28 de octubre de 2026 (hora del cliente, UTC−06:00). Base:
`46c978d3445c0ac660c67831205485de8a5c9f80`. Las correcciones se ejecutan antes
del commit de cierre: los registros declaran árbol modificado y conservan
huellas del código. No se atribuyen a ese commit base los cambios posteriores.

## Hallazgos corregidos

| ID | Hallazgo e impacto | Corrección y comprobación |
|---|---|---|
| A01 | El apartado 8 pide consultar tickets desde un CI; la ficha solo tenía auditoría del inventario. | Endpoint paginado y panel de tickets con bitácora. El filtro de permisos se aplica antes del conteo. Regresión con colas privadas, solicitantes distintos, consulta, paginación, 401 y 404; prueba de navegador. |
| A02 | La notificación E2/E3 existía en BD, pero no se veía en la ficha. | Fecha/mensaje visibles y enlace al incidente autorizado. Se mantienen la unicidad y la correlación transaccional; API y navegador verifican el recorrido. |
| A03 | Un GET de ticket podía insertar el flujo si faltaba su fila. | El alta crea el flujo en la misma transacción. GET usa SELECT y, ante un registro heredado incompleto, genera solo una representación de lectura. La prueba simula ese registro y verifica que no aparece una fila nueva. |
| A04 | Tras correlacionar un evento se podían cambiar servicio o CI, contradiciendo el incidente vinculado. | Se rechazan esos cambios con 409; la regresión verifica que conserva el servicio y la misma notificación. |
| A05 | `npm audit` identificó un paquete Vite con avisos, incluido uno alto. | Vite 7.3.6 → 7.3.7, versión y lockfile actualizados; auditoría y pruebas de interfaz repetidas. |
| A06 | La resolución de los requirements originales daba avisos en Starlette 0.48.0 y Cryptography 46.0.7. | FastAPI 0.162.0 permite Starlette 1.10.0; Cryptography se fija en 50.0.2. Se repite aceptación, cifrado, autenticación y navegador. Se conserva inventario `pip freeze`. |
| A07 | Compose ignoraba variables de puerto/API, usaba `npm install` y no esperaba la salud del frontend. | Puertos configurables y publicados en loopback, `npm ci`, URL API desde entorno y healthcheck HTTP de Vite. Arranque comprobado con el Compose principal, sin override. |
| A08 | El contexto de construcción no excluía todos los archivos locales de credenciales y dumps. | `.dockerignore`/`.gitignore` incluyen `.env.*`, `.e2e.env`, `.demo*` y dumps; `.env.example` permanece disponible. Comprobación de archivos y claves privadas antes de publicar. |
| A09 | El enunciado del parcial aportado como texto no estaba en las fuentes de entrega. | Copia original `data/fuentes/Parcial_Practico_2.txt`, sin convertirla a PDF; hash y procedencia en MODELO. |
| A10 | Un permiso de consulta concedido directamente a un solicitante funcionaba por API pero no habilitaba la consola. | Los espacios se derivan también de permisos efectivos. Se verifica lectura de cola, veto de atención sin rol agente y retirada de acceso al revocar la concesión. |

La migración **008** agrega únicamente un índice por CI/ticket. Las migraciones
001–007 y los cuatro archivos fuente originales de catálogo/CMDB/Service Desk
se conservan. Se preservan capas, Argon2id, AES-GCM, sesiones revocables y
autorización de servidor; no se incorporan proveedores de modelos ni servicios
de pago.

El historial desde CI muestra las asociaciones actuales, incluidos tickets ya
resueltos/cerrados. Si se corrige una asociación, sus valores anteriores quedan
en la bitácora del ticket; no se presenta una asociación eliminada por corrección
como si siguiera vigente.

## Alcance contrastado con el enunciado

| Apartados | Implementación y evidencia |
|---|---|
| 2–3 Fuentes y parcial | MODELO, F01–F06, controles 12/46 y regresiones de importación/auth/organización. |
| 4–5 Tickets, colas y roles | P01/P05–P08/P15; notas/adjuntos, auditoría, consulta, toma concurrente y bajas protegidas. |
| 6–7 Procesos y lección 25 | P09–P13/P17; siete rutas, aprobaciones, E0–E3, I0–I6, FAQ y métricas calendario. |
| 8 CMDB | P03/P04/P14/P16; 5,000 únicos, semilla, filtros, clases disponibles, grafo y A01. |
| 9 Ingenierías | IA, contexto versionado, prompts seleccionados, harness y ciclos con resultados reales. |
| 10–11 Ejecución y pruebas | Compose, migraciones, base `_test`, P01–P18, snapshot tras reinicio y datos demo. |
| 12 Entregables | README, RESOLUCION, MODELO, PROCESOS, IA, PRUEBAS, fuentes, código y comandos. |

Resultados, comandos, fechas, entradas y salidas de la auditoría:
[evidencias de auditoría](evidencias/AUDITORIA-2026-10-28.md). Los registros
anteriores permanecen como historia de su versión, no se reemplazan por éxitos
retroactivos. La galería anterior de 23 capturas sigue disponible; esta fase
agrega capturas del historial de tickets y de la notificación visible.

## Fuentes de las actualizaciones de seguridad

Se consultaron los avisos de [Vite/launch-editor](https://github.com/advisories/GHSA-587h-7wmj-h5pm)
y [acceso a archivos de Vite](https://github.com/advisories/GHSA-rq7h-c2jc-7f22),
las [notas de FastAPI](https://fastapi.tiangolo.com/release-notes/),
las [correcciones de Starlette](https://starlette.dev/release-notes/) y el
[changelog de Cryptography](https://cryptography.io/en/latest/changelog/).
Los metadatos de PyPI confirmaron versiones y requisitos compatibles antes de
construir. La comprobación automatizada se basa en los reportes npm/pip-audit
guardados, no solo en estas referencias. No se hace `audit fix --force` ni se
modifican versiones sin ejecutar las regresiones.

## Límites que se mantienen explícitos

- El Excel CMDB entregado no contiene un árbol multinivel: se conservan
  Hardware/Software y los atributos verificables. La estudiante confirmó que
  ese es el material de la lección 22; no se inventan niveles para aparentar P04.
- Las comprobaciones Docker se realizan en el servidor temporal Ubuntu. El
  arranque físico en el Fedora de destino y la defensa individual corresponden
  al equipo/estudiante; FEDORA y ENTREGA explican cómo verificarlos.
- «Sin avisos» se refiere a la base de advisories consultada y al conjunto
  resuelto en esta fecha; no es una certificación de ausencia de vulnerabilidades.
  No se realizó una prueba de carga ni una auditoría del sistema operativo remoto.
- La aplicación es local y el Compose publica loopback; no se solicita nube ni
  se presenta esta configuración de desarrollo como un despliegue público.
