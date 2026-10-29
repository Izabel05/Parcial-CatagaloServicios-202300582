# Punto de partida del parcial 2

Fecha: 28 de octubre de 2026. Código evaluado: `7255835b653ebd1b948d0c97a41cfffaacbb7a85`.
Esta comprobación precede a la ampliación Service Desk; no acredita módulos nuevos.

## Entorno y aislamiento

Se ejecutó una copia obtenida con `git archive` en Ubuntu 24.04.4, Docker
29.3.0 y Docker Compose v5.1.1, en el servidor autorizado. El equipo Windows
local no tiene el comando Docker disponible.

- Directorio remoto: `/home/servidor/catalogo-baseline-7255835`.
- Integración: proyecto `catalogo-baseline-7255835`, base `catalogo_servicios_test`.
- Aplicación: proyecto `catalogo-baseline-app`, con volumen propio.
- Persistencia: proyecto `catalogo-servicios-tests`, utilizado por el script existente.
- La aplicación se publicó únicamente en loopback: frontend `127.0.0.1:15173`,
  API `127.0.0.1:18000`; PostgreSQL de la aplicación no se publicó.
- Se generó una clave local y cuentas demo exclusivamente en la copia remota.
  No se incluyen claves, contraseñas, sesiones ni archivos `.env` en esta evidencia.

El Excel original no se modificó. SHA-256 de `data/CatalogoServicios.xlsx`:
`de3b478a5faeeeaebce1aa7726e0e3321188a68e41bbb656e1d17b0c5b74dcf0`.

## Controles ejecutados

| Control | Resultado observado | Salida |
|---|---|---|
| Unitarias del importador y seguridad | 6 pruebas aprobadas, 5.773 s, sin omisiones | 0 |
| Integración del parcial P01-P11 | 1 método con múltiples escenarios aprobado, 6.036 s, sin omisiones | 0 |
| Persistencia P12 | Marcador conservado después de reiniciar PostgreSQL | 0 tras ajustes del entorno |
| Arranque Compose | Construcción y arranque correctos; base y API saludables | 0 |
| Salud API | `{"status":"ok","database":"ok"}` | HTTP 200 |
| Frontend | Página inicial accesible | HTTP 200 |
| Compilación React | Vite 7.3.6, 32 módulos, compilación en 1.66 s | 0 |
| Interfaz tras correcciones | 6 casos aprobados, 4.7 s, sin omisiones | 0 |
| Interfaz con regresión de respuestas fuera de orden | 6 casos aprobados, 4.8 s, sin omisiones | 0 |
| Compilación final tras las correcciones | 32 módulos, compilación en 1.65 s | 0 |

La integración comprueba credenciales válidas e inválidas, rechazo sin sesión,
revocación por logout, usuario inactivo, lectura y rechazo de escritura del rol
consulta, creación de jerarquía y usuario, duplicados y referencias inválidas,
importación 12/46, repetición con cero creados y 46 sin cambios, conflicto SE.12,
validación mínimo/máximo, filtros y rechazo de responsables de otra sección.
Es un único método de prueba; no debe contarse como once pruebas independientes.

Registros completos, conservados como texto para versionarlos:

- [Unitarias](base-2026-10-28/unit.txt) e [integración](base-2026-10-28/integration.txt).
- [Persistencia inicial fallida](base-2026-10-28/persistence.txt) y
  [persistencia aprobada](base-2026-10-28/persistence-fixed.txt).
- [Arranque](base-2026-10-28/startup.txt) y [estado de Compose](base-2026-10-28/compose-ps.txt).
- [E2E inicial](base-2026-10-28/e2e.txt),
  [segundo selector ambiguo](base-2026-10-28/e2e-fixed.txt),
  [mensaje de validación incorrecto](base-2026-10-28/e2e-final.txt),
  [carrera del buscador](base-2026-10-28/e2e-corrected.txt),
  [suite corregida](base-2026-10-28/e2e-verified.txt) y
  [suite con regresión determinista](base-2026-10-28/e2e-regression.txt).
- [Compilación final](base-2026-10-28/frontend-build-final.txt),
  [hashes de archivos evaluados](base-2026-10-28/hashes.txt) y
  [apagado](base-2026-10-28/shutdown.txt).

Los hashes finales del componente y de las pruebas coinciden entre el servidor
y este árbol de trabajo. Al terminar se retiraron únicamente los contenedores y
redes de verificación con `down`, sin `-v`. Los volúmenes se conservaron y se
eliminaron los archivos temporales de credenciales demo y variables E2E. La
clave de la copia aislada permanece en su `.env` remoto con permisos 600.

Las unitarias comprueban además atributos desconocidos, observaciones de
importación, hash Argon2id y recuperación de perfiles con AES-GCM.

## Comandos

Desde el directorio de la copia remota:

