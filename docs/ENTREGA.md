# Preparación de entrega, capturas y defensa

## Contenido listo y límites

Se incluyen código, siete migraciones, Dockerfile/Compose, fuentes originales,
importadores, generadores, pruebas y los documentos exigidos. El registro
anterior de 18 escenarios, 63 métodos y 15 E2E conserva su procedencia.
Los commits de cierre documentan el trabajo ahora; no alteran el historial pasado.
Los hashes exactos se localizan con:

```bash
git log --format='%h %s' -- docs/contexto/ACTUALIZACIONES.md
git log -5 --oneline
```

La clasificación de la fuente sigue limitada a Hardware/Software, sin niveles
externos inventados. La instalación física en Fedora se verifica en el equipo
destino siguiendo FEDORA.md. No hace falta publicar la aplicación en la nube.

## Capturas: cuáles, dónde y qué deben mostrar

Las capturas complementan logs y ejecución; no sustituyen las pruebas. Ya existen:

- `docs/evidencias/demo-2026-10-28/tablero-final.png`: tablero calendario revisado.
- `docs/evidencias/demo-2026-10-28/proceso-incidente-final.png`: incidente atendido.
- `docs/evidencias/pantallas-2026-10-28/tablero-solicitante.png`: ámbito del portal.

Para tu presentación en Fedora, guarda las nuevas en
`docs/evidencias/fedora/capturas/`. Usa solo cuentas y contenidos sintéticos.
Puedes crear esa carpeta con `mkdir -p docs/evidencias/fedora/capturas`.

| Archivo sugerido | Dónde tomarla | Contenido visible |
|---|---|---|
| `01-entorno.png` | Terminal Fedora, raíz del proyecto | `cat /etc/fedora-release`, `docker compose version`, `git rev-parse HEAD` y `docker compose ps`. |
| `02-cmdb.png` | Navegador → CMDB → dispositivos | Total de 5,000, filtros y paginación; sin confundir servicios con dispositivos. |
| `03-dependencias.png` | CMDB → detalle de un CI con relaciones | CI relacionado, dependencias y servicios potencialmente afectados. |
| `04-colas.png` | Service Desk → Administración como demo-admin | Las siete colas y sus procesos/permisos. |
| `05-aprobacion.png` | Consola como demo-aprobador → cambio pendiente | Datos del cambio y aprobación con actor independiente; luego mostrar su historial. |
| `06-trazabilidad.png` | Consola → problema de ejemplo | Incidente relacionado, causa raíz y cambio correctivo. |
| `07-evento.png` | Consola → evento E2/E3 respondido | Incidente vinculado y registro de notificación; ID estable tras repetir. |
| `08-portal.png` | Service Desk como demo-solicitante | Portal con tickets propios; abrir FAQ para mostrar autoservicio en la defensa. |
| `09-tablero.png` | Tablero como demo-admin o agente | Cantidades, ámbito y explicación de objetivos calendario. |
| `10-aceptacion.png` | Terminal al terminar el harness | Resumen real P01–P18 aprobado y código de salida; conservar también los logs. |

No mostrar `.env`, contraseñas, claves, cookies, tokens ni pestañas personales.
Anota en un `README.md` de esa carpeta fecha, commit, usuario de evaluación y qué
prueba ilustra cada captura. Si una pantalla no existe o una prueba falla,
registra lo ocurrido en vez de fabricar una imagen de éxito.

## Recorrido de defensa (aproximadamente 12–15 minutos)

1. Arrancar con Compose y mostrar salud, catálogo 12/46 y fuente original.
2. Explicar organización, clasificación y grafo técnico por separado; buscar
   un CI entre 5,000 y recorrer sus servicios potencialmente afectados.
3. Mostrar portal propio y consola por colas; explicar por qué consulta no escribe.
4. Recorrer aprobación de cambio y bloqueo de autoaprobación en accesos.
5. Mostrar correlación de evento y trazabilidad incidente–problema–cambio.
6. Consultar FAQ y explicar cómo tablero trata abiertos, esperas y reaperturas.
7. Abrir IA.md: explicar un prompt refinado, una actualización de contexto,
   el harness y el ciclo de corrección del Host rechazado.
8. Mostrar aceptación y persistencia; localizar servicio, repositorio y prueba
   que cambiarías si el catedrático pide una modificación pequeña.

## Cierre de versión

Antes de presentar, comprueba que llevas los commits nuevos (GitHub o bundle),
ejecuta aceptación en Fedora y conserva reportes con su commit real. Las claves
de evaluación se generan localmente; comunícalas al evaluador por un medio
privado, nunca dentro del repositorio. Incluye solo código/fuentes/evidencias,
sin `.env`, dumps privados, `node_modules` ni volúmenes.

El enunciado fija el 28 de octubre de 2026 como entrega y el 30 como segunda
jornada de calificación del mismo commit, no una prórroga automática. Respeta
la versión y las condiciones indicadas por el catedrático; no retrofeches commits.
