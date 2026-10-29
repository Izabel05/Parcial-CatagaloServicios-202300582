import { useEffect, useState } from 'react'
import { deskRequest } from './deskApi.js'
import DeskTicket from './DeskTicket.jsx'
import DeskQueues from './DeskQueues.jsx'

const empty={titulo:'',descripcion:'',servicio_id:'',cola_id:'',prioridad:3,impacto:'medio',urgencia:'media',canal:'portal',ci_ids:'',motivo_sin_ci:''}

export default function DeskPanel({token,mode}) {
  const [error,setError]=useState(''),[notice,setNotice]=useState('')
  const [me,setMe]=useState(null),[queues,setQueues]=useState([]),[users,setUsers]=useState([]),[services,setServices]=useState([])
  const [options,setOptions]=useState({procesos:[],permisos:[]})
  const [revision,setRevision]=useState(0),[page,setPage]=useState(1),[result,setResult]=useState({items:[],total:0})
  const [filters,setFilters]=useState({search:'',cola_id:'',servicio_id:'',estado:'',prioridad:'',responsable_id:'',proceso:'',desde:'',hasta:''})
  const [draft,setDraft]=useState(filters),[form,setForm]=useState(empty),[ticket,setTicket]=useState(null)
  const api=(...args)=>deskRequest(token,...args)
  async function act(work) {
    setError('');setNotice('')
    try{await work();setRevision(r=>r+1);setNotice('Operación completada')}
    catch(e){setError(e.message)}
  }
  useEffect(()=>{
    let current=true
    Promise.all([api('/desk/me'),api('/desk/colas'),api('/usuarios'),api('/services?page_size=100'),api('/desk/opciones')])
      .then(([m,q,u,s,o])=>{if(current){setMe(m);setQueues(q);setUsers(u);setServices(s.items);setOptions(o)}})
      .catch(e=>{if(current)setError(e.message)})
    return()=>{current=false}
  },[token,revision])
  useEffect(()=>{
    let current=true
    const query=new URLSearchParams({page,page_size:25,ambito:mode==='portal'?'propios':'colas'})
    Object.entries(filters).forEach(([k,v])=>{if(v!=='')query.set(k,['desde','hasta'].includes(k)?new Date(v).toISOString():v)})
    api(`/desk/tickets?${query}`).then(r=>{if(current)setResult(r)}).catch(e=>{if(current)setError(e.message)})
    return()=>{current=false}
  },[token,revision,page,filters,mode])
  async function open(id) {
    setError('')
    try{setTicket(await api(`/desk/tickets/${id}?ambito=${mode==='portal'?'propios':'colas'}`))}catch(e){setError(e.message)}
  }
  const setField=(key,value)=>setForm(f=>({...f,[key]:value}))
  if(!me)return <section><h3>{mode==='portal'?'Portal del solicitante':'Consola del agente'}</h3>{error?<p role="alert">{error}</p>:<p>Cargando…</p>}</section>
  const create=mode==='portal'&&me.role!=='consulta'&&(me.role==='administrador'||me.roles.includes('solicitante'))
  if(mode==='administracion')return <>{error&&<p role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}<DeskQueues queues={queues.filter(q=>q.mis_permisos.includes('administrar')||me.role==='administrador')} users={users} options={options} api={api} act={act} admin={me.role==='administrador'}/></>
  const visibleQueues=mode==='portal'?queues:queues.filter(q=>q.mis_permisos.includes('consultar'))
  return <section aria-label="Service Desk"><div className="card"><h3>{mode==='portal'?'Portal del solicitante':'Consola del agente'}</h3><p>{mode==='portal'?'Solo tus tickets, comentarios y solicitudes.':'Colas autorizadas, asignación, atención y transferencias.'}</p></div>
    {error&&<p className="error" role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}
    <section className="card" aria-label="Búsqueda de tickets"><h3>Tickets disponibles</h3>
      <form className="filter-grid" onSubmit={e=>{e.preventDefault();setFilters(draft);setPage(1)}}>
        {['search','desde','hasta'].map(k=><label key={k}>{({search:'Número o título',desde:'Desde',hasta:'Hasta'})[k]}<input type={k==='search'?'text':'datetime-local'} value={draft[k]} onChange={e=>setDraft({...draft,[k]:e.target.value})}/></label>)}
        <label>Cola filtro<select value={draft.cola_id} onChange={e=>setDraft({...draft,cola_id:e.target.value})}><option value="">Todas</option>{visibleQueues.map(q=><option key={q.id} value={q.id}>{q.nombre}</option>)}</select></label>
        <label>Servicio filtro<select value={draft.servicio_id} onChange={e=>setDraft({...draft,servicio_id:e.target.value})}><option value="">Todos</option>{services.map(s=><option key={s.id} value={s.id}>{s.code}</option>)}</select></label>
        <label>Proceso filtro<select value={draft.proceso} onChange={e=>setDraft({...draft,proceso:e.target.value})}><option value="">Todos</option>{options.procesos.map(p=><option key={p}>{p}</option>)}</select></label>
        <label>Estado filtro<select value={draft.estado} onChange={e=>setDraft({...draft,estado:e.target.value})}><option value="">Todos</option>{options.estados.map(s=><option key={s}>{s}</option>)}</select></label>
        <label>Prioridad filtro<select value={draft.prioridad} onChange={e=>setDraft({...draft,prioridad:e.target.value})}><option value="">Todas</option>{[1,2,3,4].map(p=><option key={p}>{p}</option>)}</select></label>
        <label>Responsable filtro<select value={draft.responsable_id} onChange={e=>setDraft({...draft,responsable_id:e.target.value})}><option value="">Todos</option>{users.map(u=><option key={u.id} value={u.id}>{u.username}</option>)}</select></label><button>Filtrar tickets</button>
      </form><p>{result.total} tickets · página {page} · orden: prioridad 1–4, antigüedad e ID</p>
      <ul>{result.items.map(t=><li key={t.id}><button onClick={()=>open(t.id)}>{t.numero}</button> · {t.titulo} · {t.estado} · prioridad {t.prioridad} · {t.cola_nombre} · responsable {t.responsable_id??'Sin asignar'}</li>)}</ul>
      <button disabled={page===1} onClick={()=>setPage(page-1)}>Anterior tickets</button><button disabled={page*25>=result.total} onClick={()=>setPage(page+1)}>Siguiente tickets</button>
    </section>
    {create&&<section className="card" aria-label="Crear ticket"><h3>Nuevo ticket</h3><form className="filter-grid" onSubmit={e=>{e.preventDefault();act(async()=>{
      const saved=await api('/desk/tickets','POST',{...form,cola_id:Number(form.cola_id),servicio_id:Number(form.servicio_id),
        ci_ids:form.ci_ids.split(',').filter(x=>x.trim()).map(Number),motivo_sin_ci:form.motivo_sin_ci||null})
      setForm(empty);await open(saved.id)
    })}}>
      <label>Título ticket<input required value={form.titulo} onChange={e=>setField('titulo',e.target.value)}/></label>
      <label>Descripción ticket<textarea required value={form.descripcion} onChange={e=>setField('descripcion',e.target.value)}/></label>
      <label>Servicio ticket<select required value={form.servicio_id} onChange={e=>setField('servicio_id',e.target.value)}><option value="">Seleccione</option>{services.filter(s=>s.active).map(s=><option key={s.id} value={s.id}>{s.code} · {s.name}</option>)}</select></label>
      <label>Cola ticket<select required value={form.cola_id} onChange={e=>setField('cola_id',e.target.value)}><option value="">Seleccione</option>{queues.filter(q=>q.activo).map(q=><option key={q.id} value={q.id}>{q.nombre} · {q.proceso}</option>)}</select></label>
      <label>Prioridad ticket<input type="number" min="1" max="4" value={form.prioridad} onChange={e=>setField('prioridad',Number(e.target.value))}/></label>
      {[['impacto',['bajo','medio','alto']],['urgencia',['baja','media','alta']],['canal',['portal','telefono','correo','presencial','otro']]].map(([key,values])=><label key={key}>{key}<select value={form[key]} onChange={e=>setField(key,e.target.value)}>{values.map(v=><option key={v}>{v}</option>)}</select></label>)}
      <label>IDs de CI (separados por coma)<input value={form.ci_ids} onChange={e=>setField('ci_ids',e.target.value)}/></label>
      <label>Justificación sin CI<input value={form.motivo_sin_ci} onChange={e=>setField('motivo_sin_ci',e.target.value)}/></label><button>Crear ticket</button>
    </form></section>}
    {ticket&&<DeskTicket key={ticket.id} ticket={ticket} mode={mode} queues={visibleQueues} users={users} services={services} me={me} token={token} api={api} act={act} refresh={()=>open(ticket.id)} open={open}/>}
  </section>
}
