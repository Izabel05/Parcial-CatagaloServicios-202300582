# Frontend

Cliente web inicial con React, Vite y JavaScript.

## Comandos

```bash
npm install
npm run dev
```

La URL de la API se configura con `VITE_API_URL`.

La interfaz muestra la estructura `Empresa → Área → Departamento → Sección →
Puesto` para ambos roles. El administrador puede crear, editar y realizar bajas
lógicas; el rol `consulta` solo navega y consulta. Los padres que aparecen en
los formularios se limitan a registros activos y el servidor vuelve a validar
la relación antes de guardar.

El dashboard se organiza en pestañas de Resumen, Servicios, Organización y
Usuarios. Las fichas muestran valores legibles y etiquetas en español; las
estructuras internas no se presentan como JSON al usuario.
