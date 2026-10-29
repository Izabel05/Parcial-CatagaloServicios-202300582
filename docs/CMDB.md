# Uso y operación de la CMDB

La CMDB amplía React, Python y PostgreSQL conservando las sesiones y roles del
parcial. `administrador` mantiene datos; `consulta` puede leer, buscar y
recorrer dependencias. Cada ruta valida la sesión y los permisos en el servidor.

## Preparación en Docker

```bash
docker compose up --build -d
docker compose exec backend python scripts/create_demo_users.py
docker compose exec db psql -U catalogo -d catalogo_servicios -c "SELECT id,username FROM users WHERE is_active ORDER BY id;"
```

El último comando permite elegir el ID de un usuario activo existente. No
guardar las credenciales que genera el script en Git. Con ese ID, ejecutar:

```bash
docker compose exec backend python scripts/generate_cmdb.py --seed 202300582 --count 5000 --responsable-id ID_USUARIO
```

Repetir el mismo comando informa cero creados, 5,000 actualizados y 5,000
dispositivos en el lote. No agrega otro conjunto de dispositivos. Una semilla
o versión diferente identifica otro lote. No se permite reducir un lote
existente mediante `--count`; una limpieza de prueba tendría que ser explícita.
El arranque normal no genera ni borra dispositivos.

Las migraciones se ejecutan automáticamente después del importador del catálogo,
también con volúmenes existentes. Para aplicarlas manualmente:

```bash
docker compose exec backend python -m backend.app.database.migrate
```

El registro `schema_migrations` guarda nombre y checksum normalizado de cada SQL.
Cada ejecución está protegida mediante bloqueo transaccional. Una migración ya
aplicada con contenido distinto se rechaza; no editar migraciones publicadas,
sino agregar otra.

## Datos y alcance de la clasificación

El generador utiliza **Hardware**, el tipo observado en `CMDB!C5`; Software
(`C6`) se conserva como otro tipo y no se cuenta como dispositivo físico.
Ambos se crean con `origen=fuente` y referencia de celda. No se inventan
subcategorías docentes. La configuración de nuevas clasificaciones por el
administrador queda identificada como proyecto y tiene historial de cambios.

La jerarquía docente multinivel no está en el material entregado; esa
limitación de [MODELO.md](MODELO.md) sigue vigente y el reporte devuelve
`jerarquia_docente_multinivel_verificada=false`. La autorización para continuar
esta implementación permite generar datos bajo el tipo disponible, sin afirmar
que se haya cumplido la correspondencia de niveles aún no documentados.

Se generan nombres, series y etiquetas sintéticos estables. Los atributos de
proyecto aplicables a Hardware son `memoria_gb`, `almacenamiento_gb`,
`sistema_operativo` e `ip`. Memoria/capacidad se validan como enteros positivos;
IP es texto válido y opcional: solo un tercio del lote la tiene. No se pretende
que esos atributos sean listas transcritas del Excel ni información de equipos
reales. La ubicación `SINTETICA` es una ubicación del proyecto.

Todos los dispositivos referencian un usuario activo existente, una ubicación,
Hardware y un servicio activo existente. Los servicios se distribuyen por
código en orden estable. Los códigos `SYN-...` quedan reservados al generador.
Su repetición restaura los campos sintéticos de su lote, vuelve a activarlos y
registra antes/después; puede sobrescribir ediciones manuales de esos campos.
No elimina otras relaciones ni datos ajenos al lote. Si cambia el catálogo
activo, puede agregar la nueva asociación determinista y conservar las previas.

Los 20 atributos originales tienen representación operativa: los datos del CI,
las referencias literales de relaciones y padres/hijos, fechas/descripción de
cambio originales y documentación/referencias a tickets. Los textos originales
no crean relaciones o tickets automáticamente. No hay importador del Excel CMDB
en esta etapa: el generador usa sus tipos documentados y la interfaz admite los
campos; la importación de las dos filas de ejemplo permanece pendiente. El
catálogo de servicios conserva su importador y controles 12/46.

## Interfaz

Abrir la aplicación y seleccionar la pestaña **CMDB**:

1. Buscar por código o nombre, filtrar por clasificación, ubicación, estado o
   dispositivo físico, y navegar páginas de 25 registros.
2. Abrir un código para ver atributos, clasificación completa, relaciones,
   servicios y últimas 100 acciones del CI.
3. Como administrador, crear o editar CI con el formulario; para un dispositivo
   físico se requieren etiqueta única, clasificación Hardware, ubicación y
   responsable activos. Campos ausentes se conservan como nulos.
4. Mantener clasificaciones y ubicaciones, indicar un padre al crear una
   clasificación y resolver sus dependencias antes de desactivarlas.
5. En la ficha, vincular/desvincular servicios y crear, editar o desactivar
   relaciones. El ID del CI destino aparece junto a cada resultado de búsqueda.
6. Abrir los CI vecinos o seleccionar **Ver servicios potencialmente afectados**
   para obtener servicios y rutas de dependencia explicativas.

Los atributos técnicos se introducen como JSON; por ejemplo:

```json
{"memoria_gb":16,"almacenamiento_gb":512,"sistema_operativo":"Linux sintético"}
```

