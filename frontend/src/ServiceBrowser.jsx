import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const DETAIL_LABELS = {
  id: 'Identificador', code: 'Código', original_code: 'Código original', level_1_code: 'Código nivel 1',
  level_1_name: 'Nombre nivel 1', name: 'Nombre', active: 'Estado', service_class: 'Clase',
  service_class_name: 'Nombre de clase', criticality: 'Criticidad', criticality_name: 'Nombre de criticidad',
  service_type: 'Tipo de servicio', service_type_name: 'Nombre del tipo', description: 'Descripción',
  metric: 'Métrica', minimum: 'Mínimo', maximum: 'Máximo', review_status: 'Estado de revisión',
  service_class_id: 'Identificador de clase', criticality_id: 'Identificador de criticidad',
  service_type_id: 'Identificador de tipo', source_sheet: 'Hoja de origen', source_row: 'Fila de origen',
  source_range: 'Rango de origen', transformations: 'Transformaciones', responsible_section_id: 'Identificador de sección responsable',
  responsible_section_code: 'Código de sección responsable', responsible_user_id: 'Identificador de usuario responsable',
  responsible_user_name: 'Usuario responsable',
}

function detailLabel(key) {
  return DETAIL_LABELS[key] ?? key.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function DetailValue({ value }) {
  if (value === null || value === undefined || value === '') return 'Sin dato'
  if (typeof value === 'boolean') return value ? 'Activo' : 'Inactivo'
  if (Array.isArray(value)) return <ul className="detail-list">{value.map((item, index) => <li key={index}><DetailValue value={item} /></li>)}</ul>
  if (typeof value === 'object') return <dl className="detail-map">{Object.entries(value).map(([key, nestedValue]) => <div key={key}><dt>{detailLabel(key)}</dt><dd><DetailValue value={nestedValue} /></dd></div>)}</dl>
  return String(value)
}

async function apiRequest(path, token, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...(options.headers ?? {}) },
    ...options,
  })
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = body?.detail
    const message = Array.isArray(detail)
      ? detail.map((error) => error.msg).filter(Boolean).join('; ')
      : typeof detail === 'string' ? detail : ''
    throw new Error(message || 'No fue posible completar la operación')
  }
  return body
}

