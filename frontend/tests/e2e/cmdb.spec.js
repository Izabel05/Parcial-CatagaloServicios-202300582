import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  test.skip(!process.env.E2E_ADMIN_PASSWORD || !process.env.E2E_CONSULTA_PASSWORD,
    'Requiere cuentas demo y un lote de 5000 dispositivos en la instalación aislada.')
  await page.goto('/')
})

async function openCmdb(page, reader = false) {
  await page.getByLabel('Usuario o correo').fill(reader ? process.env.E2E_CONSULTA_USER : process.env.E2E_ADMIN_USER)
  await page.getByLabel('Contraseña', { exact: true }).fill(reader ? process.env.E2E_CONSULTA_PASSWORD : process.env.E2E_ADMIN_PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await page.getByRole('tab', { name: 'CMDB', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'CMDB', exact: true })).toBeVisible()
}

test('CMDB busca entre 5000 dispositivos y navega ficha y dependencias', async ({ page }) => {
  await openCmdb(page)
  await expect(page.getByText('5000 dispositivos activos', { exact: true })).toBeVisible()
  await page.getByLabel('Buscar CI', { exact: true }).fill('000123')
  await page.getByRole('button', { name: 'Aplicar filtros CMDB' }).click()
  await expect(page.getByText('1 resultados · página 1', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: /SYN-hardware-v1-.*-000123/ }).click()
  const ficha = page.getByRole('region', { name: 'Ficha de CI' })
  await expect(ficha.getByText('Clasificación: Hardware', { exact: true })).toBeVisible()
  await ficha.getByRole('button', { name: 'Ver servicios potencialmente afectados' }).click()
  await expect(ficha.getByText(/Una dependencia no demuestra una interrupción efectiva/)).toBeVisible()
  await expect(ficha.getByRole('button', { name: 'Abrir CI de la ruta' })).toBeVisible()
})

test('CMDB consulta es de lectura y administrador mantiene ubicaciones', async ({ page }) => {
  await openCmdb(page, true)
  await expect(page.getByRole('region', { name: 'Mantenimiento de CI' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Guardar catálogo CMDB' })).toHaveCount(0)
  await page.getByRole('button', { name: 'Cerrar sesión' }).click()
  await openCmdb(page)
  const code = `E2E-LOC-${Date.now()}`
  await page.getByRole('combobox', { name: 'Catálogo', exact: true }).selectOption('ubicaciones')
  await page.getByLabel('Código catálogo').fill(code)
  await page.getByLabel('Nombre catálogo').fill('Ubicación de interfaz de prueba')
  await page.getByRole('button', { name: 'Guardar catálogo CMDB' }).click()
  await expect(page.getByRole('button', { name: `Editar ${code}`, exact: true })).toBeVisible()
  await page.getByRole('button', { name: `Desactivar ${code}`, exact: true }).click()
  await expect(page.getByText(`${code} · Ubicación de interfaz de prueba · Inactivo`, { exact: false })).toBeVisible()
})
