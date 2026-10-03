import { useEffect, useState } from 'react'
import AdminPanel from './AdminPanel.jsx'
import OrganizationPanel from './OrganizationPanel.jsx'
import ServiceBrowser from './ServiceBrowser.jsx'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
    ...options,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? 'No fue posible completar la solicitud')
  }
  return response.status === 204 ? null : response.json()
}

function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem('access_token'))
  const [user, setUser] = useState(null)
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('resumen')

  useEffect(() => {
    if (!token) return
    const loadSession = async () => {
      try {
        const headers = { Authorization: `Bearer ${token}` }
        const [currentUser] = await Promise.all([
          request('/api/v1/auth/me', { headers }),
        ])
        setUser(currentUser)
      } catch {
        sessionStorage.removeItem('access_token')
        setToken(null)
      }
    }
    loadSession()
  }, [token])

  async function handleLogin(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = await request('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ identifier, password }),
      })
      sessionStorage.setItem('access_token', result.access_token)
      setPassword('')
      setToken(result.access_token)
      setActiveTab('resumen')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleLogout() {
    try {
      await request('/api/v1/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
    } finally {
      sessionStorage.removeItem('access_token')
      setToken(null)
      setUser(null)
    }
  }

  if (!token || !user) {
    return (
      <main className="auth-layout">
        <section className="auth-card">
          <p className="eyebrow">Catálogo de Servicios</p>
          <h1>Iniciar sesión</h1>
          <p className="intro">Accede con un usuario local o una cuenta de correo registrada en la aplicación.</p>
          <form onSubmit={handleLogin}>
            <label htmlFor="identifier">Usuario o correo</label>
            <input id="identifier" value={identifier} onChange={(event) => setIdentifier(event.target.value)} required autoComplete="username" />
            <label htmlFor="password">Contraseña</label>
            <input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" />
            {error && <p className="error" role="alert">{error}</p>}
            <button type="submit" disabled={loading}>{loading ? 'Validando…' : 'Entrar'}</button>
          </form>
        </section>
      </main>
    )
  }

  return (
    <main className="container">
      <header className="page-header">
        <div>
          <p className="eyebrow">Catálogo de Servicios</p>
          <h1>Servicios externos</h1>
          <p className="intro">Sesión activa para {user.username} · rol: {user.role}.</p>
        </div>
        <button className="secondary-button" type="button" onClick={handleLogout}>Cerrar sesión</button>
      </header>
      <nav className="dashboard-nav" role="tablist" aria-label="Secciones del dashboard">
        <button role="tab" type="button" className={activeTab === 'resumen' ? 'active-tab' : ''} aria-selected={activeTab === 'resumen'} aria-controls="dashboard-panel" onClick={() => setActiveTab('resumen')}>Resumen</button>
        <button role="tab" type="button" className={activeTab === 'servicios' ? 'active-tab' : ''} aria-selected={activeTab === 'servicios'} aria-controls="dashboard-panel" onClick={() => setActiveTab('servicios')}>Servicios</button>
        <button role="tab" type="button" className={activeTab === 'organizacion' ? 'active-tab' : ''} aria-selected={activeTab === 'organizacion'} aria-controls="dashboard-panel" onClick={() => setActiveTab('organizacion')}>Organización</button>
        {user.role === 'administrador' && <button role="tab" type="button" className={activeTab === 'usuarios' ? 'active-tab' : ''} aria-selected={activeTab === 'usuarios'} aria-controls="dashboard-panel" onClick={() => setActiveTab('usuarios')}>Usuarios</button>}
      </nav>
      <section id="dashboard-panel" className="dashboard-content" role="tabpanel" aria-live="polite">
        {activeTab === 'resumen' && <DashboardSummary user={user} onNavigate={setActiveTab} />}
        {activeTab === 'servicios' && <ServiceBrowser token={token} role={user.role} />}
        {activeTab === 'organizacion' && <OrganizationPanel token={token} role={user.role} />}
        {activeTab === 'usuarios' && user.role === 'administrador' && <AdminPanel token={token} />}
      </section>
    </main>
  )
}

function DashboardSummary({ user, onNavigate }) {
  return (
    <section className="dashboard-summary" aria-label="Resumen del dashboard">
      <div className="card summary-welcome">
        <p className="eyebrow">Panel principal</p>
        <h2>Bienvenida, {user.name ?? user.username}</h2>
        <p className="intro">Desde aquí puedes consultar el catálogo de servicios y explorar la estructura organizacional de la institución.</p>
      </div>
      <div className="summary-grid">
        <button type="button" className="summary-card" onClick={() => onNavigate('servicios')}><span className="summary-icon">01</span><strong>Catálogo de servicios</strong><small>Buscar, filtrar y revisar fichas completas.</small></button>
        <button type="button" className="summary-card" onClick={() => onNavigate('organizacion')}><span className="summary-icon">02</span><strong>Organización</strong><small>Explorar empresas, áreas, departamentos, secciones y puestos.</small></button>
        {user.role === 'administrador' && <button type="button" className="summary-card" onClick={() => onNavigate('usuarios')}><span className="summary-icon">03</span><strong>Usuarios</strong><small>Administrar roles y estados de las cuentas locales.</small></button>}
      </div>
    </section>
  )
}

export default App
