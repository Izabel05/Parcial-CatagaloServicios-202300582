import { useEffect, useRef, useState } from 'react'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const emptyCI = { codigo: '', nombre: '', clasificacion_id: '', ubicacion_id: '', responsable_usuario_id: '',
  estado: 'Activo', activo: true, es_dispositivo: true, etiqueta: '', descripcion: '', numero_serie: '', version: '',
  fecha_adquisicion: '', fecha_vencimiento: '', ubicacion_original: '', responsable_original: '',
  nivel_seguridad: '', cumplimiento: '', estado_configuracion: '', numero_licencia: '',
  relaciones_originales: '', padres_hijos_originales: '', fecha_cambio_original: '',
  descripcion_cambio_original: '', documentacion_relacionada: '', enlaces_incidentes_problemas: '' }
const optionalLabels = { descripcion: 'Descripción', numero_serie: 'Número de serie', version: 'Versión',
  fecha_adquisicion: 'Fecha de adquisición', fecha_vencimiento: 'Fecha de vencimiento',
  ubicacion_original: 'Ubicación original', responsable_original: 'Responsable original',
  nivel_seguridad: 'Nivel de seguridad', cumplimiento: 'Cumplimiento',
  estado_configuracion: 'Estado de configuración', numero_licencia: 'Número de licencia',
  relaciones_originales: 'Referencia original de relaciones', padres_hijos_originales: 'Padres/hijos originales',
  fecha_cambio_original: 'Fecha de cambio original', descripcion_cambio_original: 'Descripción del cambio original',
  documentacion_relacionada: 'Documentación relacionada', enlaces_incidentes_problemas: 'Referencias originales a incidentes y problemas' }

