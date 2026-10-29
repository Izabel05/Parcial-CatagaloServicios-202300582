import { useState } from 'react'

const empty={codigo:'',nombre:'',descripcion:'',proceso:'incidentes',activo:true,nivel_soporte:1,
  ordenamiento:'prioridad_antiguedad',objetivo_primera_atencion_min:null,objetivo_resolucion_min:null,responsables_ids:[]}

export default function DeskQueues({queues,users,options,api,act,admin}) {
  const [form,setForm]=useState(empty)
  const [id,setId]=useState(null)
  const [grants,setGrants]=useState([])
  const [grant,setGrant]=useState({rol:'agente',usuario_id:'',permiso:'consultar'})
  const [target,setTarget]=useState('')
  const [roles,setRoles]=useState([])
  const [history,setHistory]=useState(null)
  const update=(key,value)=>setForm({...form,[key]:value})
  function edit(queue) {
    setId(queue.id);setForm(Object.fromEntries(Object.keys(empty).map(k=>[k,queue[k]])))
    setGrants(queue.permisos??[]);setHistory(null)
  }
  const managed=queues.filter(q=>q.mis_permisos.includes('administrar'))
  return <section className="card" aria-label="Administración de colas"><h3>Colas y permisos</h3><p>Objetivos en minutos calendario, 24 × 7. Los cambios se aplican a los ciclos que se inicien después de guardar.</p>
    <ul>{queues.map(q=><li key={q.id}>{q.codigo} · {q.nombre} · {q.proceso} · nivel {q.nivel_soporte} · {q.activo?'Activa':'Inactiva'} · permisos: {q.mis_permisos.join(', ')||'sin concesión'}
      {(admin||q.mis_permisos.includes('administrar'))&&<><button onClick={()=>edit(q)}>Editar cola {q.codigo}</button><button onClick={()=>act(()=>api(`/desk/colas/${q.id}`,'DELETE'))}>Desactivar cola {q.codigo}</button></>}</li>)}</ul>
    {(admin||managed.length>0)&&<><form className="filter-grid" onSubmit={e=>{e.preventDefault();act(async()=>{const q=await api(`/desk/colas${id?`/${id}`:''}`,id?'PUT':'POST',form);setId(q.id)})}}>
      <h4>{id?'Editar cola':'Nueva cola'}</h4>
      {['codigo','nombre','descripcion'].map(k=><label key={k}>{k} cola<input required={k!=='descripcion'} value={form[k]} onChange={e=>update(k,e.target.value)}/></label>)}
      <label>Proceso cola<select value={form.proceso} onChange={e=>update('proceso',e.target.value)}>{options.procesos.map(p=><option key={p}>{p}</option>)}</select></label>
      <label>Nivel soporte<input type="number" min="0" max="4" value={form.nivel_soporte} onChange={e=>update('nivel_soporte',Number(e.target.value))}/></label>
      {['objetivo_primera_atencion_min','objetivo_resolucion_min'].map(k=><label key={k}>{k==='objetivo_primera_atencion_min'?'Objetivo primera atención (minutos calendario)':'Objetivo resolución (minutos calendario)'}<input type="number" min="1" value={form[k]??''} onChange={e=>update(k,e.target.value?Number(e.target.value):null)}/></label>)}
      <label>Responsables de cola<select multiple value={form.responsables_ids.map(String)} onChange={e=>update('responsables_ids',Array.from(e.target.selectedOptions,o=>Number(o.value)))}>{users.filter(u=>u.is_active).map(u=><option key={u.id} value={u.id}>{u.username}</option>)}</select></label>
      <label><input type="checkbox" checked={form.activo} onChange={e=>update('activo',e.target.checked)}/>Cola activa</label>
      <button>Guardar cola</button><button type="button" onClick={()=>{setId(null);setForm(empty);setGrants([])}}>Limpiar cola</button>
    </form>
    {id&&<section aria-label="Permisos de cola"><h4>Permisos de cola {id}</h4><p>Roles o usuarios reciben permisos independientes. Consulta conserva solo lectura.</p>
      <ul>{grants.map((g,i)=><li key={i}>{g.rol||`Usuario ${g.usuario_id}`} · {g.permiso}<button onClick={()=>setGrants(grants.filter((_,n)=>n!==i))}>Quitar permiso {i+1}</button></li>)}</ul>
      <form className="filter-grid" onSubmit={e=>{e.preventDefault();setGrants([...grants,{rol:grant.usuario_id?null:grant.rol,usuario_id:grant.usuario_id?Number(grant.usuario_id):null,permiso:grant.permiso}])}}>
        <label>Rol de permiso<select value={grant.rol} onChange={e=>setGrant({...grant,rol:e.target.value,usuario_id:''})}>{['administrador','consulta','solicitante','agente','aprobador'].map(r=><option key={r}>{r}</option>)}</select></label>
        <label>Usuario de permiso<select value={grant.usuario_id} onChange={e=>setGrant({...grant,usuario_id:e.target.value})}><option value="">Usar rol</option>{users.filter(u=>u.is_active).map(u=><option key={u.id} value={u.id}>{u.username}</option>)}</select></label>
        <label>Permiso<select value={grant.permiso} onChange={e=>setGrant({...grant,permiso:e.target.value})}>{options.permisos.map(p=><option key={p}>{p}</option>)}</select></label><button>Agregar permiso</button>
      </form><button onClick={()=>act(()=>api(`/desk/colas/${id}/permisos`,'PUT',{permisos:grants}))}>Guardar permisos</button>{' '}
      <button onClick={()=>act(async()=>setHistory(await api(`/desk/colas/${id}/historial`)))}>Historial de cola</button>
      {history&&<pre>{JSON.stringify(history,null,2)}</pre>}
    </section>}</>}
    {admin&&<section aria-label="Roles Service Desk"><h4>Roles adicionales</h4>
      <label>Usuario para roles<select value={target} onChange={e=>{setTarget(e.target.value);setRoles([])}}><option value="">Seleccione</option>{users.filter(u=>u.is_active).map(u=><option key={u.id} value={u.id}>{u.username} · principal: {u.role}</option>)}</select></label>
      <button disabled={!target} onClick={()=>act(async()=>{const user=await api(`/desk/usuarios/${target}/roles`);setRoles(user.roles.filter(r=>['solicitante','agente','aprobador'].includes(r)))})}>Leer roles</button>
      {['solicitante','agente','aprobador'].map(r=><label key={r}><input type="checkbox" checked={roles.includes(r)} onChange={e=>setRoles(e.target.checked?[...roles,r]:roles.filter(x=>x!==r))}/>{r}</label>)}
      <button disabled={!target} onClick={()=>act(()=>api(`/desk/usuarios/${target}/roles`,'PUT',{roles}))}>Guardar roles adicionales</button>
    </section>}
  </section>
}
