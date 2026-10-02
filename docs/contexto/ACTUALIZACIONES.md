# Actualizaciones del contexto

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
