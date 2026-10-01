# tests

Pruebas automatizadas del proyecto.

- Las pruebas del backend pueden organizarse en `tests/backend/`.
- Las pruebas del frontend pueden organizarse en `tests/frontend/`.
- Las pruebas de integración pueden organizarse en `tests/integration/`.

Prueba de reglas del importador:

```powershell
python -m unittest tests.backend.test_importer_rules tests.backend.test_security
```
