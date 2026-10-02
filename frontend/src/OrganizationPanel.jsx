import { useEffect, useMemo, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const LEVELS = [
  { key: 'empresas', label: 'Empresas', singular: 'Empresa', parentField: null },
  { key: 'areas', label: 'Áreas', singular: 'Área', parentField: 'empresa_id', parentKey: 'empresas' },
  { key: 'departamentos', label: 'Departamentos', singular: 'Departamento', parentField: 'area_id', parentKey: 'areas' },
  { key: 'secciones', label: 'Secciones', singular: 'Sección', parentField: 'departamento_id', parentKey: 'departamentos' },
  { key: 'puestos', label: 'Puestos', singular: 'Puesto', parentField: 'seccion_id', parentKey: 'secciones' },
]

async function apiRequest(path, token, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...(options.headers ?? {}) },
    ...options,
  })
  const body = await response.json().catch(() => null)
  if (!response.ok) throw new Error(body?.detail ?? 'No fue posible completar la operación')
  return body
}

const emptyForm = { kind: 'empresas', id: null, codigo: '', nombre: '', activo: true, parentId: '' }

function OrganizationPanel({ token, role }) {
  const [records, setRecords] = useState({ empresas: [], areas: [], departamentos: [], secciones: [], puestos: [] })
  const [users, setUsers] = useState([])
  const [selection, setSelection] = useState({ empresas: null, areas: null, departamentos: null, secciones: null, puestos: null })
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  async function loadOrganization() {
    setLoading(true)
    try {
      const responses = await Promise.all([
        ...LEVELS.map((level) => apiRequest(`/api/v1/${level.key}`, token)),
        apiRequest('/api/v1/usuarios', token),
      ])
      const nextRecords = Object.fromEntries(LEVELS.map((level, index) => [level.key, responses[index]]))
      setRecords(nextRecords)
      setUsers(responses[LEVELS.length])
      setError('')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOrganization()
  }, [token])

  const selectedRecord = useMemo(() => {
    for (let index = LEVELS.length - 1; index >= 0; index -= 1) {
      const level = LEVELS[index]
      const id = selection[level.key]
      if (id !== null) {
        const record = records[level.key].find((item) => item.id === id)
        if (record) return { level, record }
      }
    }
    return null
  }, [records, selection])

  function visibleRecords(level, index) {
    if (index === 0) return records[level.key]
    const parentId = selection[level.parentKey]
    if (parentId === null) return []
    return records[level.key].filter((item) => item[level.parentField] === parentId)
  }

  function selectRecord(level, id, index) {
    setSelection((current) => {
      const next = { ...current, [level.key]: id }
      LEVELS.slice(index + 1).forEach((child) => { next[child.key] = null })
      return next
    })
  }

  function startCreate(kind = 'empresas') {
    setError('')
    setEditing(false)
    setForm({ ...emptyForm, kind })
  }

  function startEdit() {
    if (!selectedRecord) return
    const { level, record } = selectedRecord
    setError('')
    setEditing(true)
    setForm({
      kind: level.key,
      id: record.id,
      codigo: record.codigo,
      nombre: record.nombre,
      activo: record.activo,
      parentId: level.parentField ? String(record[level.parentField]) : '',
    })
  }

  function changeForm(event) {
    const { name, value, type, checked } = event.target
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  function parentOptions(kind) {
    const level = LEVELS.find((item) => item.key === kind)
    if (!level?.parentKey) return []
    return records[level.parentKey].filter((item) => item.activo)
  }

  async function saveRecord(event) {
    event.preventDefault()
    setError('')
    const level = LEVELS.find((item) => item.key === form.kind)
    const payload = { codigo: form.codigo, nombre: form.nombre, activo: form.activo }
    if (level.parentField) payload[level.parentField] = Number(form.parentId)
    try {
      await apiRequest(
        editing ? `/api/v1/${form.kind}/${form.id}` : `/api/v1/${form.kind}`,
        token,
        { method: editing ? 'PATCH' : 'POST', body: JSON.stringify(payload) },
      )
      await loadOrganization()
      setEditing(false)
      setForm(emptyForm)
    } catch (requestError) {
      setError(requestError.message)
    }
  }

  async function deactivateSelected() {
    if (!selectedRecord) return
    const { level, record } = selectedRecord
    if (!window.confirm(`¿Desactivar ${level.singular} ${record.codigo}?`)) return
    setError('')
    try {
      await apiRequest(`/api/v1/${level.key}/${record.id}`, token, { method: 'DELETE' })
      await loadOrganization()
      setSelection((current) => ({ ...current, [level.key]: null }))
    } catch (requestError) {
      setError(requestError.message)
    }
  }

  function usersForPosition(positionId) {
    return users.filter((user) => user.puesto_id === positionId)
  }

  return (
    <section className="card organization-panel" aria-label="Estructura organizacional">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Directorio</p>
          <h2>Organización</h2>
        </div>
        <span className="role-badge">Consulta jerárquica</span>
      </div>
      <p className="intro organization-intro">Explora la relación Empresa → Área → Departamento → Sección → Puesto. Los usuarios se muestran dentro de su puesto.</p>
      {error && <p className="error" role="alert">{error}</p>}
      {loading ? <p>Cargando estructura…</p> : <div className="organization-tree">{LEVELS.map((level, index) => <div className="organization-column" key={level.key}><h3>{level.label}</h3>{visibleRecords(level, index).length === 0 ? <p className="muted">Selecciona el nivel anterior.</p> : visibleRecords(level, index).map((record) => <button type="button" className={`organization-item ${selection[level.key] === record.id ? 'selected' : ''}`} key={record.id} onClick={() => selectRecord(level, record.id, index)}><span><strong>{record.codigo}</strong><small>{record.nombre}</small></span><span className={`status-dot ${record.activo ? 'active' : 'inactive'}`}>{record.activo ? 'Activo' : 'Inactivo'}</span></button>)}</div>)}</div>}

      {selectedRecord && <div className="organization-detail"><div><p className="eyebrow">Registro seleccionado</p><h3>{selectedRecord.level.singular}: {selectedRecord.record.nombre}</h3><p><strong>Código:</strong> {selectedRecord.record.codigo} · <strong>Estado:</strong> {selectedRecord.record.activo ? 'Activo' : 'Inactivo'}</p>{selectedRecord.level.key === 'puestos' && <div><strong>Usuarios asignados</strong>{usersForPosition(selectedRecord.record.id).length === 0 ? <p className="muted">Sin usuarios asignados.</p> : <ul>{usersForPosition(selectedRecord.record.id).map((user) => <li key={user.id}>{user.name} · {user.username} · {user.role}</li>)}</ul>}</div>}</div>{role === 'administrador' && <div className="button-row"><button type="button" className="small-button" onClick={startEdit}>Editar</button>{selectedRecord.record.activo && <button type="button" className="small-button danger-button" onClick={deactivateSelected}>Baja lógica</button>}</div>}</div>}

      {role === 'administrador' && <section className="organization-admin"><div className="section-heading"><div><p className="eyebrow">Administración</p><h3>{editing ? `Editar ${form.kind}` : 'Nuevo registro'}</h3></div><button type="button" className="small-button" onClick={() => startCreate(form.kind)}>Limpiar</button></div><div className="organization-create-buttons">{LEVELS.map((level) => <button type="button" className={form.kind === level.key && !editing ? 'active-choice' : ''} key={level.key} onClick={() => startCreate(level.key)}>+ {level.singular}</button>)}</div><form className="filter-grid organization-form" onSubmit={saveRecord}><select name="kind" value={form.kind} onChange={(event) => startCreate(event.target.value)} disabled={editing}><option value="empresas">Empresa</option>{LEVELS.slice(1).map((level) => <option key={level.key} value={level.key}>{level.singular}</option>)}</select><input name="codigo" value={form.codigo} onChange={changeForm} placeholder="Código" required /><input name="nombre" value={form.nombre} onChange={changeForm} placeholder="Nombre" required />{LEVELS.find((level) => level.key === form.kind)?.parentField && <select name="parentId" value={form.parentId} onChange={changeForm} required><option value="">Selecciona padre activo</option>{parentOptions(form.kind).map((parent) => <option key={parent.id} value={parent.id}>{parent.codigo} · {parent.nombre}</option>)}</select>}<label className="checkbox-label"><input name="activo" type="checkbox" checked={form.activo} onChange={changeForm} /> Registro activo</label><button type="submit">{editing ? 'Guardar cambios' : 'Crear registro'}</button></form></section>}
    </section>
  )
}

export default OrganizationPanel
