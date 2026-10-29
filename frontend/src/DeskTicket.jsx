import { useEffect, useRef, useState } from 'react'
import ProcessPanel from './ProcessPanel.jsx'
import { downloadAttachment } from './deskApi.js'

export default function DeskTicket({ticket,mode,queues,users,services,me,token,api,act,refresh,open}) {
  const detailRef=useRef(null)
  useEffect(()=>{detailRef.current?.scrollIntoView({block:'start'})},[ticket.id])
  const [text,setText]=useState(''),[internal,setInternal]=useState(false)
  const [target,setTarget]=useState(''),[destination,setDestination]=useState(''),[reason,setReason]=useState('')
  const [other,setOther]=useState(''),[kind,setKind]=useState('relacionado')
  const [file,setFile]=useState(null),[fileInternal,setFileInternal]=useState(false)
  const [editing,setEditing]=useState(null)
  const queue=queues.find(q=>q.id===ticket.cola_id)
  const readonly=me.role==='consulta'
  const support=mode!=='portal'&&!readonly&&(me.role==='administrador'||me.roles.includes('agente'))
  const can=p=>mode!=='portal'&&!readonly&&(me.role==='administrador'||queue?.mis_permisos.includes(p))
  const mutate=(path,body)=>act(async()=>{await api(`/desk/tickets/${ticket.id}/${path}`,'POST',body);await refresh()})
  function edit() {
    setEditing({titulo:ticket.titulo,descripcion:ticket.descripcion,servicio_id:ticket.servicio_id,prioridad:ticket.prioridad,
      impacto:ticket.impacto,urgencia:ticket.urgencia,canal:ticket.canal,
      ci_ids:ticket.ci.map(c=>c.id).join(','),motivo_sin_ci:ticket.motivo_sin_ci||'',motivo:''})
  }
  return <section ref={detailRef} className="card ticket-detail" aria-label="Ficha de ticket"><h3>{ticket.numero} · {ticket.titulo}</h3>
    <p>{ticket.descripcion}</p><p>{ticket.proceso} · {ticket.tipo} · {ticket.estado} · prioridad {ticket.prioridad}</p>
    <p>Cola: {ticket.cola_nombre} · solicitante: {ticket.solicitante_id} · creador: {ticket.creador_id} · responsable: {ticket.responsable_id??'Sin asignar'}</p>
    <p>Servicio: {ticket.servicio_id} · nivel 1: {ticket.level_1_code}</p>
    <p>CI: {ticket.ci.map(c=>`${c.codigo} (ID ${c.id})`).join(', ')||ticket.motivo_sin_ci}</p>
    <p>Resolución: {ticket.resolucion??'Pendiente'} · creado: {ticket.created_at} · actualizado: {ticket.updated_at}</p>
    {support&&can('atender')&&<><button onClick={()=>mutate('tomar')}>Tomar ticket</button><button onClick={edit}>Editar ticket</button>
      <form className="filter-grid" onSubmit={e=>{e.preventDefault();mutate('asignar',{usuario_id:Number(target),motivo:reason})}}>
        <label>Agente asignado<select required value={target} onChange={e=>setTarget(e.target.value)}><option value="">Seleccione</option>{users.filter(u=>u.is_active).map(u=><option key={u.id} value={u.id}>{u.username}</option>)}</select></label>
        <label>Motivo asignación<input required value={reason} onChange={e=>setReason(e.target.value)}/></label><button>Asignar agente</button>
      </form>
      </>}
    {support&&can('transferir')&&<form className="filter-grid" onSubmit={e=>{e.preventDefault();mutate(e.nativeEvent.submitter.value,{cola_id:Number(destination),motivo:reason})}}>
      <label>Cola destino<select required value={destination} onChange={e=>setDestination(e.target.value)}><option value="">Seleccione</option>{queues.filter(q=>q.activo&&q.id!==ticket.cola_id&&q.proceso===ticket.proceso).map(q=><option key={q.id} value={q.id}>{q.nombre} · nivel {q.nivel_soporte}</option>)}</select></label>
      <label>Motivo transferencia<input required value={reason} onChange={e=>setReason(e.target.value)}/></label><button value="transferir">Transferir ticket</button><button value="escalar">Escalar ticket</button>
    </form>}
    {editing&&<form className="filter-grid" onSubmit={e=>{e.preventDefault();act(async()=>{await api(`/desk/tickets/${ticket.id}`,'PUT',{...editing,ci_ids:editing.ci_ids.split(',').filter(x=>x.trim()).map(Number),motivo_sin_ci:editing.motivo_sin_ci||null});setEditing(null);await refresh()})}}>
      <h4>Editar datos del ticket</h4>{['titulo','descripcion','ci_ids','motivo_sin_ci','motivo'].map(k=><label key={k}>{k} edición<input required={['titulo','descripcion','motivo'].includes(k)} value={editing[k]} onChange={e=>setEditing({...editing,[k]:e.target.value})}/></label>)}
      <label>Servicio edición<select value={editing.servicio_id} onChange={e=>setEditing({...editing,servicio_id:Number(e.target.value)})}>{services.filter(s=>s.active).map(s=><option key={s.id} value={s.id}>{s.code}</option>)}</select></label>
      <label>Prioridad edición<input type="number" min="1" max="4" value={editing.prioridad} onChange={e=>setEditing({...editing,prioridad:Number(e.target.value)})}/></label><button>Guardar edición ticket</button><button type="button" onClick={()=>setEditing(null)}>Cancelar edición</button>
    </form>}
    <ProcessPanel key={`${ticket.id}-${ticket.flujo?.updated_at}`} {...{ticket,users,services,queues,me,api,act,refresh,support,can}}/>
    {ticket.notificaciones?.length>0&&<section aria-label="Notificaciones del evento"><h4>Notificaciones del evento</h4>
      <ul>{ticket.notificaciones.map(n=><li key={n.id}><strong>{new Date(n.fecha).toLocaleString()}</strong> · {n.mensaje}
        {n.incidente_id?<button type="button" onClick={()=>open(n.incidente_id)}>Consultar incidente {n.incidente_numero}</button>:<span> · Incidente fuera de tu ámbito de consulta</span>}
      </li>)}</ul></section>}
    <h4>Comentarios y notas</h4><ul aria-label="Comentarios del ticket">{ticket.comentarios.map(c=><li key={c.id}>{c.interno?'Nota interna':'Público'} · {c.actor} · {c.fecha}: {c.texto}</li>)}</ul>
    {!readonly&&(ticket.solicitante_id===me.id||support&&can('atender'))&&<form onSubmit={e=>{e.preventDefault();mutate('comentarios',{texto:text,interno:internal});setText('')}}>
      <label>Comentario<textarea required value={text} onChange={e=>setText(e.target.value)}/></label>
      {support&&can('atender')&&<label><input type="checkbox" checked={internal} onChange={e=>setInternal(e.target.checked)}/>Nota interna</label>}<button>Agregar comentario</button>
    </form>}
    <h4>Adjuntos</h4><ul>{ticket.adjuntos.map(f=><li key={f.id}>{f.nombre} · {f.bytes} bytes · {f.interno?'Interno':'Público'} <button onClick={()=>act(()=>downloadAttachment(token,f))}>Descargar {f.nombre}</button></li>)}</ul>
    {!readonly&&(ticket.solicitante_id===me.id||support&&can('atender'))&&<form onSubmit={e=>{e.preventDefault();act(async()=>{if(!file)throw new Error('Seleccione un archivo');await api(`/desk/tickets/${ticket.id}/adjuntos?nombre=${encodeURIComponent(file.name)}&interno=${fileInternal}`,'POST',file,{'Content-Type':file.type||'application/octet-stream'});await refresh()})}}>
      <label>Archivo adjunto<input type="file" accept=".txt,.pdf,.png,.jpg,.jpeg" onChange={e=>setFile(e.target.files[0])}/></label>
      <p>Máximo 5 MiB. TXT UTF-8, PDF, PNG o JPEG.</p>{support&&can('atender')&&<label><input type="checkbox" checked={fileInternal} onChange={e=>setFileInternal(e.target.checked)}/>Adjunto interno</label>}<button>Subir adjunto</button>
    </form>}
    <h4>Tickets relacionados</h4><ul>{ticket.vinculos.map(v=><li key={v.id}>{v.tipo} <button onClick={()=>open(v.otro_id)}>{v.otro_numero}</button></li>)}</ul>
    {support&&can('atender')&&<form className="filter-grid" onSubmit={e=>{e.preventDefault();mutate('vinculos',{ticket_id:Number(other),tipo:kind})}}>
      <label>ID ticket relacionado<input required type="number" min="1" value={other} onChange={e=>setOther(e.target.value)}/></label><label>Tipo vínculo<select value={kind} onChange={e=>setKind(e.target.value)}>{['relacionado','duplicado','incidente_problema','problema_cambio'].map(k=><option key={k}>{k}</option>)}</select></label><button>Vincular ticket</button>
    </form>}
    {ticket.flujo?.estado==='pendiente_aprobacion'&&can('aprobar')&&(me.role==='administrador'||me.roles.includes('aprobador'))&&<form onSubmit={e=>{e.preventDefault();mutate('aprobaciones',{aprobado:e.nativeEvent.submitter.value==='si',motivo:reason})}}>
      <label>Motivo decisión<input required value={reason} onChange={e=>setReason(e.target.value)}/></label><button value="si">Registrar aprobación</button><button value="no">Registrar rechazo</button>
    </form>}
    <ul>{ticket.aprobaciones.map(a=><li key={a.id}>{a.aprobado?'Aprobado':'Rechazado'} · usuario {a.actor_id} · {a.motivo}</li>)}</ul>
    <details><summary>Bitácora del ticket</summary><ul>{ticket.historial.map(h=><li key={h.id}>{h.fecha} · {h.actor} · {h.accion}<pre>{JSON.stringify({antes:h.antes,despues:h.despues},null,2)}</pre></li>)}</ul></details>
  </section>
}
