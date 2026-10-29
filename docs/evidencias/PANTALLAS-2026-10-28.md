# Validación de pantallas y tiempos

Punto de control de la etapa 6, 28 de octubre de 2026, anterior a la incorporación
del generador de la etapa 7. Commit base:
`7255835b653ebd1b948d0c97a41cfffaacbb7a85`; árbol de trabajo modificado, sin
atribuir las nuevas funciones al commit base. Los 121 archivos ejecutados se
identifican mediante los manifiestos SHA256 del registro.

| Comando/verificación | Entrada | Esperado | Obtenido | Salida |
|---|---|---|---|---|
| `docker compose -p catalogo-pantallas-tests -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from backend-tests` | Fixtures aislados, reloj fijo y suites del parcial/CMDB/Desk/procesos/pantallas | Reglas y regresiones aprobadas | 58 métodos, sin omisiones, 72.699 s | 0 |
| `docker compose -p catalogo-pantallas-app -f compose.yaml -f compose.validation.yaml up -d --build --wait` | Base nueva y migraciones 001–006 | Aplicación levantada, API y BD saludables | Arranque correcto | 0 |
| `docker compose -p catalogo-pantallas-app -f compose.yaml -f compose.validation.yaml exec -T frontend npm run build` | React con portal, consola, administración, FAQ y tablero | Compilación de producción | 41 módulos, 1.75 s | 0 |
| `docker run --rm --network host --env-file .e2e.env -v "$PWD/frontend:/work" -w /work mcr.microsoft.com/playwright:v1.63.0-noble sh -c 'npm ci && npx playwright test --reporter=list'` | Cuentas sintéticas y aplicación real | Perfiles, FAQ, tablero y regresiones navegables | 15 casos, sin omisiones, 17.8 s | 0 |
| `bash scripts/verify_experience_persistence.sh` | Datos de la base exclusiva de pruebas | Conteos/huellas de ciclos, FAQ y datos previos iguales tras reinicio | Comparación idéntica | 0 |
| Snapshot de aplicación y reinicio de PostgreSQL | 46 servicios, 5,000 dispositivos, dos tickets/ciclos, seis FAQ, un adjunto y 32 acciones | Mismos datos y API recuperada | Conteos y checksums idénticos | 0 |
| Comparación SHA256 | Código local frente al copiado al servidor | Correspondencia de las fuentes ejecutadas | 121 archivos coincidentes | 0 |

Entorno: Ubuntu 24.04.4, Docker 29.3.0, Compose v5.1.1; contenedores Python 3.12,
PostgreSQL 16, Node 22 y Playwright 1.63.0. Directorio remoto
`/home/servidor/catalogo-pantallas-validacion`; proyectos propios
`catalogo-pantallas-tests` y `catalogo-pantallas-app`. API/frontend se publicaron
solo en loopback 18000/15173 y la base de aplicación no publicó puerto.

Se probaron ámbitos propios/de cola en servidor; borradores FAQ invisibles al
autoservicio; escritura reservada a administrador; límite exacto de objetivos;
promedios sin convertir pendientes en cero; transferencia sin reiniciar reloj;
reapertura con ciclo nuevo y objetivo adoptado. La migración se ejecutó además
en un esquema temporal de la base de pruebas para comprobar que no inventa
objetivos históricos.

Los registros, snapshots y capturas están en
[pantallas-2026-10-28](pantallas-2026-10-28/). Se revisó visualmente
`tablero-solicitante.png`. `npm ci` mantiene el aviso ya conocido de una
vulnerabilidad alta en dependencias de desarrollo; no se cambiaron versiones.
Se retiraron estos contenedores sin eliminar volúmenes y se borraron archivos
temporales de credenciales. `.env` remoto conserva permisos 600.

El código posterior de demostración/aceptación amplía esta revisión; sus
resultados y huellas se registran por separado, no se atribuyen a esta corrida.
