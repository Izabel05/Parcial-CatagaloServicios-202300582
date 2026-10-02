# Registro de prompts utilizados

Fecha de registro: 2026-10-01. Herramienta: Codex Desktop, modelo GPT-5.

Estos registros resumen solicitudes realmente utilizadas durante la construcción;
no son prompts inventados para simular resultados.

## Prompt 1 — estructura inicial

- **Objetivo:** crear la separación `frontend`, `backend`, `src`, `tests`,
  `scripts`, `docs` y archivos base.
- **Contexto:** proyecto de catálogo de servicios para el parcial.
- **Restricciones:** frontend React/Vue/JS y backend Python con MVC por capas.
- **Salida esperada:** estructura de carpetas, README y archivos de ejecución.
- **Aceptación:** frontend y backend desacoplados y documentación inicial.

## Prompt 2 — PostgreSQL e importador

- **Objetivo:** crear la base local persistente e importar el Excel original.
- **Contexto:** hoja `Servicios Externos`, rangos `A4:L4`, filas 5–101 y listas
  `E112:H122`.
- **Restricciones:** 12 niveles 1, 46 niveles 2, importación repetible,
  celdas combinadas, conflicto `SE.12`, ausencias y trazabilidad.
- **Salida esperada:** esquema, importador, resumen y documentación.
- **Aceptación:** no duplicar registros y conservar incidencias.

## Prompt 3 — autenticación

- **Objetivo:** implementar login, logout, sesiones, roles y protección real.
- **Contexto:** usuarios locales en PostgreSQL.
- **Restricciones:** Argon2id para contraseñas, AES solo para datos recuperables,
  autorización en servidor y secretos fuera de Git.
- **Salida esperada:** endpoints, dependencias de autorización y pruebas.
- **Aceptación:** consulta no modifica y el logout invalida la sesión.

## Prompt 4 — organización y usuarios

- **Objetivo:** implementar CRUD y bajas lógicas para Empresa→Área→Departamento
  →Sección→Puesto→Usuario.
- **Restricciones:** padres activos, códigos únicos dentro del padre, sin huérfanos
  y política de dependencias.
- **Salida esperada:** tablas, repositorios, servicios, rutas y pruebas P04/P05.
- **Aceptación:** relaciones recuperables y sin hashes expuestos.

## Prompt 5 — servicios y validaciones

- **Objetivo:** mantener niveles, catálogos, filtros, ficha y responsables.
- **Restricciones:** mínimo≤máximo, opciones controladas y usuario responsable de
  la misma sección.
- **Salida esperada:** CRUD de servicios y UI administrativa.
- **Aceptación:** crear, editar, desactivar, buscar y rechazar referencias inválidas.

## Prompt 6 — pruebas de seguimiento

- **Objetivo:** automatizar P01–P12 y aislar los datos de prueba.
- **Restricciones:** no destruir el volumen de evaluación; separar unitarias,
  integración, E2E y persistencia.
- **Salida esperada:** pruebas reproducibles y comandos documentados.
- **Aceptación:** cada escenario tiene una prueba o rutina verificable.

## Iteraciones documentadas

1. **Importador:** el diseño inicial de ejecución SQL no distinguía correctamente
   bloques `DO $$...$$`; se revisó y se cambió a un parser por líneas que preserva
   esos bloques. El control del esquema y las pruebas unitarias volvieron a pasar.
2. **Interfaz:** la primera interfaz permitía consultar y crear, pero no editar ni
   dar de baja servicios; se revisó el alcance y se agregaron edición, baja lógica,
   filtros, ficha completa y pruebas Playwright.
