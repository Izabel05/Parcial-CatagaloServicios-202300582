# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: catalogo.spec.js >> P10 permite búsqueda y filtros desde la interfaz
- Location: tests/e2e/catalogo.spec.js:46:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByLabel('Buscar por código o nombre')

```

# Page snapshot

```yaml
- main [ref=e3]:
  - generic [ref=e4]:
    - generic [ref=e5]:
      - paragraph [ref=e6]: Catálogo de Servicios
      - heading "Servicios externos" [level=1] [ref=e7]
      - paragraph [ref=e8]: "Sesión activa para demo-admin · rol: administrador."
    - button "Cerrar sesión" [ref=e9] [cursor=pointer]
  - tablist "Secciones del dashboard" [ref=e10]:
    - tab "Resumen" [selected] [ref=e11] [cursor=pointer]
    - tab "Servicios" [ref=e12] [cursor=pointer]
    - tab "Organización" [ref=e13] [cursor=pointer]
    - tab "Usuarios" [ref=e14] [cursor=pointer]
  - tabpanel [ref=e15]:
    - region "Resumen del dashboard" [ref=e16]:
      - generic [ref=e17]:
        - paragraph [ref=e18]: Panel principal
        - heading "Bienvenida, demo-admin" [level=2] [ref=e19]
        - paragraph [ref=e20]: Desde aquí puedes consultar el catálogo de servicios y explorar la estructura organizacional de la institución.
      - generic [ref=e21]:
        - button "01 Catálogo de servicios Buscar, filtrar y revisar fichas completas." [ref=e22] [cursor=pointer]:
          - generic [ref=e23]: "01"
          - strong [ref=e24]: Catálogo de servicios
          - generic [ref=e25]: Buscar, filtrar y revisar fichas completas.
        - button "02 Organización Explorar empresas, áreas, departamentos, secciones y puestos." [ref=e26] [cursor=pointer]:
          - generic [ref=e27]: "02"
          - strong [ref=e28]: Organización
          - generic [ref=e29]: Explorar empresas, áreas, departamentos, secciones y puestos.
        - button "03 Usuarios Administrar roles y estados de las cuentas locales." [ref=e30] [cursor=pointer]:
          - generic [ref=e31]: "03"
          - strong [ref=e32]: Usuarios
          - generic [ref=e33]: Administrar roles y estados de las cuentas locales.
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test'
  2  | 
  3  | const adminUser = process.env.E2E_ADMIN_USER
  4  | const adminPassword = process.env.E2E_ADMIN_PASSWORD
  5  | const consultaUser = process.env.E2E_CONSULTA_USER
  6  | const consultaPassword = process.env.E2E_CONSULTA_PASSWORD
  7  | 
  8  | test.beforeEach(async ({ page }) => {
  9  |   test.skip(!adminUser || !adminPassword || !consultaUser || !consultaPassword,
  10 |     'Definir E2E_ADMIN_USER/E2E_ADMIN_PASSWORD/E2E_CONSULTA_USER/E2E_CONSULTA_PASSWORD para ejecutar el E2E contra cuentas locales.')
  11 |   await page.goto('/')
  12 | })
  13 | 
  14 | async function login(page, identifier, password) {
  15 |   await page.getByLabel('Usuario o correo').fill(identifier)
  16 |   await page.getByLabel('Contraseña').fill(password)
  17 |   await page.getByRole('button', { name: 'Entrar' }).click()
  18 | }
  19 | 
  20 | test('P01 rechaza credenciales incorrectas y acepta las válidas', async ({ page }) => {
  21 |   await login(page, adminUser, 'credencial-incorrecta')
  22 |   await expect(page.getByRole('alert')).toContainText(/incorrect|inválid|credencial/i)
  23 |   await login(page, adminUser, adminPassword)
  24 |   await expect(page.getByRole('heading', { name: 'Servicios externos' })).toBeVisible()
  25 | })
  26 | 
  27 | test('P02 y P03 protegen la sesión y respetan el rol consulta', async ({ page }) => {
  28 |   await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
  29 |   await login(page, consultaUser, consultaPassword)
  30 |   await expect(page.getByRole('heading', { name: 'Servicios externos' })).toBeVisible()
  31 |   await expect(page.getByRole('heading', { name: 'Nuevo servicio' })).toHaveCount(0)
  32 |   await page.getByRole('button', { name: 'Cerrar sesión' }).click()
  33 |   await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
  34 | })
  35 | 
  36 | test('el dashboard navega por pestañas sin apilar todas las vistas', async ({ page }) => {
  37 |   await login(page, adminUser, adminPassword)
  38 |   await expect(page.getByRole('tab', { name: 'Resumen' })).toHaveAttribute('aria-selected', 'true')
  39 |   await page.getByRole('tab', { name: 'Servicios' }).click()
  40 |   await expect(page.getByRole('heading', { name: 'Buscar servicios' })).toBeVisible()
  41 |   await page.getByRole('tab', { name: 'Organización' }).click()
  42 |   await expect(page.getByRole('heading', { name: 'Organización' })).toBeVisible()
  43 |   await expect(page.getByRole('heading', { name: 'Buscar servicios' })).toHaveCount(0)
  44 | })
  45 | 
  46 | test('P10 permite búsqueda y filtros desde la interfaz', async ({ page }) => {
  47 |   await login(page, adminUser, adminPassword)
> 48 |   await page.getByLabel('Buscar por código o nombre').fill('SE.12')
     |                                                       ^ Error: locator.fill: Test timeout of 30000ms exceeded.
  49 |   await page.getByRole('button', { name: 'Aplicar filtros' }).click()
  50 |   await expect(page.getByText('SE.12.1').or(page.getByText('SE.12.2')).first()).toBeVisible()
  51 | })
  52 | 
  53 | test('P04 muestra la jerarquía organizacional y los puestos', async ({ page }) => {
  54 |   await login(page, adminUser, adminPassword)
  55 |   await expect(page.getByRole('heading', { name: 'Organización' })).toBeVisible()
  56 |   await expect(page.getByRole('heading', { name: 'Empresas' })).toBeVisible()
  57 |   await expect(page.getByRole('heading', { name: 'Áreas' })).toBeVisible()
  58 |   await expect(page.getByRole('heading', { name: 'Departamentos' })).toBeVisible()
  59 |   await expect(page.getByRole('heading', { name: 'Secciones' })).toBeVisible()
  60 |   await expect(page.getByRole('heading', { name: 'Puestos' })).toBeVisible()
  61 | })
  62 | 
  63 | test('P09 comunica al usuario el rango mínimo/máximo inválido', async ({ page }) => {
  64 |   await login(page, adminUser, adminPassword)
  65 |   await page.getByRole('heading', { name: 'Nuevo servicio' }).scrollIntoViewIfNeeded()
  66 |   await page.getByPlaceholder('Código').fill(`E2E-${Date.now()}`)
  67 |   await page.getByPlaceholder('Nombre').fill('Validación E2E')
  68 |   await page.getByPlaceholder('Mínimo opcional').fill('10')
  69 |   await page.getByPlaceholder('Máximo opcional').fill('1')
  70 |   await page.getByRole('button', { name: 'Crear servicio' }).click()
  71 |   await expect(page.getByRole('alert')).toContainText(/mínimo.*máximo/i)
  72 | })
  73 | 
```