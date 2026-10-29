import {useEffect,useState} from 'react'
import {deskRequest} from './deskApi.js'
const time=v=>v===null||v===undefined?'Sin datos':`${Number(v).toLocaleString(undefined,{maximumFractionDigits:1})} min`
const name=s=>s.replaceAll('_',' ')

export default function DeskDashboard({token}) {
 const [scope,setScope]=useState('propios'),[queue,setQueue]=useState(''),[process,setProcess]=useState(''),[page,setPage]=useState(1)
 const [queues,setQueues]=useState([]),[spaces,setSpaces]=useState(null),[data,setData]=useState(null),[error,setError]=useState(''),[refresh,setRefresh]=useState(0)
 useEffect(()=>{Promise.all([deskRequest(token,'/desk/colas'),deskRequest(token,'/desk/espacios')]).then(([q,s])=>{setQueues(q);setSpaces(s);setScope(s.consola?'colas':'propios')}).catch(e=>setError(e.message))},[token])
 useEffect(()=>{let live=true;setError('');setData(null);const query=new URLSearchParams({ambito:scope,page,page_size:25});if(queue)query.set('cola_id',queue);if(process)query.set('proceso',process)
  deskRequest(token,`/desk/tablero?${query}`).then(r=>{if(live)setData(r)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}
 },[token,scope,queue,process,page,refresh])
 const filter=(setter,value)=>{setter(value);setPage(1)}
 return <section aria-label="Tablero de atención"><div className="card"><h2>Tablero de atención</h2><p>Objetivos en <strong>tiempo calendario, 24 × 7</strong>. Las esperas y aprobaciones cuentan; no se descuentan pausas. Cada reapertura inicia otro ciclo.</p>
  <div className="filter-grid"><label>Ámbito del tablero<select value={scope} onChange={e=>{filter(setScope,e.target.value);setQueue('')}}><option value="propios">Mis tickets</option>{spaces?.consola&&<option value="colas">Colas autorizadas</option>}</select></label>
  <label>Cola del tablero<select value={queue} onChange={e=>filter(setQueue,e.target.value)}><option value="">Todas</option>{queues.filter(q=>scope==='propios'||q.mis_permisos.includes('consultar')).map(q=><option key={q.id} value={q.id}>{q.nombre}</option>)}</select></label>
  <label>Proceso del tablero<select value={process} onChange={e=>filter(setProcess,e.target.value)}><option value="">Todos</option>{[...new Set(queues.map(q=>q.proceso))].map(p=><option key={p}>{p}</option>)}</select></label><button onClick={()=>setRefresh(x=>x+1)}>Actualizar tablero</button></div>
  {error&&<p role="alert" className="error">{error}</p>}
 </div>{data&&<>
  <div className="metric-grid" aria-label="Cantidades de tickets">{Object.entries(data.cantidades).map(([state,count])=><article className="card metric" key={state}><span>{name(state)}</span><strong>{count}</strong></article>)}</div>
  <section className="card"><h3>Tiempos y objetivos</h3><p>{data.total} tickets · {data.ciclos} ciclos · {data.reaperturas_registradas} reaperturas registradas. Corte: {new Date(data.calculado_at).toLocaleString()}.</p>
   <p>Primera atención promedio: <strong>{time(data.promedio_primera_atencion_min)}</strong> ({data.muestras_primera_atencion} muestras). Resolución promedio: <strong>{time(data.promedio_resolucion_min)}</strong> ({data.muestras_resolucion} muestras).</p>
   <p>Los promedios incluyen todos los ciclos con esa marca registrada; los pendientes no se consideran como cero.</p>
   {data.ciclos_migrados>0&&<p>Hay {data.ciclos_migrados} ciclos anteriores a esta versión. Sus objetivos históricos son desconocidos; las reaperturas previas no se reconstruyen.</p>}
   <div className="objective-grid">{[['Primera atención',data.objetivos_atencion],['Resolución',data.objetivos_resolucion]].map(([title,counts])=><div key={title}><h4>{title}: objetivos por ciclo</h4><ul>{Object.entries(counts).map(([key,count])=><li key={key}><span>{name(key)}</span><strong>{count}</strong></li>)}</ul></div>)}</div>
   <p>Sin objetivo significa que no había un objetivo configurado al iniciar el ciclo. Vencido es un objetivo abierto superado; incumplido corresponde a un tiempo ya completado. Los cierres sin resolución no aplican al objetivo de resolución.</p>
   <div className="analytics-columns"><div><h4>Cantidad por cola actual</h4><ul>{data.por_cola.map(q=><li key={q.cola_id}><span>{q.cola}</span><strong>{q.cantidad}</strong></li>)}</ul></div>
   <div><h4>Cantidad por proceso</h4><ul>{Object.entries(data.por_proceso).map(([key,count])=><li key={key}><span>{name(key)}</span><strong>{count}</strong></li>)}</ul></div><div><h4>Cantidad por prioridad</h4><ul>{Object.entries(data.por_prioridad).map(([key,count])=><li key={key}><span>Prioridad {key}</span><strong>{count}</strong></li>)}</ul></div></div>
  </section>
  <section className="card"><h3>Antigüedad y atención por ticket</h3><p>Orden: mayor antigüedad. Objetivos y tiempos de la fila corresponden al ciclo actual.</p>
   <div className="table-scroll"><table><thead><tr>{['Ticket','Cola','Estado','Ciclo','Antigüedad','Primera atención','Resolución','Objetivo atención','Objetivo resolución'].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{data.tickets.map(t=><tr key={t.ticket_id}><td>{t.numero}<br/>{t.titulo}</td><td>{t.cola}</td><td>{name(t.estado)}</td><td>{t.ciclo}</td><td>{time(t.antiguedad_min)}</td><td>{time(t.primera_atencion_min)}</td><td>{time(t.resolucion_min)}</td><td>{time(t.objetivo_atencion_min)} · {name(t.estado_objetivo_atencion)}</td><td>{time(t.objetivo_resolucion_min)} · {name(t.estado_objetivo_resolucion)}</td></tr>)}</tbody></table></div>
   {data.tickets.length===0&&<p>No hay tickets para este ámbito y filtros.</p>}<p>Página {page} · {data.detalle_total} tickets</p><button disabled={page===1} onClick={()=>setPage(page-1)}>Anterior tablero</button><button disabled={page*25>=data.detalle_total} onClick={()=>setPage(page+1)}>Siguiente tablero</button>
  </section>
 </>}</section>
}
