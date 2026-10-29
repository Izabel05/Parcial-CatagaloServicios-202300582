import { useEffect, useState } from 'react'
import AdminPanel from './AdminPanel.jsx'
import OrganizationPanel from './OrganizationPanel.jsx'
import ServiceBrowser from './ServiceBrowser.jsx'
import CmdbPanel from './CmdbPanel.jsx'
import DeskWorkspace from './DeskWorkspace.jsx'
import FaqPanel from './FaqPanel.jsx'
import DeskDashboard from './DeskDashboard.jsx'
import WorkspaceIcon from './WorkspaceIcon.jsx'

const sections = [
  ['resumen', 'Resumen', 'Servicios externos', 'Tu punto de partida para gestionar servicios, solicitudes e infraestructura.'],
  ['desk', 'Service Desk', 'Atención de solicitudes', 'Organiza el trabajo, consulta tus tickets y acompaña cada proceso.'],
  ['servicios', 'Servicios', 'Catálogo de servicios', 'Encuentra los servicios disponibles y consulta sus responsables.'],
  ['cmdb', 'CMDB', 'Inventario de configuración', 'Explora dispositivos, ubicaciones y dependencias entre servicios.'],
  ['tablero', 'Tablero', 'Indicadores de atención', 'Revisa cantidades, tiempos y objetivos de las colas autorizadas.'],
  ['faq', 'FAQ', 'Centro de ayuda', 'Encuentra respuestas antes de abrir una nueva solicitud.'],
  ['organizacion', 'Organización', 'Estructura organizacional', 'Consulta las unidades y las personas de la institución.'],
  ['usuarios', 'Usuarios', 'Gestión de cuentas', 'Administra las cuentas, sus roles y su estado.'],
]

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

  if (token && !user) return <main className="session-loading" role="status"><span className="brand-mark">S</span><p>Preparando tu espacio de trabajo…</p></main>

  if (!token) {
    return (
      <main className="auth-layout">
        <div className="auth-story">
          <div className="brand"><span className="brand-mark">S</span><span>Service Desk<small>Gestión de servicios TI</small></span></div>
          <span className="auth-kicker">UN SOLO ESPACIO DE TRABAJO</span>
          <h2>Conecta los servicios.<br/><em>Resuelve lo importante.</em></h2>
          <p>Solicitudes, infraestructura y conocimiento al alcance de tu equipo.</p>
          <div className="auth-features"><span><WorkspaceIcon name="desk"/> Atención y seguimiento</span><span><WorkspaceIcon name="cmdb"/> Dispositivos y dependencias</span><span><WorkspaceIcon name="faq"/> Conocimiento compartido</span></div>
          <small>Catálogo de servicios · CMDB · Service Desk</small>
        </div>
        <section className="auth-card">
          <p className="eyebrow">Bienvenido a tu espacio</p>
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
          <p className="auth-footnote">¿Necesitas acceso? Solicita tu cuenta al administrador de tu organización.</p>
        </section>
      </main>
    )
  }

  const current = sections.find(([key]) => key === activeTab)
  return (
    <div className="app-shell">
      <a className="skip-link" href="#dashboard-panel">Ir al contenido</a>
      <aside className="workspace-sidebar">
        <div className="brand"><span className="brand-mark">S</span><span>Service Desk<small>Gestión de servicios TI</small></span></div>
        <p className="nav-caption">ESPACIO DE TRABAJO</p>
        <nav className="dashboard-nav" role="tablist" aria-label="Secciones del dashboard">
          {sections.filter(([key]) => key !== 'usuarios' || user.role === 'administrador').map(([key, title]) => <button key={key} role="tab" type="button" className={activeTab === key ? 'active-tab' : ''} aria-selected={activeTab === key} aria-controls="dashboard-panel" onClick={() => setActiveTab(key)}><WorkspaceIcon name={key}/><span>{title}</span></button>)}
        </nav>
        <div className="sidebar-profile"><span className="user-avatar">{user.username.slice(0,2).toUpperCase()}</span><div><strong>{user.username}</strong><small>{user.role}</small></div></div>
        <button className="logout-button" type="button" onClick={handleLogout}><WorkspaceIcon name="logout"/>Cerrar sesión</button>
      </aside>
      <main className="container">
      <div className="workspace-topbar"><span>Espacio de trabajo <span aria-hidden="true">/</span> <strong>{current[1]}</strong></span><span className="role-badge">{user.role === 'consulta' ? 'Acceso de lectura' : user.role.replaceAll('_',' ')}</span></div>
      <header className="page-header">
        <div>
          <p className="eyebrow">{activeTab === 'resumen' ? 'Todo conectado' : current[1]}</p>
          <h1>{current[2]}</h1>
          <p className="intro">{current[3]}</p>
        </div>
        <span className="workspace-label"><span className="live-dot"/>Sesión activa</span>
      </header>
      <section id="dashboard-panel" className="dashboard-content" role="tabpanel" aria-live="polite">
        {activeTab === 'resumen' && <DashboardSummary user={user} onNavigate={setActiveTab} />}
        {activeTab === 'servicios' && <ServiceBrowser token={token} role={user.role} />}
        {activeTab === 'organizacion' && <OrganizationPanel token={token} role={user.role} />}
        {activeTab === 'cmdb' && <CmdbPanel token={token} role={user.role} />}
        {activeTab === 'desk' && <DeskWorkspace token={token} />}
        {activeTab === 'faq' && <FaqPanel token={token} />}
        {activeTab === 'tablero' && <DeskDashboard token={token} />}
        {activeTab === 'usuarios' && user.role === 'administrador' && <AdminPanel token={token} />}
      </section>
      <footer className="workspace-footer"><span>Service Desk · Catálogo e infraestructura</span><span>Tu organización, conectada.</span></footer>
    </main></div>
  )
}

