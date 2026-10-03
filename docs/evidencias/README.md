# Evidencias

Espacio para capturas, resultados de pruebas y evidencias de ejecución. No
incluir secretos ni datos personales.

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