export default function CmdbPanel({ token, role }) {
  const admin = role === 'administrador'
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [classes, setClasses] = useState([])
  const [locations, setLocations] = useState([])
  const [users, setUsers] = useState([])
  const [services, setServices] = useState([])
  const [report, setReport] = useState(null)
  const [filters, setFilters] = useState({ search: '', clasificacion_id: '', ubicacion_id: '', activo: '', es_dispositivo: '' })
  const [draft, setDraft] = useState(filters)
  const [page, setPage] = useState(1)
  const [result, setResult] = useState({ items: [], total: 0 })
  const [revision, setRevision] = useState(0)
  const [detail, setDetail] = useState(null)
  const detailRef = useRef(null)
  useEffect(() => { if (detail) detailRef.current?.scrollIntoView({ block: 'start' }) }, [detail?.id])
  const [impact, setImpact] = useState(null)
  const [ciForm, setCiForm] = useState(emptyCI)
  const [editing, setEditing] = useState(null)
  const [attributes, setAttributes] = useState('{}')
  const [catalog, setCatalog] = useState({ entity: 'clasificaciones', id: null, codigo: '', nombre: '', padre_id: '', activo: true })
  const [relation, setRelation] = useState({ destino_ci_id: '', tipo: 'depende_de', justificacion: '' })
  const [relationId, setRelationId] = useState(null)
  const [serviceId, setServiceId] = useState('')

  async function api(path, method = 'GET', body) {
    const response = await fetch(`${API}/api/v1${path}`, { method,
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }) })
    const data = await response.json()
    if (!response.ok) throw new Error(Array.isArray(data.detail) ? data.detail.map((e) => e.msg).join('; ') : data.detail || 'Operación rechazada')
    return data
  }
  async function act(work) {
    setError(''); setNotice('')
    try { await work(); setRevision((r) => r + 1); setNotice('Operación completada') }
    catch (e) { setError(e.message) }
  }
  useEffect(() => {
    let current = true
    Promise.all([api('/cmdb/catalogos/clasificaciones'), api('/cmdb/catalogos/ubicaciones'),
      api('/usuarios'), api('/services?page_size=100'), api('/cmdb/reporte')])
      .then(([c, l, u, s, r]) => { if (current) { setClasses(c); setLocations(l); setUsers(u); setServices(s.items); setReport(r) } })
      .catch((e) => { if (current) setError(e.message) })
    return () => { current = false }
  }, [token, revision])
  useEffect(() => {
    let current = true
    const query = new URLSearchParams({ page, page_size: 25 })
    Object.entries(filters).forEach(([key, value]) => { if (value !== '') query.set(key, value) })
    api(`/cmdb/ci?${query}`).then((r) => { if (current) setResult(r) }).catch((e) => { if (current) setError(e.message) })
    return () => { current = false }
  }, [token, page, filters, revision])

  async function show(id) {
    setError(''); setImpact(null); setRelationId(null)
    setRelation({ destino_ci_id: '', tipo: 'depende_de', justificacion: '' })
    try { setDetail(await api(`/cmdb/ci/${id}`)) } catch (e) { setError(e.message) }
  }
  function editCI(ci) {
    const values = Object.fromEntries(Object.keys(emptyCI).map((key) => [key, ci[key] ?? emptyCI[key]]))
    values.es_dispositivo = Boolean(ci.dispositivo)
    values.etiqueta = ci.dispositivo?.etiqueta ?? ''
    setCiForm(values); setAttributes(JSON.stringify(ci.atributos_tecnicos, null, 2)); setEditing(ci.id)
  }
  async function saveCI(e) {
    e.preventDefault()
    await act(async () => {
      const body = { ...ciForm, atributos_tecnicos: JSON.parse(attributes) }
      for (const key of ['clasificacion_id', 'ubicacion_id', 'responsable_usuario_id']) body[key] = body[key] ? Number(body[key]) : null
      for (const key of [...Object.keys(optionalLabels), 'etiqueta']) body[key] = body[key] || null
      const saved = await api(editing ? `/cmdb/ci/${editing}` : '/cmdb/ci', editing ? 'PUT' : 'POST', body)
      setEditing(null); setCiForm(emptyCI); setAttributes('{}'); await show(saved.id)
    })
  }
  const updateCI = (key, value) => setCiForm((f) => ({ ...f, [key]: value }))
  const selected = (key, value) => setDraft((f) => ({ ...f, [key]: value }))

  return <section aria-label="CMDB">
    <div className="card"><h2>CMDB</h2><p>{report?.dispositivos_activos ?? 0} dispositivos activos</p>
      <p>La clasificación organiza tus CI. Las relaciones técnicas permiten explorar sus dependencias.</p>
      {report && <details><summary>Distribución por clasificación</summary><ul>{report.por_clasificacion.map((r) => <li key={r.id}>{r.codigo} · nivel configurado {r.nivel}: {r.dispositivos_subarbol}</li>)}</ul></details>}
    </div>
    {error && <p role="alert" className="error">{error}</p>}{notice && <p role="status">{notice}</p>}
    <section className="card" aria-label="Búsqueda CMDB"><h3>Buscar CI y dispositivos</h3>
      <form className="filter-grid" onSubmit={(e) => { e.preventDefault(); setFilters(draft); setPage(1) }}>
        <label>Buscar CI<input value={draft.search} onChange={(e) => selected('search', e.target.value)} /></label>
        <label>Clasificación<select value={draft.clasificacion_id} onChange={(e) => selected('clasificacion_id', e.target.value)}><option value="">Todas</option>{classes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}</select></label>
        <label>Ubicación<select value={draft.ubicacion_id} onChange={(e) => selected('ubicacion_id', e.target.value)}><option value="">Todas</option>{locations.map((l) => <option key={l.id} value={l.id}>{l.nombre}</option>)}</select></label>
        <label>Estado del registro<select value={draft.activo} onChange={(e) => selected('activo', e.target.value)}><option value="">Todos</option><option value="true">Activo</option><option value="false">Inactivo</option></select></label>
        <label>Clase de registro<select value={draft.es_dispositivo} onChange={(e) => selected('es_dispositivo', e.target.value)}><option value="">Todos los CI</option><option value="true">Dispositivos físicos</option><option value="false">Otros CI</option></select></label>
        <button>Aplicar filtros CMDB</button>
      </form><p>{result.total} resultados · página {page}</p>
      <ul className="record-list">{result.items.map((ci) => <li key={ci.id}><button className="small-button" onClick={() => show(ci.id)}>{ci.codigo}</button><div className="record-body"><strong>{ci.nombre}</strong><small>{ci.clasificacion_nombre} · ID {ci.id}</small></div><span className={`status-pill ${ci.activo ? '' : 'inactive'}`}>{ci.activo ? 'Activo' : 'Inactivo'}</span></li>)}</ul>
      {result.items.length === 0 && <p>No hay dispositivos que coincidan con estos filtros.</p>}
      <button disabled={page === 1} onClick={() => setPage(page - 1)}>Anterior CMDB</button>{' '}
      <button disabled={page * 25 >= result.total} onClick={() => setPage(page + 1)}>Siguiente CMDB</button>
    </section>
    {detail && <section ref={detailRef} className="card ci-detail" aria-label="Ficha de CI"><h3>{detail.codigo} · {detail.nombre}</h3>
      <p>Clasificación: {detail.clasificacion_completa.map((c) => c.nombre).join(' → ')}</p>
      <dl>{Object.entries({ ...optionalLabels, estado: 'Estado técnico', ubicacion_id: 'ID ubicación', responsable_usuario_id: 'ID responsable' }).map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{String(detail[key] ?? 'Sin dato')}</dd></div>)}</dl>
      <p>Dispositivo: {detail.dispositivo?.etiqueta ?? 'No es dispositivo físico'}</p><pre>{JSON.stringify(detail.atributos_tecnicos, null, 2)}</pre>
      {admin && <><button onClick={() => editCI(detail)}>Editar CI</button>{' '}<button onClick={() => act(async () => { await api(`/cmdb/ci/${detail.id}`, 'DELETE'); await show(detail.id) })}>Desactivar CI</button></>}
      <h4>Servicios asociados</h4><ul>{detail.servicios.map((s) => <li key={s.id}>{s.code} · {s.name} {admin && <button onClick={() => act(async () => { await api(`/cmdb/ci/${detail.id}/servicios/${s.id}`, 'DELETE'); await show(detail.id) })}>Desvincular</button>}</li>)}</ul>
      {admin && <form onSubmit={(e) => { e.preventDefault(); act(async () => { await api(`/cmdb/ci/${detail.id}/servicios`, 'POST', { servicio_id: Number(serviceId) }); await show(detail.id) }) }}>
        <label>Servicio para vincular<select required value={serviceId} onChange={(e) => setServiceId(e.target.value)}><option value="">Seleccione</option>{services.filter((s) => s.active).map((s) => <option key={s.id} value={s.id}>{s.code} · {s.name}</option>)}</select></label><button>Vincular servicio</button></form>}
      <h4>Relaciones navegables</h4><ul>{detail.relaciones.map((r) => { const neighbor = r.origen_ci_id === detail.id ? r.destino_ci_id : r.origen_ci_id; return <li key={r.id}>{r.origen_codigo} → {r.tipo} → {r.destino_codigo} · {r.justificacion}{' '}<button onClick={() => show(neighbor)}>Abrir CI {neighbor}</button>{admin && <><button onClick={() => { setRelationId(r.id); setRelation({ origen_ci_id: r.origen_ci_id, destino_ci_id: r.destino_ci_id, tipo: r.tipo, justificacion: r.justificacion }) }}>Editar relación</button><button onClick={() => act(async () => { await api(`/cmdb/relaciones/${r.id}`, 'DELETE'); await show(detail.id) })}>Desactivar relación</button></>}</li> })}</ul>
      {admin && <form className="filter-grid" onSubmit={(e) => { e.preventDefault(); act(async () => { await api(relationId ? `/cmdb/relaciones/${relationId}` : '/cmdb/relaciones', relationId ? 'PUT' : 'POST', { ...relation, origen_ci_id: Number(relation.origen_ci_id || detail.id), destino_ci_id: Number(relation.destino_ci_id) }); setRelation({ destino_ci_id: '', tipo: 'depende_de', justificacion: '' }); await show(detail.id) }) }}>
        <label>ID CI destino<input type="number" min="1" required value={relation.destino_ci_id} onChange={(e) => setRelation({ ...relation, destino_ci_id: e.target.value })} /></label>
        <label>Tipo de relación<select value={relation.tipo} onChange={(e) => setRelation({ ...relation, tipo: e.target.value })}>{['depende_de', 'alojado_en', 'componente_de', 'conectado_a'].map((t) => <option key={t}>{t}</option>)}</select></label>
        <label>Motivo<input required value={relation.justificacion} onChange={(e) => setRelation({ ...relation, justificacion: e.target.value })} /></label><button>{relationId ? 'Guardar relación' : 'Crear relación'}</button>
      </form>}
      <button onClick={() => { setError(''); api(`/cmdb/ci/${detail.id}/dependencias`).then(setImpact).catch((e) => setError(e.message)) }}>Ver servicios potencialmente afectados</button>
      {impact && <div><p>{impact.advertencia} CI alcanzados: {impact.alcanzados}{impact.truncado && ' · recorrido truncado'}</p><ul>{impact.servicios_potencialmente_afectados.map((s) => <li key={s.id}>{s.code} · {s.name} · ruta {s.ruta_ci.join(' → ')} <button onClick={() => show(s.ci_id)}>Abrir CI de la ruta</button></li>)}</ul></div>}
      <details><summary>Historial del CI (últimas 100 acciones)</summary><ul>{detail.historial.map((h) => <li key={h.id}>{h.fecha} · {h.actor} · {h.accion}<pre>{JSON.stringify({ antes: h.antes, despues: h.despues }, null, 2)}</pre></li>)}</ul></details>
    </section>}
    {admin && <section className="card" aria-label="Mantenimiento de CI"><h3>{editing ? `Editar CI ${editing}` : 'Nuevo CI'}</h3>
      <form className="filter-grid" onSubmit={saveCI}>
        {['codigo', 'nombre', 'etiqueta', 'estado'].map((key) => <label key={key}>{key}<input required={key !== 'etiqueta' || ciForm.es_dispositivo} value={ciForm[key]} onChange={(e) => updateCI(key, e.target.value)} /></label>)}
        <label>Clasificación CI<select required value={ciForm.clasificacion_id} onChange={(e) => updateCI('clasificacion_id', e.target.value)}><option value="">Seleccione</option>{classes.filter((c) => c.activo).map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}</select></label>
        <label>Ubicación CI<select required={ciForm.es_dispositivo} value={ciForm.ubicacion_id} onChange={(e) => updateCI('ubicacion_id', e.target.value)}><option value="">Sin ubicación</option>{locations.filter((l) => l.activo).map((l) => <option key={l.id} value={l.id}>{l.nombre}</option>)}</select></label>
        <label>Responsable CI<select required={ciForm.es_dispositivo} value={ciForm.responsable_usuario_id} onChange={(e) => updateCI('responsable_usuario_id', e.target.value)}><option value="">Sin responsable</option>{users.filter((u) => u.is_active).map((u) => <option key={u.id} value={u.id}>{u.username}</option>)}</select></label>
        <label><input type="checkbox" checked={ciForm.es_dispositivo} onChange={(e) => updateCI('es_dispositivo', e.target.checked)} /> Dispositivo físico</label>
        <label><input type="checkbox" checked={ciForm.activo} onChange={(e) => updateCI('activo', e.target.checked)} /> Registro activo</label>
        {Object.entries(optionalLabels).map(([key, label]) => <label key={key}>{label}<input type={key.startsWith('fecha_') ? 'date' : 'text'} value={ciForm[key]} onChange={(e) => updateCI(key, e.target.value)} /></label>)}
        <label>Atributos técnicos JSON<textarea value={attributes} onChange={(e) => setAttributes(e.target.value)} /></label>
        <button>Guardar CI</button><button type="button" onClick={() => { setEditing(null); setCiForm(emptyCI); setAttributes('{}') }}>Limpiar formulario CI</button>
      </form>
    </section>}
    <section className="card" aria-label="Clasificaciones y ubicaciones"><h3>Clasificaciones y ubicaciones</h3>
      {[['clasificaciones', classes], ['ubicaciones', locations]].map(([entity, rows]) => <div key={entity}><h4>{entity}</h4><ul>{rows.map((row) => <li key={row.id}>{row.codigo} · {row.nombre} · {row.activo ? 'Activo' : 'Inactivo'}{row.padre_id && ` · padre ${row.padre_id}`}{admin && <><button onClick={() => setCatalog({ ...row, entity, padre_id: row.padre_id ?? '' })}>Editar {row.codigo}</button><button onClick={() => act(() => api(`/cmdb/catalogos/${entity}/${row.id}`, 'DELETE'))}>Desactivar {row.codigo}</button></>}</li>)}</ul></div>)}
      {admin && <form className="filter-grid" onSubmit={(e) => { e.preventDefault(); act(async () => { await api(`/cmdb/catalogos/${catalog.entity}${catalog.id ? `/${catalog.id}` : ''}`, catalog.id ? 'PUT' : 'POST', { codigo: catalog.codigo, nombre: catalog.nombre, padre_id: catalog.entity === 'clasificaciones' && catalog.padre_id ? Number(catalog.padre_id) : null, activo: catalog.activo }); setCatalog({ entity: catalog.entity, id: null, codigo: '', nombre: '', padre_id: '', activo: true }) }) }}>
        <label>Catálogo<select value={catalog.entity} onChange={(e) => setCatalog({ entity: e.target.value, id: null, codigo: '', nombre: '', padre_id: '', activo: true })}><option>clasificaciones</option><option>ubicaciones</option></select></label>
        <label>Código catálogo<input required value={catalog.codigo} onChange={(e) => setCatalog({ ...catalog, codigo: e.target.value })} /></label><label>Nombre catálogo<input required value={catalog.nombre} onChange={(e) => setCatalog({ ...catalog, nombre: e.target.value })} /></label>
        {catalog.entity === 'clasificaciones' && <label>Padre clasificación<select value={catalog.padre_id} onChange={(e) => setCatalog({ ...catalog, padre_id: e.target.value })}><option value="">Sin padre</option>{classes.filter((c) => c.id !== catalog.id && c.activo).map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}</select></label>}
        <label><input type="checkbox" checked={catalog.activo} onChange={(e) => setCatalog({ ...catalog, activo: e.target.checked })} /> Catálogo activo</label><button>Guardar catálogo CMDB</button>
      </form>}
    </section>
  </section>
}