function ServiceBrowser({ token, role }) {
  const [draft, setDraft] = useState({ search: '', level_1_code: '', active: '', service_class_id: '', criticality_id: '', service_type_id: '' })
  const [filters, setFilters] = useState(draft)
  const [catalogs, setCatalogs] = useState({ service_classes: [], criticalities: [], service_types: [] })
  const [levels, setLevels] = useState([])
  const [sections, setSections] = useState([])
  const [users, setUsers] = useState([])
  const [pageData, setPageData] = useState({ items: [], total: 0, page: 1, page_size: 10, pages: 1 })
  const [selected, setSelected] = useState(null)
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ code: '', level_1_code: '', name: '', service_class_id: '', criticality_id: '', service_type_id: '', responsible_section_id: '', responsible_user_id: '', minimum: '', maximum: '' })

  useEffect(() => {
    Promise.all([
      apiRequest('/api/v1/services/catalog-options', token),
      apiRequest('/api/v1/services/level-1', token),
      apiRequest('/api/v1/secciones', token),
      apiRequest('/api/v1/usuarios', token),
    ]).then(([nextCatalogs, nextLevels, nextSections, nextUsers]) => {
      setCatalogs(nextCatalogs)
      setLevels(nextLevels)
      setSections(nextSections.filter((section) => section.activo))
      setUsers(nextUsers.filter((user) => user.is_active))
      setForm((current) => ({ ...current, level_1_code: nextLevels[0]?.code ?? '', service_class_id: nextCatalogs.service_classes[0]?.id ?? '', criticality_id: nextCatalogs.criticalities[0]?.id ?? '', service_type_id: nextCatalogs.service_types[0]?.id ?? '', responsible_section_id: nextSections.find((section) => section.activo)?.id ?? '' }))
    }).catch((requestError) => setError(requestError.message))
  }, [token])

  useEffect(() => {
    let current = true
    const query = new URLSearchParams({ page: String(pageData.page), page_size: '10' })
    Object.entries(filters).forEach(([key, value]) => { if (value !== '') query.set(key, value) })
    setLoading(true)
    apiRequest(`/api/v1/services?${query.toString()}`, token)
      .then((result) => { if (current) setPageData(result) })
      .catch((requestError) => { if (current) setError(requestError.message) })
      .finally(() => { if (current) setLoading(false) })
    return () => { current = false }
  }, [token, filters, pageData.page])

  function updateDraft(event) {
    setDraft((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  function submitFilters(event) {
    event.preventDefault()
    setPageData((current) => ({ ...current, page: 1 }))
    setFilters(draft)
  }

  function setFormValue(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function createService(event) {
    event.preventDefault()
    setError('')
    try {
      await apiRequest('/api/v1/services', token, {
        method: 'POST',
        body: JSON.stringify({
          ...form,
          active: true,
          service_class_id: Number(form.service_class_id),
          criticality_id: Number(form.criticality_id),
          service_type_id: Number(form.service_type_id),
          responsible_section_id: Number(form.responsible_section_id),
          responsible_user_id: form.responsible_user_id ? Number(form.responsible_user_id) : null,
          minimum: form.minimum === '' ? null : Number(form.minimum),
          maximum: form.maximum === '' ? null : Number(form.maximum),
        }),
      })
      setForm((current) => ({ ...current, code: '', name: '', minimum: '', maximum: '', responsible_user_id: '' }))
      setPageData((current) => ({ ...current, page: 1 }))
      setFilters((current) => ({ ...current }))
    } catch (requestError) {
      setError(requestError.message)
    }
  }

  function startEditing(service) {
    setEditing({
      code: service.code,
      name: service.name,
      service_class_id: service.service_class_id ?? '',
      criticality_id: service.criticality_id ?? '',
      service_type_id: service.service_type_id ?? '',
      responsible_section_id: service.responsible_section_id ?? '',
      responsible_user_id: service.responsible_user_id ?? '',
      minimum: service.minimum ?? '',
      maximum: service.maximum ?? '',
      active: service.active === true,
    })
  }

  function updateEditing(event) {
    setEditing((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function saveEditing(event) {
    event.preventDefault()
    setError('')
    try {
      const updated = await apiRequest(`/api/v1/services/${editing.code}`, token, {
        method: 'PATCH',
        body: JSON.stringify({
          name: editing.name,
          service_class_id: Number(editing.service_class_id),
          criticality_id: Number(editing.criticality_id),
          service_type_id: Number(editing.service_type_id),
          responsible_section_id: Number(editing.responsible_section_id),
          responsible_user_id: editing.responsible_user_id ? Number(editing.responsible_user_id) : null,
          minimum: editing.minimum === '' ? null : Number(editing.minimum),
          maximum: editing.maximum === '' ? null : Number(editing.maximum),
          active: editing.active,
        }),
      })
      setSelected(updated)
      setEditing(null)
      setPageData((current) => ({ ...current }))
    } catch (requestError) {
      setError(requestError.message)
    }
  }

  async function deactivateService(service) {
    if (!window.confirm(`¿Desactivar el servicio ${service.code}?`)) return
    setError('')
    try {
      const updated = await apiRequest(`/api/v1/services/${service.code}`, token, { method: 'DELETE' })
      setSelected(updated)
      setPageData((current) => ({ ...current }))
    } catch (requestError) {
      setError(requestError.message)
    }
  }

  return (
    <>
      <section className="card service-browser" aria-label="Búsqueda de servicios">
        <div className="section-heading"><div><p className="eyebrow">Catálogo</p><h2>Buscar servicios</h2></div><span>{pageData.total} resultados</span></div>
        <form className="filter-grid" onSubmit={submitFilters}>
          <input name="search" value={draft.search} onChange={updateDraft} placeholder="Código o nombre" aria-label="Buscar por código o nombre" />
          <select name="level_1_code" value={draft.level_1_code} onChange={updateDraft} aria-label="Filtrar por nivel 1"><option value="">Todos los niveles</option>{levels.map((level) => <option key={level.code} value={level.code}>{level.code} · {level.name}</option>)}</select>
          <select name="service_class_id" value={draft.service_class_id} onChange={updateDraft} aria-label="Filtrar por clase"><option value="">Todas las clases</option>{catalogs.service_classes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
          <select name="criticality_id" value={draft.criticality_id} onChange={updateDraft} aria-label="Filtrar por criticidad"><option value="">Todas las criticidades</option>{catalogs.criticalities.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
          <select name="service_type_id" value={draft.service_type_id} onChange={updateDraft} aria-label="Filtrar por tipo"><option value="">Todos los tipos</option>{catalogs.service_types.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
          <select name="active" value={draft.active} onChange={updateDraft} aria-label="Filtrar por estado"><option value="">Todos los estados</option><option value="true">Activos</option><option value="false">Inactivos</option></select>
          <button type="submit">Aplicar filtros</button>
        </form>
        {error && <p className="error" role="alert">{error}</p>}
        {loading ? <p>Cargando servicios…</p> : <ul className="service-list">{pageData.items.map((service) => <li key={service.code} onClick={() => setSelected(service)}><strong>{service.code}</strong><span>{service.name}<small>{service.level_1_code} · {service.service_class_name ?? service.service_class ?? 'Clase pendiente'}</small></span><small>{service.active === true ? 'Activo' : service.active === false ? 'Inactivo' : 'Revisión'}</small></li>)}</ul>}
        <div className="pagination"><button type="button" disabled={pageData.page <= 1} onClick={() => setPageData((current) => ({ ...current, page: current.page - 1 }))}>Anterior</button><span>Página {pageData.page} de {pageData.pages}</span><button type="button" disabled={pageData.page >= pageData.pages} onClick={() => setPageData((current) => ({ ...current, page: current.page + 1 }))}>Siguiente</button></div>
      </section>

      {selected && <section className="card service-detail" aria-label="Ficha de servicio"><div className="section-heading"><div><p className="eyebrow">Ficha completa</p><h2>{selected.code}</h2></div><div className="button-row"><button className="small-button" type="button" onClick={() => setSelected(null)}>Cerrar</button>{role === 'administrador' && <><button className="small-button" type="button" onClick={() => startEditing(selected)}>Editar</button>{selected.active !== false && <button className="small-button danger-button" type="button" onClick={() => deactivateService(selected)}>Baja lógica</button>}</>}</div></div><dl>{Object.entries(selected).map(([key, value]) => <div key={key}><dt>{detailLabel(key)}</dt><dd><DetailValue value={value} /></dd></div>)}</dl></section>}

      {editing && <section className="card" aria-label="Editar servicio"><div className="section-heading"><div><p className="eyebrow">Administración</p><h2>Editar {editing.code}</h2></div><button className="small-button" type="button" onClick={() => setEditing(null)}>Cancelar</button></div><form className="filter-grid" onSubmit={saveEditing}><input name="name" value={editing.name} onChange={updateEditing} placeholder="Nombre" required /><select name="service_class_id" value={editing.service_class_id} onChange={updateEditing} required>{catalogs.service_classes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select name="criticality_id" value={editing.criticality_id} onChange={updateEditing} required>{catalogs.criticalities.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select name="service_type_id" value={editing.service_type_id} onChange={updateEditing} required>{catalogs.service_types.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select name="responsible_section_id" value={editing.responsible_section_id} onChange={updateEditing} required>{sections.map((section) => <option key={section.id} value={section.id}>{section.codigo} · {section.nombre}</option>)}</select><select name="responsible_user_id" value={editing.responsible_user_id} onChange={updateEditing}><option value="">Sin usuario responsable</option>{users.map((user) => <option key={user.id} value={user.id}>{user.name} · {user.username}</option>)}</select><input name="minimum" type="number" value={editing.minimum} onChange={updateEditing} placeholder="Mínimo opcional" /><input name="maximum" type="number" value={editing.maximum} onChange={updateEditing} placeholder="Máximo opcional" /><label className="checkbox-label"><input name="active" type="checkbox" checked={editing.active} onChange={(event) => setEditing((current) => ({ ...current, active: event.target.checked }))} /> Servicio activo</label><button type="submit">Guardar cambios</button></form></section>}

      {role === 'administrador' && <section className="card" aria-label="Alta de servicio"><p className="eyebrow">Administración</p><h2>Nuevo servicio</h2><form className="filter-grid" onSubmit={createService}><input name="code" value={form.code} onChange={setFormValue} placeholder="Código" required /><input name="name" value={form.name} onChange={setFormValue} placeholder="Nombre" required /><select name="level_1_code" value={form.level_1_code} onChange={setFormValue} required>{levels.map((level) => <option key={level.code} value={level.code}>{level.code} · {level.name}</option>)}</select><select name="service_class_id" value={form.service_class_id} onChange={setFormValue} required>{catalogs.service_classes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select name="criticality_id" value={form.criticality_id} onChange={setFormValue} required>{catalogs.criticalities.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select name="service_type_id" value={form.service_type_id} onChange={setFormValue} required>{catalogs.service_types.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select name="responsible_section_id" value={form.responsible_section_id} onChange={setFormValue} required><option value="">Sección responsable</option>{sections.map((section) => <option key={section.id} value={section.id}>{section.codigo} · {section.nombre}</option>)}</select><select name="responsible_user_id" value={form.responsible_user_id} onChange={setFormValue}><option value="">Sin usuario responsable</option>{users.map((user) => <option key={user.id} value={user.id}>{user.name} · {user.username}</option>)}</select><input name="minimum" type="number" value={form.minimum} onChange={setFormValue} placeholder="Mínimo opcional" /><input name="maximum" type="number" value={form.maximum} onChange={setFormValue} placeholder="Máximo opcional" /><button type="submit">Crear servicio</button></form></section>}
    </>
  )
}

export default ServiceBrowser
