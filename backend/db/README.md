# Base de datos

La base de datos local usa PostgreSQL y se inicializa automáticamente al crear el volumen por primera vez.

- `00_schema.sql`: tablas, claves, índices y controles de importación.
- `../app/importer/catalog_importer.py`: importador idempotente que lee el Excel original y registra cada ejecución.

El esquema SQL se monta en `/docker-entrypoint-initdb.d/` y el backend ejecuta el importador después de que PostgreSQL responde al healthcheck. Para reconstruir los datos de prueba, consultar el procedimiento destructivo documentado en el README raíz.