function DashboardSummary({ user, onNavigate }) {
  return (
    <section className="dashboard-summary" aria-label="Resumen del dashboard">
      <div className="card summary-welcome">
        <div><p className="eyebrow">Tu centro de operaciones</p>
        <h2>Bienvenida, {user.name ?? user.username}</h2>
        <p className="intro">Cada solicitud tiene un siguiente paso. Accede a tus tickets o explora los servicios de tu organización.</p>
        <button className="hero-action" onClick={() => onNavigate('desk')}>Abrir Service Desk <WorkspaceIcon name="arrow"/></button></div>
        <div className="welcome-graphic" aria-hidden="true"><span><WorkspaceIcon name="desk"/></span><span><WorkspaceIcon name="cmdb"/></span><span><WorkspaceIcon name="servicios"/></span><i/><i/></div>
      </div>
      <div className="section-heading"><div><p className="eyebrow">Explorar</p><h2>Todo lo que necesitas</h2></div><span className="muted">Acceso según tus permisos</span></div>
      <div className="summary-grid">
        {[
          ['servicios','Catálogo de servicios','Consulta servicios, características y responsables.'],
          ['cmdb','Dispositivos y relaciones','Explora el inventario y sus dependencias técnicas.'],
          ['tablero','Tablero de atención','Consulta cantidades, tiempos y objetivos.'],
          ['faq','Preguntas frecuentes','Encuentra respuestas y resuelve tus dudas.'],
          ['organizacion','Organización','Conoce las unidades y las personas del equipo.'],
          ...(user.role === 'administrador' ? [['usuarios','Usuarios','Administra cuentas, roles y acceso.']] : []),
        ].map(([key,title,description]) => <button key={key} type="button" className="summary-card" onClick={() => onNavigate(key)}><span className="summary-icon"><WorkspaceIcon name={key}/></span><strong>{title}</strong><small>{description}</small><span className="card-link">Explorar <WorkspaceIcon name="arrow"/></span></button>)}
      </div>
    </section>
  )
}

export default App