Los códigos y datos originales pueden leerse sin permisos administrativos.
El software es un CI, pero no un dispositivo físico. Un CI sin ubicación o
responsable puede conservarse si no se marca como dispositivo.

## Relaciones y reglas

- `depende_de` y `alojado_en`: dirigidas; no admiten ciclos, tampoco mezclados.
- `componente_de`: dirigida; no admite ciclos de composición.
- `conectado_a`: simétrica; admite ciclos entre CI distintos; se normaliza la
  pareja para rechazar duplicados inversos.
- No se admiten autorrelaciones. La creación requiere CI activos y motivo.
- Las modificaciones del grafo y clasificación usan un mismo bloqueo
  transaccional, evitando ciclos por carreras entre dos operaciones.
- Las bajas son lógicas. Una clasificación con hijos/CI activos, una ubicación
  con CI activos o un CI con relaciones/servicios activos no puede desactivarse
  hasta resolver esos vínculos. El historial no se elimina desde la API.

El recorrido parte del CI y sigue en sentido inverso las dependencias activas
`depende_de`/`alojado_en`. Incluye los servicios del CI inicial, elimina
duplicados, utiliza visitados y devuelve una ruta por servicio. Por defecto
recorre hasta 5,000 CI; `limit` admite hasta 10,000. Si se alcanza el límite se
indica `truncado=true`. No propaga impacto por conexiones o composición ni
afirma una interrupción efectiva. La jerarquía de clasificación no participa
en este recorrido técnico.

## API

Prefijo `/api/v1/cmdb`; encabezado `Authorization: Bearer TOKEN`.
PUT reemplaza todos los atributos editables del recurso; no es PATCH parcial.

| Ruta | Métodos | Permisos |
|---|---|---|
| `/catalogos/{clasificaciones|ubicaciones}` | GET, POST | Lectura ambos roles; POST administrador |
| `/catalogos/{entidad}/{id}` | PUT, DELETE | Administrador |
| `/ci` | GET, POST | Lectura ambos; POST administrador |
| `/ci/{id}` | GET, PUT, DELETE | Lectura ambos; mantenimiento administrador |
| `/ci/{id}/servicios` | POST | Administrador; cuerpo `servicio_id` |
| `/ci/{id}/servicios/{servicio_id}` | DELETE | Administrador; baja del vínculo |
| `/tipos-relacion` | GET | Ambos roles |
| `/relaciones` | POST | Administrador |
| `/relaciones/{id}` | PUT, DELETE | Administrador |
| `/ci/{id}/dependencias` | GET | Ambos roles |
| `/reporte` | GET | Ambos roles |

Filtros de `/ci`: `search`, `clasificacion_id`, `ubicacion_id`, `activo`,
`es_dispositivo`, `page` y `page_size` (1–100). La clasificación filtra el nodo
exacto; el reporte muestra conteos del subárbol y nivel configurado, sin
sumarlos como total porque los ancestros contarían los mismos dispositivos.
La paginación ordena por código e ID, de forma reproducible.

## Pruebas aisladas

```bash
docker compose -f compose.test.yaml -p catalogo-cmdb-tests run --build --rm backend-tests python -m unittest -v tests.backend.test_importer_rules tests.backend.test_security tests.integration.test_cmdb
bash scripts/verify_cmdb_persistence.sh
```

La base de pruebas se llama `catalogo_servicios_test` y el volumen pertenece
solo al proyecto `catalogo-cmdb-tests`. La suite reinicia su esquema y rechaza
nombres de base que no terminen en `_test`; no apuntarla a una base de evaluación.
El puerto 55432 debe estar libre de otros proyectos de pruebas.

Los escenarios comprueban migración repetible, generación/repetición de 5,000,
unicidad, filtros y páginas, permisos, detalle e historial, mantenimiento,
referencias inválidas, IP inválida, ciclos mixtos, conexiones cíclicas,
duplicados inversos, rutas de impacto y reparentado concurrente. Se conserva
el escenario P01–P11 del parcial. El script de persistencia compara cantidades
y un checksum de datos antes/después de reiniciar PostgreSQL sin borrar volumen.

La suite Playwright incluye `frontend/tests/e2e/cmdb.spec.js`. Requiere las
cuentas E2E documentadas en `tests/README.md` y un lote de exactamente 5,000
dispositivos activos en una instalación de aplicación aislada. Sus pruebas
comprueban búsqueda, ficha, dependencias, lectura por consulta y mantenimiento
de una ubicación por administrador. Los resultados reales y el entorno se
registran en `docs/evidencias/CMDB-2026-10-28.md`.

## Tickets asociados a un CI

La ficha incluye historial paginado por `GET /api/v1/cmdb/ci/{id}/tickets`, con
`page` y `page_size` (máximo 100). Se ordena por fecha e ID descendentes y solo
cuenta/devuelve tickets propios o de colas consultables; administrador conserva
su ámbito autorizado. El total no revela tickets de otras colas. Un CI inexistente
devuelve 404 y una petición sin sesión, 401.

Desde la lista se abre una consulta de ticket y su bitácora ya filtrada por los
permisos habituales de Service Desk. No se duplican operaciones de atención en
CMDB. La migración 008 indexa `(ci_id,ticket_id)` para esta consulta; no altera
las migraciones aplicadas. Pruebas y resultados: [AUDITORIA](AUDITORIA.md).
