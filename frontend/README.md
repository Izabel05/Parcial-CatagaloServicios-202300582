# Frontend

Cliente web inicial con React, Vite y JavaScript.

## Comandos

```bash
npm install
npm run dev
```

Si Fedora muestra `EACCES` al ejecutar `npm ci`, normalmente `node_modules`
fue creado anteriormente con otro usuario. Corrige la propiedad del directorio
local y vuelve a instalar las dependencias sin usar `sudo npm`:

```bash
if [ -d node_modules ]; then
  sudo chown -R "$(id -u):$(id -g)" node_modules
fi
npm ci
npx playwright install chromium
```

La instalación del navegador se realiza una sola vez por usuario. No se debe
subir `node_modules` al repositorio.

La URL de la API se configura con `VITE_API_URL`.

La interfaz muestra la estructura `Empresa → Área → Departamento → Sección →
Puesto` para ambos roles. El administrador puede crear, editar y realizar bajas
lógicas; el rol `consulta` solo navega y consulta. Los padres que aparecen en
los formularios se limitan a registros activos y el servidor vuelve a validar
la relación antes de guardar.

El dashboard se organiza en pestañas de Resumen, Servicios, Organización y
Usuarios. Las fichas muestran valores legibles y etiquetas en español; las
estructuras internas no se presentan como JSON al usuario.
