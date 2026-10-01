import { useEffect, useState } from 'react'

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
  const [services, setServices] = useState([])
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!token) return
    const loadSession = async () => {
      try {
        const headers = { Authorization: `Bearer ${token}` }
        const [currentUser, catalog] = await Promise.all([
          request('/api/v1/auth/me', { headers }),
          request('/api/v1/services', { headers }),
        ])
        setUser(currentUser)
        setServices(catalog)
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
      setServices([])
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
          <p className="intro">Sesión activa para {user.username}.</p>
        </div>
        <button className="secondary-button" type="button" onClick={handleLogout}>Cerrar sesión</button>
      </header>
      <section className="card" aria-label="Servicios disponibles">
        <div>
          <strong>{services.length} servicios cargados</strong>
          <p>La información fue solicitada a una ruta protegida del backend.</p>
        </div>
      </section>
      <ul className="service-list">
        {services.map((service) => (
          <li key={service.code}>
            <strong>{service.code}</strong>
            <span>{service.name}</span>
            {service.review_status === 'REVIEW' && <small>Revisión pendiente</small>}
          </li>
        ))}
      </ul>
    </main>
  )
}

export default App
