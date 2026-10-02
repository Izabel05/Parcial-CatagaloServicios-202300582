import { useEffect, useState } from 'react'
import AdminPanel from './AdminPanel.jsx'
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
      <ServiceBrowser token={token} role={user.role} />
      {user.role === 'administrador' && <AdminPanel token={token} />}
    </main>
  )
}

export default App
