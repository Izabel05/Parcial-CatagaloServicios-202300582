import { test, expect } from '@playwright/test'

const adminUser = process.env.E2E_ADMIN_USER
const adminPassword = process.env.E2E_ADMIN_PASSWORD
const consultaUser = process.env.E2E_CONSULTA_USER
const consultaPassword = process.env.E2E_CONSULTA_PASSWORD

test.beforeEach(async ({ page }) => {
  test.skip(!adminUser || !adminPassword || !consultaUser || !consultaPassword,
    'Definir E2E_ADMIN_USER/E2E_ADMIN_PASSWORD/E2E_CONSULTA_USER/E2E_CONSULTA_PASSWORD para ejecutar el E2E contra cuentas locales.')
  await page.goto('/')
})

async function login(page, identifier, password) {
  await page.getByLabel('Usuario o correo').fill(identifier)
  await page.getByLabel('Contraseña').fill(password)
  await page.getByRole('button', { name: 'Entrar' }).click()
}

async function openServices(page) {
  await page.getByRole('tab', { name: 'Servicios' }).click()
  await expect(page.getByRole('heading', { name: 'Buscar servicios' })).toBeVisible()
}

async function openOrganization(page) {
  await page.getByRole('tab', { name: 'Organización' }).click()
  await expect(page.getByRole('heading', { name: 'Organización' })).toBeVisible()
}

test('P01 rechaza credenciales incorrectas y acepta las válidas', async ({ page }) => {
  await login(page, adminUser, 'credencial-incorrecta')
  await expect(page.getByRole('alert')).toContainText(/incorrect|inválid|credencial/i)
  await login(page, adminUser, adminPassword)
  await expect(page.getByRole('heading', { name: 'Servicios externos' })).toBeVisible()
})

test('P02 y P03 protegen la sesión y respetan el rol consulta', async ({ page }) => {
  await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
  await login(page, consultaUser, consultaPassword)
  await expect(page.getByRole('heading', { name: 'Servicios externos' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Nuevo servicio' })).toHaveCount(0)
  await page.getByRole('button', { name: 'Cerrar sesión' }).click()
  await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
})

test('el dashboard navega por pestañas sin apilar todas las vistas', async ({ page }) => {
  await login(page, adminUser, adminPassword)
  await expect(page.getByRole('tab', { name: 'Resumen' })).toHaveAttribute('aria-selected', 'true')
  await openServices(page)
  await openOrganization(page)
  await expect(page.getByRole('heading', { name: 'Buscar servicios' })).toHaveCount(0)
})

test('P10 permite búsqueda y filtros desde la interfaz', async ({ page }) => {
  await login(page, adminUser, adminPassword)
  await openServices(page)
  await page.getByLabel('Buscar por código o nombre').fill('SE.12')
  await page.getByRole('button', { name: 'Aplicar filtros' }).click()
  await expect(page.getByText('SE.12.1').or(page.getByText('SE.12.2')).first()).toBeVisible()
})

test('P04 muestra la jerarquía organizacional y los puestos', async ({ page }) => {
  await login(page, adminUser, adminPassword)
  await openOrganization(page)
  await expect(page.getByRole('heading', { name: 'Empresas' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Áreas' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Departamentos' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Secciones' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Puestos' })).toBeVisible()
})

test('P09 comunica al usuario el rango mínimo/máximo inválido', async ({ page }) => {
  await login(page, adminUser, adminPassword)
  await openServices(page)
  await page.getByRole('heading', { name: 'Nuevo servicio' }).scrollIntoViewIfNeeded()
  await page.getByPlaceholder('Código').fill(`E2E-${Date.now()}`)
  await page.getByPlaceholder('Nombre').fill('Validación E2E')
  await page.getByPlaceholder('Mínimo opcional').fill('10')
  await page.getByPlaceholder('Máximo opcional').fill('1')
  await page.getByRole('button', { name: 'Crear servicio' }).click()
  await expect(page.getByRole('alert')).toContainText(/mínimo.*máximo/i)
})
