# Catálogo de servicios, CMDB y Service Desk

Ampliación del parcial 2 de Software Avanzado: React/Vite, FastAPI y PostgreSQL.
Conserva autenticación, organización, usuarios y catálogo original 12/46; añade
CMDB y siete procesos con colas, permisos, auditoría, FAQ y tablero.

Auditoría final: **P01–P18, 71 pruebas backend y 18 E2E aprobadas**.
[Hallazgos corregidos y evidencia](docs/AUDITORIA.md).

## Arranque desde un clon limpio

Se necesitan Git, Docker Engine con Compose y Bash. Python, PostgreSQL y Node se
ejecutan en contenedores. Para instalar y ejecutar en Fedora, seguir
[docs/FEDORA.md](docs/FEDORA.md), incluida la preparación de la clave local.

```bash
git clone https://github.com/Izabel05/Parcial-CatagaloServicios-202300582.git
cd Parcial-CatagaloServicios-202300582
cp .env.example .env
```

Generar una clave sin instalar Python en el anfitrión; reemplaza cualquier
marcador de `APP_ENCRYPTION_KEY` y guarda el archivo con permisos locales:

```bash
umask 077
clave_local=$(docker run --rm python:3.12-slim python -c 'import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())')
sed -i "s|^APP_ENCRYPTION_KEY=.*|APP_ENCRYPTION_KEY=$clave_local|" .env
unset clave_local
chmod 600 .env
docker compose up --build -d --wait
docker compose exec backend python scripts/prepare_demo.py --seed 202300582
```

Guardar las contraseñas demo que se muestran **solo una vez en la terminal**.
El generador prepara seis cuentas, siete colas, 37 tickets y 5,000 dispositivos;
repetir con la misma semilla no duplica el lote ni restablece su avance.

| Cuenta | Uso |
|---|---|
| `demo-admin` | Administración de catálogo, CMDB, usuarios, colas y FAQ. |
| `demo-consulta` | Evaluar lectura y rechazo de escritura. |
| `demo-solicitante` | Portal y confirmación de solicitudes propias. |
| `demo-agente1`, `demo-agente2` | Atención y competencia por la toma de un ticket. |
| `demo-aprobador` | Aprobaciones independientes. |

Abrir [frontend](http://localhost:5173), [salud API](http://localhost:8000/health)
y [Swagger](http://localhost:8000/docs). Puertos del Compose principal:
5173 frontend, 8000 API y `${POSTGRES_PORT:-5432}` PostgreSQL. Las variables
`BACKEND_PORT`, `FRONTEND_PORT` y `POSTGRES_PORT` configuran los puertos de
Compose, publicados en loopback. Si cambias API/frontend, ajusta también
`VITE_API_URL` y `FRONTEND_ORIGINS` como explica FEDORA.md.

## Pruebas y operación

```bash
bash scripts/run_acceptance.sh
docker compose exec frontend npm run build
docker compose ps
docker compose logs --tail=100 backend frontend db
docker compose stop
docker compose start
```

La aceptación usa otra base y conserva evidencia en
`docs/evidencias/aceptacion-local/`. No destruye la demostración. Para retirar
contenedores conservando datos: `docker compose down`; para recuperarlos:
`docker compose up -d --wait`. No agregar `-v` si se quieren conservar datos.
La clave `.env` debe conservarse junto con cualquier respaldo de la BD,
fuera de Git. No existe contraseña fija de evaluación versionada.

## Entregables y evidencias

| Documento | Contenido |
|---|---|
| [RESOLUCION](docs/RESOLUCION.md) | Alcance actual, arquitectura, decisiones y limitaciones. |
| [MODELO](docs/MODELO.md) | Entidades, diccionario, celdas/diapositivas y diferencias entre fuentes. |
| [CMDB](docs/CMDB.md) | Generación, clasificación y dependencias. |
| [SERVICE_DESK](docs/SERVICE_DESK.md) / [PROCESOS](docs/PROCESOS.md) | Base común y siete flujos, permisos y transiciones. |
| [PANTALLAS_Y_TIEMPOS](docs/PANTALLAS_Y_TIEMPOS.md) | Portal, consola, FAQ y métricas calendario. |
| [FRONTEND](docs/FRONTEND.md) | Diseño actualizado, navegación adaptable y reproducción de capturas. |
| [AUDITORIA](docs/AUDITORIA.md) | Cumplimiento, correcciones de permisos/CMDB, dependencias y resultados vigentes. |
| [Galería de 23 capturas](docs/evidencias/FRONTEND-2026-10-28.md) | Siete procesos, roles, CMDB, portal, FAQ, tablero y móvil; 16 E2E aprobadas. |
| [IA](docs/IA.md) | Ocho solicitudes reales, contexto, harness y ciclos de corrección. |
| [PRUEBAS](docs/PRUEBAS.md) | Matriz P01–P18, aislamiento y comandos. |
| [DEMOSTRACION](docs/DEMOSTRACION.md) | Cuentas, datos, repetición y recorridos. |
| [FEDORA](docs/FEDORA.md) | Instalación, arranque, pruebas y recuperación en el equipo destino. |
| [ENTREGA](docs/ENTREGA.md) | Lista de entrega, capturas y defensa individual. |
| [Resultados reales](docs/evidencias/DEMO-ACEPTACION-2026-10-28.md) | 18 escenarios, 63 métodos y 15 E2E de la ampliación. |
| [Verificación del cierre](docs/evidencias/CIERRE-2026-10-28.md) | Repetición de aceptación y Compose sobre un commit del cierre. |

Estructura: `frontend/` cliente, `backend/app/services/` reglas,
`backend/app/repositories/` SQL, `backend/db/migrations/` migraciones,
`scripts/` automatización, `tests/` pruebas y `data/` fuentes originales.
Las contraseñas usan Argon2id y los perfiles recuperables AES-256-GCM.
Toda autorización se valida en el servidor.

Histórico del parcial: [resolución original](docs/RESOLUCION-PARCIAL.md).
La clasificación CMDB no se confunde con la organización ni con el grafo técnico.
El Excel proporcionado no acredita una jerarquía multinivel: la limitación se
declara en MODELO y P04. No se requiere infraestructura en la nube.
