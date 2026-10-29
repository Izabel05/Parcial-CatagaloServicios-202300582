import {useEffect, useState} from 'react'
import {deskRequest} from './deskApi.js'

export default function CiTicketHistory({token, ciId}) {
 const [page,setPage]=useState(1),[result,setResult]=useState(null),[error,setError]=useState('')
 const [ticketId,setTicketId]=useState(null),[ticket,setTicket]=useState(null)
 useEffect(()=>{
  let live=true;setResult(null);setError('')
  deskRequest(token,`/cmdb/ci/${ciId}/tickets?page=${page}&page_size=10`)
   .then(data=>{if(live)setResult(data)}).catch(e=>{if(live)setError(e.message)})
  return()=>{live=false}
 },[token,ciId,page])
 useEffect(()=>{
  let live=true;setTicket(null)
  if(ticketId)deskRequest(token,`/desk/tickets/${ticketId}`)
   .then(data=>{if(live)setTicket(data)}).catch(e=>{if(live)setError(e.message)})
  return()=>{live=false}
 },[token,ticketId])
 return <section aria-label="Tickets del CI">
  <h4>Historial de tickets asociados</h4>
  <p>Solo se muestran tus tickets y los de las colas que puedes consultar, del más reciente al más antiguo.</p>
  {error&&<p role="alert" className="error">{error}</p>}
  {result?<><p>{result.total} tickets visibles · página {page}</p>
   <ul className="record-list">{result.items.map(t=><li key={t.id}>
    <button type="button" onClick={()=>setTicketId(t.id)}>{t.numero}</button>
    <div className="record-body"><strong>{t.titulo}</strong><small>{t.cola_nombre} · {new Date(t.created_at).toLocaleString()}</small></div>
    <span className={`status-pill ${t.estado}`}>{t.estado.replaceAll('_',' ')}</span>
   </li>)}</ul>
   {result.total===0&&<p>No tienes tickets visibles asociados a este CI.</p>}
   <div className="pagination"><button type="button" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Anterior historial CI</button>
   <button type="button" disabled={page*10>=result.total} onClick={()=>setPage(p=>p+1)}>Siguiente historial CI</button></div>
  </>:<p>Cargando historial de tickets…</p>}
  {ticket&&<section className="card" aria-label="Ticket asociado al CI"><h4>{ticket.numero} · {ticket.titulo}</h4>
   <p>{ticket.descripcion}</p><p>Estado: {ticket.estado.replaceAll('_',' ')} · proceso: {ticket.proceso.replaceAll('_',' ')}</p>
   <p>Resolución: {ticket.resolucion||'Pendiente'}</p>
   <details><summary>Bitácora del ticket asociado</summary><ul>{ticket.historial.map(h=><li key={h.id}>
    {new Date(h.fecha).toLocaleString()} · {h.actor} · {h.accion}
    <pre>{JSON.stringify({antes:h.antes,despues:h.despues},null,2)}</pre>
   </li>)}</ul></details></section>}
 </section>
}
