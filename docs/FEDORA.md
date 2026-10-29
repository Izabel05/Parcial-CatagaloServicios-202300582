# Cómo ejecutar y presentar el proyecto en Fedora

Esta es una instalación **local**, sin depender del servidor de pruebas.
Necesitas conexión para descargar paquetes/imágenes, Git, Bash y Docker Compose.
Python, Node y PostgreSQL se ejecutan dentro de contenedores. Los pasos de
instalación Docker se contrastaron con la
[guía oficial para Fedora](https://docs.docker.com/engine/install/fedora/).
Usa una versión mantenida de Fedora compatible con esa guía.

## 1. Instalar Docker Engine y Compose

En una terminal de Fedora:

```bash
sudo dnf install -y dnf-plugins-core git
sudo dnf config-manager addrepo --from-repofile https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Cierra sesión e ingresa de nuevo para aplicar el grupo. El grupo docker concede
control privilegiado del daemon; úsalo para tu usuario local de evaluación.
Si hay paquetes Docker anteriores incompatibles, revisa los conflictos indicados
en la guía oficial antes de sustituirlos. Verifica:

```bash
docker run --rm hello-world
docker compose version
```

Si aparece permiso denegado al socket, comprueba `id -nG` y vuelve a iniciar
sesión. Si el daemon no inicia, consulta `sudo journalctl -u docker -n 80`.
No uses Podman como sustitución implícita: estos comandos se verifican con Docker.

## 2. Obtener la versión entregada

Primero asegúrate de llevar los commits del cierre al equipo Fedora. Crear commits
locales en Windows no los publica automáticamente en GitHub. Puedes subirlos tú
a tu repositorio y clonar, o transferirlos sin publicar mediante un bundle:

En Windows, desde la raíz del proyecto:

```powershell
git bundle create ../service-desk-entrega.bundle main
```

Copia ese archivo a Fedora y clónalo allí:

```bash
git clone -b main /ruta/al/service-desk-entrega.bundle Parcial-CatagaloServicios-202300582
cd Parcial-CatagaloServicios-202300582
git log -5 --oneline
git status --short
```

Si ya publicaste los commits, puedes usar:

```bash
git clone https://github.com/Izabel05/Parcial-CatagaloServicios-202300582.git
cd Parcial-CatagaloServicios-202300582
```

Git/bundle transfiere código, fuentes y evidencias versionadas; no transfiere
`.env` ni volúmenes PostgreSQL. El generador reconstruye una demostración nueva.
Esto no recupera cambios manuales que hayas hecho en la base del servidor.

## 3. Configurar `.env` sin instalar lenguajes

Desde la raíz del repositorio, solo en una instalación nueva:

```bash
cp .env.example .env
umask 077
clave_local=$(docker run --rm python:3.12-slim python -c 'import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())')
test -n "$clave_local"
sed -i "s|^APP_ENCRYPTION_KEY=.*|APP_ENCRYPTION_KEY=$clave_local|" .env
unset clave_local
chmod 600 .env
```

La clave es aleatoria y Base64 URL-safe de 32 bytes. No la reemplaces al reiniciar:
los perfiles ya guardados requieren la misma clave. `.env.example` contiene
valores de BD para desarrollo local, no cuentas reales de producción. Si cambias
la contraseña de PostgreSQL hazlo antes de crear el volumen; cambiar solo `.env`
no cambia una contraseña que PostgreSQL ya tiene almacenada.

## 4. Levantar y generar la demostración

```bash
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
docker compose exec backend python scripts/prepare_demo.py --seed 202300582
```

La primera preparación muestra contraseñas nuevas **una sola vez en la terminal**.
Guárdalas en un gestor o archivo privado fuera del repositorio. No captures esa
terminal con contraseñas. No hay contraseña universal del proyecto.

| Usuario | Rol |
|---|---|
| demo-admin | administrador |
| demo-consulta | consulta |
| demo-solicitante | solicitante |
| demo-agente1 / demo-agente2 | agentes |
| demo-aprobador | aprobador |

Abre `http://localhost:5173`. API: `http://localhost:8000/health`;
documentación interactiva: `http://localhost:8000/docs`. Debes ver siete colas,
37 tickets del lote y 5,000 dispositivos. El catálogo importado mantiene 12/46.
El portal solo muestra los tickets de su solicitante; usa administrador/consola
para inspeccionar todo el conjunto autorizado.

Repite el generador con la misma semilla para demostrar cero tickets nuevos y
5,000 etiquetas distintas. Usar otra semilla agrega otro lote. Si pierdes claves:

```bash
docker compose exec backend python scripts/prepare_demo.py --seed 202300582 --rotate-passwords
```

Esto rota las seis cuentas demo y revoca sus sesiones; cierra tus sesiones antes.

## 5. Pruebas separadas y compilación

```bash
ACCEPTANCE_EVIDENCE_DIR=docs/evidencias/aceptacion-fedora bash scripts/run_acceptance.sh
docker compose exec frontend npm run build
```

El harness recrea solo `catalogo_aceptacion_test`, comprueba P01–P18 y retira sus
contenedores sin borrar volúmenes. Conserva comando/fecha/commit, resultados,
tiempos y snapshots en `docs/evidencias/aceptacion-fedora/`. No alteres reportes
para marcar aprobado: si falla, conserva el log y corrige antes de repetir.
El conjunto normal demo queda separado. Las pruebas E2E de navegador son
adicionales; el procedimiento completo de cuentas está en `tests/README.md`.
La entrega ya incluye su corrida real de 15 E2E sin omisiones.

## 6. Logs, apagado y recuperación

```bash
docker compose logs --tail=100 backend frontend db
docker compose stop
docker compose start
```

También puedes retirar contenedores con `docker compose down` y volver con
`docker compose up -d --wait`. **No uses `down -v` para el apagado:** elimina los
datos. Conserva la misma carpeta/proyecto Compose y la misma `.env` para
reutilizar sus volúmenes. Después de reconstruir una imagen, usa `up --build`.

Para respaldar una instalación con cambios manuales:

```bash
umask 077
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$HOME/service-desk-respaldo.dump"
```

Guarda también `.env` en un medio privado seguro: la copia de BD contiene datos
sensibles y requiere su clave AES para leer perfiles. Para restaurar en una
instalación nueva sin datos propios, con esa misma `.env`, antes de arrancar
backend/frontend (reemplaza las tablas iniciales creadas por el contenedor):

```bash
docker compose up -d db --wait
docker compose exec -T db sh -c 'pg_restore --clean --if-exists --exit-on-error -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "$HOME/service-desk-respaldo.dump"
docker compose up -d --wait
```

Si la BD destino ya tiene datos que quieras conservar, detente: `--clean`
reemplaza tablas. No borres tu instalación para probar la restauración.

## 7. Problemas frecuentes en Fedora

- **SELinux y permisos sobre archivos:** los Compose usan `:z` en montajes del
  repositorio compartidos entre contenedores. Mantén el clon en una carpeta de
  proyecto propia. No desactives SELinux ni relabeles todo `/home`. Consulta
  [etiquetas de montajes Docker](https://docs.docker.com/engine/storage/bind-mounts/#configure-the-selinux-label)
  y revisa `ls -Zd backend data frontend` si hay un error de acceso.
- **Puerto ocupado:** el principal usa 8000/5173; libera el proceso que lo ocupa
  o adapta los puertos y la URL del frontend/origen CORS de forma coherente.
  PostgreSQL permite `POSTGRES_PORT=5433` en `.env`. Aceptación permite
  `ACCEPTANCE_API_PORT`/`ACCEPTANCE_FRONTEND_PORT`; son puertos distintos.
- **API unhealthy:** revisa logs de backend y db; comprueba clave válida y
  credenciales. No elimines el volumen como primera solución.
- **Shell con `\r`:** usa un clon Linux con `.gitattributes`; para una copia
  antigua de archivos Windows, `sed -i 's/\r$//' scripts/*.sh` y repite.
- **Primer arranque lento:** depende de descargas de imágenes y npm. Consulta
  logs; si `--wait` termina antes, repite cuando las dependencias estén listas.
- **Archivos generados por Docker como root:** puedes recuperar propiedad de
  una carpeta concreta de reportes con `sudo chown -R "$USER:$(id -gn)" docs/evidencias/aceptacion-fedora`;
  comprueba primero que esa sea la carpeta de reportes deseada.

## 8. Evidencia que tomar en el equipo destino

Sigue [ENTREGA.md](ENTREGA.md): captura Fedora/Compose, pantalla CMDB y recorrido
del ticket, además del resultado real de aceptación. La ejecución física en tu
Fedora todavía no está registrada; no se presenta la corrida Ubuntu como Fedora.
