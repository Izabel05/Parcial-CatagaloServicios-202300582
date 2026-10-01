# scripts

Utilidades reproducibles para preparar datos, validar la estructura y automatizar tareas de desarrollo.

El importador ejecutable está en `backend/app/importer/catalog_importer.py` y se ejecuta con `python -m backend.app.importer`. Lee la hoja `Servicios Externos`, normaliza las filas con `COD.N2`, aplica las reglas de celdas combinadas y valida los controles de 12 códigos de nivel 1 y 46 códigos de nivel 2.

Para crear un usuario local, con la base levantada:

```powershell
python scripts/create_user.py --username admin --email admin@local.test --display-name "Administrador"
```

La contraseña se solicita de forma interactiva y se almacena con Argon2id. Los datos de perfil se guardan cifrados con AES-256-GCM.
