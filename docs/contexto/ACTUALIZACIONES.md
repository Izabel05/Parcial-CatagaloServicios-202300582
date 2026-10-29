# Actualizaciones del contexto

Las tres entradas originales siguientes pertenecen al parcial. Las actualizaciones
Service Desk al final se versionan ahora, durante el cierre; no se presentan como
commits creados antes de las ejecuciones del 28 de octubre.

## Actualización 1 — reglas reales del Excel

- **Hallazgo:** las filas físicas no equivalen a servicios por las celdas
  combinadas y existe el conflicto `SE.12`.
- **Decisión:** recuperar únicamente la celda ancla dentro de su rango,
  conservar variantes del nombre y generar observaciones; no propagar valores
  de forma general.
- **Comprobación:** `python -m backend.app.importer --dry-run` reporta 12
  niveles 1, 46 niveles 2, filas omitidas y observaciones.

## Actualización 2 — seguridad de credenciales

- **Hallazgo:** el requisito pide hash especializado y también cifrado de datos
  recuperables.
- **Decisión:** Argon2id para contraseñas y AES-256-GCM únicamente para el perfil
  recuperable. El hash nunca se cifra de forma reversible ni se devuelve por API.
- **Comprobación:** `tests.backend.test_security` verifica hash, sal, validación
  y cifrado autenticado.

## Actualización 3 — organización y asignaciones

- **Hallazgo:** la jerarquía y las asignaciones son requisitos nuevos y no deben
  atribuirse al Excel.
- **Decisión:** crear tablas organizacionales independientes y un script demo
  que agrega una estructura `DEMO` y tres asignaciones válidas.
- **Comprobación:** la prueba de integración P04/P11 valida creación,
  recuperación y rechazo de una asignación entre secciones distintas.

## SD-1 — alcance y procedencia de fuentes (cierre de entrega)

- **Problema:** el contexto seguía describiendo solo dos roles y el catálogo.
- **Cambio:** `CONTEXTO-PROYECTO.md` incluye siete procesos, separación de los
  tres grafos/estructuras, cinco roles, pruebas aisladas y uso temporal del servidor.
- **Motivo:** impedir que nuevas tareas atribuyan una jerarquía inexistente al
  Excel o conviertan la prueba remota en un requisito de nube.
- **Verificación:** contraste con `MODELO.md`, `PRUEBAS.md` y los reportes reales.
- **Commit:** consultar `git log --format='%h %s' -- docs/contexto/CONTEXTO-PROYECTO.md`;
  entrada con asunto `feat: completa Service Desk y actualiza contexto de fuentes`.

## SD-2 — procedencia de IA, términos y criterios de verificación

- **Problema:** el registro anterior cubría solo seis prompts del parcial; faltaban
  vocabulario común y vínculo entre decisiones, cambios y verificaciones actuales.
- **Cambio:** `IA.md` selecciona ocho solicitudes reales, dos refinamientos y
  tres ciclos; `GLOSARIO.md` distingue CI, cola, ciclo y objetivo calendario.
- **Motivo:** evitar resultados o modelos retrospectivos inventados y aclarar
  que una prueba adversarial no implica una corrida roja histórica conservada.
- **Verificación:** cada ciclo enlaza logs reales y declara fallos deliberados.
- **Commit:** `git log --format='%h %s' -- docs/IA.md`, asunto
  `docs: documenta IA contexto y ciclos con evidencia real`.

## SD-3 — entorno Fedora y cierre reproducible

- **Problema:** la resolución todavía negaba tickets y el arranque del README
  no coincidía con la preparación completa; faltaba el traslado sin nube y SELinux.
- **Cambio:** resolución vigente, README desde clon limpio, FEDORA y ENTREGA;
  montajes compartidos con `z` y preparación de clave dentro de un contenedor.
- **Motivo:** evitar una instalación aparentemente lista con clave inválida o
  errores de acceso en Fedora, y separar evidencia Ubuntu de prueba Fedora futura.
- **Verificación:** instalación contrastada con documentación oficial Docker;
  aceptación y Compose se vuelven a validar en el entorno disponible. La
  comprobación física en Fedora permanece explícitamente pendiente del destino.
- **Commit:** `git log --format='%h %s' -- docs/FEDORA.md`, asunto
  `docs: cierra entrega y prepara ejecucion local en Fedora`.

## SD-4 — interfaz y evidencia visual verificable

- **Solicitud:** «Mejora el frontend y conectate al servidor para tomar las capturas que haga falta».
- **Cambio:** navegación lateral, acceso, portada, fichas y listas legibles,
  tablero en columnas y adaptación móvil; capturador con perfiles de evaluación.
- **Motivo:** las vistas de 980 px apilaban información y las capturas anteriores
  no cubrían todos los procesos. Las imágenes nuevas deben esperar datos reales.
- **Verificación:** 16 E2E, compilación, 23 capturas y 138 huellas coincidentes.
- **Commit de código:** `d40a42a702a2c49a3afbd78c34cb6f37acdbe55e`.
- **Fuentes:** [diseño](../FRONTEND.md) y [resultados](../evidencias/FRONTEND-2026-10-28.md).

## SD-5 — auditoría antes de publicar

- **Solicitud:** auditar, completar faltantes y después hacer commit y push.
- **Cambio:** historial de tickets por CI con permisos, notificaciones visibles,
  lecturas sin escrituras, correlación estable y consola por permisos efectivos;
  dependencias corregidas, arranque configurable y fuente original del parcial.
- **Motivo:** corregir diferencias reales entre el enunciado, la API y las vistas,
  y cerrar los avisos de dependencias antes de publicar.
- **Verificación:** 71 métodos, P01–P18, 18 E2E, Compose, compilación y reportes
  npm/pip-audit. Se conservan fallos iniciales y manifiestos, sin retrofechar.
- **Registro:** [AUDITORIA](../AUDITORIA.md); commit local de cierre y publicación
  en la rama `main` solicitada por el usuario, sin forzar el historial remoto.
