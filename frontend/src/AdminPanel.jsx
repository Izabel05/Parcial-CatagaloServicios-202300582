import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function AdminPanel({ token }) {
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')

  async function loadUsers() {
    const response = await fetch(`${API_URL}/api/v1/admin/users`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) throw new Error('No fue posible cargar los usuarios')
    setUsers(await response.json())
  }

  useEffect(() => {
    loadUsers().catch((requestError) => setError(requestError.message))
  }, [token])

  async function updateUser(userId, field, value) {
    setError('')
    const response = await fetch(`${API_URL}/api/v1/admin/users/${userId}/${field}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(field === 'status' ? { is_active: value } : { role: value }),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      setError(body.detail ?? 'No fue posible actualizar el usuario')
      return
    }
    await loadUsers()
  }

  return (
    <section className="admin-panel" aria-label="Administración de usuarios">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Administración</p>
          <h2>Usuarios</h2>
        </div>
        <span className="role-badge">administrador</span>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      <div className="user-table">
        {users.map((user) => (
          <div className="user-row" key={user.id}>
            <div><strong>{user.username}</strong><span>{user.email}</span></div>
            <select value={user.role} onChange={(event) => updateUser(user.id, 'role', event.target.value)}>
              <option value="administrador">administrador</option>
              <option value="consulta">consulta</option>
              <option value="solicitante">solicitante</option>
              <option value="agente">agente</option>
              <option value="aprobador">aprobador</option>
            </select>
            <button type="button" className="small-button" onClick={() => updateUser(user.id, 'status', !user.is_active)}>
              {user.is_active ? 'Desactivar' : 'Activar'}
            </button>
          </div>
        ))}
      </div>
    </section>
  )
}

export default AdminPanel
