# scripts

Utilidades reproducibles para preparar datos, validar la estructura y automatizar tareas de desarrollo.

El importador ejecutable está en `backend/app/importer/catalog_importer.py` y se ejecuta con `python -m backend.app.importer`. Lee la hoja `Servicios Externos`, normaliza las filas con `COD.N2`, aplica las reglas de celdas combinadas y valida los controles de 12 códigos de nivel 1 y 46 códigos de nivel 2.

Para crear un usuario local, con la base levantada:

```powershell
docker compose exec db psql -U catalogo -d catalogo_servicios -c "SELECT id, codigo, nombre FROM puestos WHERE activo ORDER BY id;"
docker compose exec backend python scripts/create_user.py --username admin --email admin@local.test --role administrador --display-name "Administrador" --puesto-id ID_PUESTO_ACTIVO
```

La contraseña se solicita de forma interactiva y se almacena con Argon2id. Los datos de perfil se guardan cifrados con AES-256-GCM.

## Cuentas de evaluación

El siguiente comando crea o actualiza dos cuentas locales, revoca sus sesiones anteriores y muestra las contraseñas solo en la consola:

```powershell
docker compose exec backend python scripts/create_demo_users.py
```

También acepta `--admin-password` y `--consulta-password` para valores temporales
proporcionados localmente. No escribas esos valores en archivos versionados ni en
documentación; para una demostración reproducible, omite los argumentos y copia
las contraseñas aleatorias directamente desde la consola.

El mismo comando crea o reactiva la jerarquía técnica `DEMO` y asigna los tres
primeros servicios importados a la sección y a usuarios demo. Esa asignación es
datos de demostración nuevos; no se lee como si proviniera del Excel.
