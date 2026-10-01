# AGENTS.md

## Alcance

Estas instrucciones aplican a todo el repositorio.

## Organización

- Mantener el frontend y el backend desacoplados.
- Colocar la lógica de negocio en `backend/app/services/`.
- Mantener el acceso a datos en `backend/app/repositories/`.
- Usar los controladores para coordinar solicitudes y respuestas, sin duplicar lógica de negocio.
- Agregar pruebas en `tests/` junto con cada funcionalidad nueva.
- Registrar decisiones funcionales y técnicas en `docs/`.

## Convenciones

- Escribir documentación y nombres de dominio en español cuando corresponda al proyecto.
- Usar nombres descriptivos y evitar archivos monolíticos.
- No subir secretos. Usar `.env` local y actualizar `.env.example` cuando se agregue una variable.
- Mantener `data/CatalogoServicios.xlsx` como fuente de datos de desarrollo, sin incluir información sensible.
- No almacenar contraseñas en texto plano ni cifrarlas con AES. Usar el servicio Argon2id existente.
- Usar AES-256-GCM únicamente para datos recuperables que requieran confidencialidad, con una clave fuera del repositorio.
- Toda ruta protegida debe validar la sesión en el servidor; la visibilidad de un botón no es una regla de autorización.

## Validación

Antes de entregar cambios, ejecutar las pruebas disponibles y validar que la aplicación pueda levantarse con Docker Compose.
