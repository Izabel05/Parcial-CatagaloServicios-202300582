# Interfaz y capturas de la demostración

## Diseño aplicado

La aplicación usa una navegación lateral persistente en escritorio y una barra
desplazable en pantallas pequeñas. El contenido dispone de más ancho y de una
cabecera con sección, rol y sesión. La portada enlaza Service Desk, catálogo,
CMDB, tablero, FAQ y organización; usuarios se muestra al administrador.

La paleta verde petróleo, fondos claros, bordes suaves y tipografía del sistema
se implementan en `frontend/src/workspace.css`. No se descargan fuentes ni se
agregan dependencias. `WorkspaceIcon.jsx` contiene iconos SVG propios del
repositorio; son decorativos y no reemplazan las etiquetas de los controles.
`styles.css` conserva los estilos de dominio previos.

Los listados de tickets y CI separan identificador, descripción y estado; los
filtros mantienen etiquetas visibles. Al abrir un CI o ticket se desplaza la
vista hasta su ficha. El tablero usa columnas para objetivos y distribución,
sin modificar cálculos, muestras ni tiempos calendario. Se conserva el diseño
de tablas con desplazamiento horizontal para datos que requieren varias columnas.

El acceso tiene presentación propia y mantiene autocomplete, etiquetas y errores.
Una sesión guardada muestra estado de carga mientras el servidor la valida,
evitando presentar fugazmente otro formulario de acceso. Los permisos siguen
siendo del servidor; el rediseño no cambia roles, colas ni máquinas de estados.

Se incluyen foco visible, enlace para saltar al contenido, iconos decorativos,
selección de pestaña y respeto por movimiento reducido. No se afirma una auditoría
formal de conformidad de accesibilidad. La prueba móvil mide ausencia de
desbordamiento de página en portal/FAQ a 390 px, además de la navegación real.

## Capturas reales y reproducción

El script `frontend/scripts/capture-demo.mjs` usa Playwright contra la aplicación
ya levantada y preparada con `scripts/prepare_demo.py`. No dibuja datos ni modifica
estados para componer imágenes. Inicia sesión con cada rol y captura las vistas
después de comprobar que los datos correspondientes están visibles.

Se utilizan cuentas sintéticas del lote, incluidas administrador, consulta,
solicitante, agente y aprobador. Las contraseñas se reciben por variables y no
se incluyen en PNG, índice, manifiestos o reportes. No se guarda el estado de
sesión del navegador. Los reportes demo se mantienen separados de su stderr
con claves, que se conserva solo temporalmente con permisos privados.

En una instalación Linux local puedes preparar un archivo **privado e ignorado**
`.e2e.env` con las credenciales generadas para:

```text
E2E_BASE_URL=http://localhost:5173
E2E_API_URL=http://localhost:8000
E2E_ADMIN_USER=demo-admin
E2E_ADMIN_PASSWORD=<clave-local>
E2E_CONSULTA_USER=demo-consulta
E2E_CONSULTA_PASSWORD=<clave-local>
E2E_REQUESTER_USER=demo-solicitante
E2E_REQUESTER_PASSWORD=<clave-local>
E2E_AGENT_USER=demo-agente1
E2E_AGENT_PASSWORD=<clave-local>
E2E_APPROVER_USER=demo-aprobador
E2E_APPROVER_PASSWORD=<clave-local>
CAPTURE_DIR=/evidence/capturas
```

Los marcadores no son contraseñas válidas. Usa el mismo host configurado en
`FRONTEND_ORIGINS`/`VITE_API_URL` (el Compose principal usa localhost). Desde la
raíz del proyecto, en Linux con Docker:

```bash
chmod 600 .e2e.env
mkdir -p docs/evidencias/frontend-local
docker run --rm --network host --env-file .e2e.env \
  -v "$PWD/frontend:/work:z" \
  -v "$PWD/docs/evidencias/frontend-local:/evidence:z" \
  -w /work mcr.microsoft.com/playwright:v1.63.0-noble \
  sh -c 'npm ci && node scripts/capture-demo.mjs'
```

No montes el socket Docker ni `.env` de la aplicación dentro del navegador.
Las etiquetas `z` permiten compartir las carpetas en Fedora con SELinux. El
modo host del comando corresponde a Linux. En el servidor temporal se usaron
otros puertos loopback, documentados junto con los resultados.

El generador de capturas espera el lote predeterminado de 37 tickets y 5,000
dispositivos. Las E2E pueden agregar solicitudes sintéticas; no se borran para
simular un conjunto exacto. `capturas/INDICE.json` registra archivo, descripción,
rol, fecha UTC y dimensiones. Las vistas móviles usan 390 × 844 y las de
escritorio 1440 × 1000. Algunas imágenes de fichas/tablero capturan todo el
elemento o la página para incluir los datos completos.

## Evidencias

Resultados y galería: [FRONTEND-2026-10-28](evidencias/FRONTEND-2026-10-28.md).
La preparación específica en Fedora se mantiene en [FEDORA.md](FEDORA.md).
Las capturas remotas no se presentan como prueba del equipo Fedora del alumno.

La auditoría posterior agrega historial de tickets en la ficha de CI y las
notificaciones visibles del evento. Sus dos regresiones elevan la suite a 18 E2E;
las capturas adicionales y resultados están en [AUDITORIA](AUDITORIA.md).
