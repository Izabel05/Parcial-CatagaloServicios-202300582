# Evidencias

Espacio para capturas, resultados de pruebas y evidencias de ejecución. No
incluir secretos ni datos personales.

## Punto de partida para Service Desk

La [verificación del 28 de octubre de 2026](BASE-PARCIAL-2026-10-28.md)
registra las pruebas del parcial antes de ampliar sus módulos, las incidencias
detectadas y las correcciones verificadas.

La [validación CMDB](CMDB-2026-10-28.md) registra la generación reproducible
de 5,000 dispositivos, pruebas de backend/interfaz, persistencia y registros
de ejecución de la ampliación.

La [validación de Service Desk](SERVICE-DESK-2026-10-28.md) registra tickets,
colas, permisos, toma concurrente, adjuntos y regresiones de los módulos previos.

La [validación de los siete procesos](PROCESOS-2026-10-28.md) registra
transiciones permitidas/rechazadas, aprobaciones, correlación de eventos,
pruebas de interfaz y persistencia.

La [validación de pantallas y tiempos](PANTALLAS-2026-10-28.md) registra
los ámbitos de portal/consola, publicación de FAQ y métricas calendario por ciclo.

La [demostración y aceptación P01–P18](DEMO-ACEPTACION-2026-10-28.md) registra
37 tickets reproducibles, 5,000 dispositivos, 63 pruebas backend, 15 E2E y
reinicio de contenedores con snapshots idénticos.

## Organización de las fotografías

- `../Imagenes/DockerEjecucion.png`: construcción y arranque saludable de Docker.
- `../Imagenes/EjecucionPrueba.png`: creación del entorno aislado de pruebas.
- `../Imagenes/P12Ejecuccion.png`: persistencia después de reiniciar el contenedor.
- `../Imagenes/PruebaIntegracion.png`: prueba de integración aprobada dentro de
  Docker (`Ran 1 test`, `OK`).
- `../Imagenes/PruebaE2EOmitida.png`: ejecución Playwright con seis casos
  omitidos; demuestra el arranque del harness, pero no una aprobación E2E.
- `../Imagenes/PruebaUnitariaPyhton.png`: ejecución omitida; no representa una
  prueba aprobada. La nueva captura de integración la reemplaza para ese
  escenario, pero todavía falta una captura de las pruebas unitarias.

La explicación y las imágenes están integradas en
[`docs/RESOLUCION.md`](../RESOLUCION.md). Antes de subir nuevas capturas,
verifica que no aparezcan contraseñas demo, claves AES, tokens ni valores
completos del archivo `.env`.
