# Registro de prompts utilizados

Fecha de registro: 2026-10-01. Herramienta: Codex Desktop, modelo GPT-5.

Estos registros resumen solicitudes realmente utilizadas durante la construcción;
no son prompts inventados para simular resultados.

## Prompt 1 — estructura inicial

- **Rol:** arquitecto de software responsable de preparar la base técnica del
  repositorio.
- **Objetivo:** crear la separación `frontend`, `backend`, `src`, `tests`,
  `scripts`, `data` y `docs`, junto con los archivos base del proyecto.
- **Contexto:** sistema de gestión del catálogo de servicios para el parcial de
  Software Avanzado, con frontend y backend desacoplados.
- **Entrada:** listado de carpetas y archivos solicitados; frontend con React y
  JavaScript; backend Python con una estructura MVC organizada por capas.
- **Formato:** árbol de directorios ejecutable, archivos README y configuración
  inicial de Docker y Compose.
- **Criterio:** la estructura puede clonarse y ejecutarse, mantiene desacoplados
  frontend y backend y respeta las responsabilidades definidas en `AGENTS.md`.

## Prompt 2 — PostgreSQL e importador

- **Rol:** ingeniero de datos y backend encargado de modelar PostgreSQL y la
  importación reproducible del catálogo.
- **Objetivo:** crear una base local persistente e importar el archivo Excel
  original sin modificarlo.
- **Contexto:** la hoja `Servicios Externos` utiliza encabezados en `A4:L4`,
  datos en las filas 5–101 y listas de opciones en `E112:H122`.
- **Entrada:** `data/CatalogoServicios.xlsx`, controles de 12 códigos de nivel 1
  y 46 de nivel 2, celdas combinadas, conflicto `SE.12`, atributos ausentes y
  requisitos de trazabilidad e idempotencia.
- **Formato:** esquema SQL, importador ejecutable por comando, resumen de
  creados, actualizados, omitidos y observados, más documentación de reglas.
- **Criterio:** repetir la importación no genera duplicados, se conservan 12
  niveles 1 y 46 niveles 2 y todas las incidencias quedan registradas.

## Prompt 3 — autenticación

- **Rol:** especialista de seguridad de aplicaciones responsable de la
  autenticación y autorización local.
- **Objetivo:** implementar inicio y cierre de sesión, sesiones revocables y los
  roles `administrador` y `consulta`.
- **Contexto:** las cuentas se validan contra PostgreSQL sin proveedores
  externos y las rutas protegidas deben autorizarse en el servidor.
- **Entrada:** usuarios locales, Argon2id para contraseñas, AES-256-GCM solo para
  datos recuperables, usuarios activos/inactivos y secretos fuera de Git.
- **Formato:** endpoints de autenticación, servicios, repositorios, dependencias
  de autorización y pruebas automatizadas.
- **Criterio:** las credenciales inválidas y usuarios inactivos son rechazados,
  `consulta` no puede modificar y el logout impide reutilizar la sesión.

## Prompt 4 — organización y usuarios

- **Rol:** desarrollador backend responsable del dominio organizacional y del
  mantenimiento de usuarios.
- **Objetivo:** implementar altas, consultas, modificaciones y bajas lógicas para
  Empresa → Área → Departamento → Sección → Puesto → Usuario.
- **Contexto:** cada entidad tiene un único padre, un puesto puede tener varios
  usuarios y la empresa del usuario se obtiene recorriendo su jerarquía.
- **Entrada:** datos mínimos de cada entidad, padres activos, códigos únicos
  dentro del padre, prohibición de huérfanos y política de dependencias activas.
- **Formato:** tablas, repositorios, servicios, controladores, rutas, pantallas y
  pruebas de los escenarios P04 y P05.
- **Criterio:** las relaciones son válidas y recuperables, no se crean registros
  huérfanos y las respuestas nunca exponen hashes ni secretos.

## Prompt 5 — servicios y validaciones

- **Rol:** desarrollador full stack responsable del catálogo funcional de
  servicios.
- **Objetivo:** mantener niveles 1 y 2, catálogos controlados, filtros, ficha
  completa y asignaciones de responsables.
- **Contexto:** los servicios importados pueden quedar sin asignación, mientras
  los datos demo deben contener al menos tres asignaciones válidas.
- **Entrada:** campos originales del Excel, catálogos de clase, criticidad y tipo,
  regla `mínimo ≤ máximo`, sección responsable y usuario opcional de esa sección.
- **Formato:** API CRUD, validaciones de servidor, formularios con opciones
  controladas, búsqueda, filtros, paginación y ficha legible.
- **Criterio:** se puede crear, editar, consultar y desactivar; las referencias
  inválidas, rangos incorrectos y responsables de otra sección son rechazados.

## Prompt 6 — pruebas de seguimiento

- **Rol:** ingeniero de calidad responsable del harness de pruebas y de sus
  evidencias reproducibles.
- **Objetivo:** automatizar los escenarios P01–P12 y aislar completamente sus
  datos del entorno de evaluación.
- **Contexto:** la solución utiliza Python `unittest`, FastAPI `TestClient`,
  Playwright, PostgreSQL y Docker Compose.
- **Entrada:** matriz P01–P12, cuentas demo locales, base de pruebas separada,
  volumen persistente y prohibición de destruir los datos de evaluación.
- **Formato:** pruebas unitarias, de integración, E2E y persistencia, comandos de
  ejecución, resultados fechados y capturas sin secretos.
- **Criterio:** cada escenario tiene una prueba o rutina verificable, los datos
  están aislados y los resultados distinguen claramente aprobados de omitidos.

## Iteraciones documentadas

1. **Importador:** el diseño inicial de ejecución SQL no distinguía correctamente
   bloques `DO $$...$$`; se revisó y se cambió a un parser por líneas que preserva
   esos bloques. El control del esquema y las pruebas unitarias volvieron a pasar.
2. **Interfaz:** la primera interfaz permitía consultar y crear, pero no editar ni
   dar de baja servicios; se revisó el alcance y se agregaron edición, baja lógica,
   filtros, ficha completa y pruebas Playwright.