```bash
docker compose -f compose.test.yaml -p catalogo-baseline-7255835 run --build --rm backend-tests
docker compose -f compose.test.yaml -p catalogo-baseline-7255835 run --rm backend-tests python -m unittest -v tests.backend.test_importer_rules tests.backend.test_security
# Liberar el puerto 55432 antes de usar el otro proyecto de pruebas:
docker compose -f compose.test.yaml -p catalogo-baseline-7255835 stop db
bash scripts/verify_persistence.sh
```

La definición `compose.baseline.yaml` utilizada junto a `compose.yaml` fue:

```yaml
services:
  db:
    ports: !reset []
  backend:
    ports: !override
      - "127.0.0.1:18000:8000"
    environment:
      FRONTEND_ORIGINS: http://127.0.0.1:15173
  frontend:
    ports: !override
      - "127.0.0.1:15173:5173"
    environment:
      VITE_API_URL: http://127.0.0.1:18000
```

Estas etiquetas requieren Compose compatible con `!override` (2.24.4 o superior).
Son ajustes de la copia de verificación; no se cambió el Compose normal.

```bash
docker compose -f compose.yaml -f compose.baseline.yaml -p catalogo-baseline-app up --build -d
docker compose -f compose.yaml -f compose.baseline.yaml -p catalogo-baseline-app exec -T frontend npm run build
curl -fsS http://127.0.0.1:18000/health
curl -I http://127.0.0.1:15173/
```

Para E2E se ejecutó `scripts/create_demo_users.py` en el backend aislado. Se
proporcionaron las credenciales generadas mediante `.e2e.env` con permisos 600,
sin imprimirlas ni incorporarlas a Git. Ese archivo define `E2E_ADMIN_USER`,
`E2E_ADMIN_PASSWORD`, `E2E_CONSULTA_USER`, `E2E_CONSULTA_PASSWORD` y
`E2E_BASE_URL=http://127.0.0.1:15173`.

```bash
docker run --rm --network host --env-file .e2e.env \
  -v "$PWD/frontend:/work" -w /work \
  mcr.microsoft.com/playwright:v1.63.0-noble \
  sh -c 'npm ci && npx playwright test --reporter=list'
```

Las ejecuciones posteriores reutilizaron las dependencias de `npm ci` y
ejecutaron solamente `npx playwright test --reporter=list` en ese contenedor.

## Incidencias y corrección

1. La exportación inicial desde Windows convirtió el script Bash a CRLF y
   `bash scripts/verify_persistence.sh` terminó con código 2 al interpretar
   `set -Eeuo pipefail`. Se normalizó la copia remota a LF. Se agrega
   `.gitattributes` con `*.sh text eol=lf` para conservar el formato al clonar
   o exportar. Se verificó con `git check-attr` y una exportación local con
   `git archive --worktree-attributes`: cero secuencias CRLF en el script.
2. La primera ejecución normalizada de P12 terminó con código 1: el proyecto
   de integración de esta misma verificación ya ocupaba el puerto 55432.
   Se detuvo únicamente su base y se repitió P12 satisfactoriamente.
3. Se intentó extraer el archivo transferido antes de que terminara la copia
   SCP. Falló la preparación y Compose no encontró su archivo. Se esperó la
   transferencia completa y se repitió la extracción antes de ejecutar pruebas.

4. La primera suite E2E ejecutó seis casos: cinco aprobados y P09 fallido.
   Los selectores parciales de `Código` y después `Nombre` también encontraban
   el buscador. Se limitaron al formulario de alta y se usó coincidencia exacta.
5. Con los selectores corregidos, P09 llegó al servidor y descubrió un defecto
   funcional: el rango inválido se rechazaba, pero la interfaz mostraba
   `[object Object]`. `ServiceBrowser.jsx` ahora extrae los mensajes `msg` de
   los errores de validación de FastAPI, conservando los errores de texto.
   No se relajó la validación del servidor ni el resultado esperado de la prueba.
6. Una ejecución posterior encontró un fallo intermitente de P10: el buscador
   conservaba `SE.12`, pero los resultados mostraban los 46 servicios. El efecto
   de React permitía que una respuesta inicial tardía sustituyera la del filtro.
   Ahora su limpieza invalida las respuestas anteriores. P10 se amplió para
   retener la respuesta sin filtro, entregar primero la filtrada y liberar
   después la antigua; debe conservar los tres resultados de SE.12.

Las correcciones están en el árbol de trabajo posterior al commit base indicado;
no se creó un commit automáticamente. Los registros distinguen las ejecuciones
iniciales y las posteriores a estas correcciones.

No fue necesario cambiar la lógica del backend de autenticación, organización,
roles, repositorios, servicios ni importación. Las pruebas anteriores son
evidencia de regresión de su alcance actual, no una auditoría exhaustiva.
