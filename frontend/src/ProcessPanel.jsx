import {useState,useEffect} from 'react'

const fields={
 nuevos_servicios:['necesidad','analisis_viabilidad','viable','plan_implementacion','evidencia_implementacion','validacion'],
 cambios:['evaluacion_impacto','riesgo','plan_pruebas','plan_reversion','programado_para','resultado_ejecucion','resultado_pruebas','validacion'],
 incidentes:['categoria','interrupcion','degradacion','seguridad','duracion_estimada_horas','duracion_real_horas','redundancia_disponible','justificacion_categoria','diagnostico','evidencia_recuperacion','solucion'],
 eventos:['categoria','evaluacion','cola_incidente_id','incidente_id'],
 problemas:['incidentes_ids','causa_raiz','solucion_temporal','error_conocido','solucion_definitiva','cambio_correctivo_id'],
 accesos:['beneficiario_id','recurso','permiso_solicitado','accion','validacion_solicitud','evidencia_provision','validacion'],
 servicios_tecnologia:['detalle_solicitud','validacion','evidencia_cumplimiento'],
}
const booleans=new Set(['viable','interrupcion','degradacion','seguridad','redundancia_disponible','error_conocido'])
const label=k=>k.replaceAll('_',' ')

export default function ProcessPanel({ticket,users,services,queues,me,api,act,refresh,support,can}) {
 const flow=ticket.flujo
 const [data,setData]=useState(flow?.datos||{}),[reason,setReason]=useState(''),[destination,setDestination]=useState('')
 const [service,setService]=useState(''),[newService,setNewService]=useState(false)
 const [draft,setDraft]=useState({code:'',name:'',level_1_code:'',service_class_id:'',criticality_id:'',service_type_id:'',responsible_section_id:''})
 const [catalogs,setCatalogs]=useState({}),[levels,setLevels]=useState([]),[sections,setSections]=useState([])
 useEffect(()=>{if(ticket.proceso==='nuevos_servicios') Promise.all([api('/services/catalog-options'),api('/services/level-1'),api('/secciones')]).then(([c,l,s])=>{setCatalogs(c);setLevels(l);setSections(s)}).catch(()=>{})},[ticket.id])
 const serviceOptions={level_1_code:levels.map(x=>({value:x.code,text:x.name})),service_class_id:catalogs.service_classes?.map(x=>({value:x.id,text:x.name})),criticality_id:catalogs.criticalities?.map(x=>({value:x.id,text:x.name})),service_type_id:catalogs.service_types?.map(x=>({value:x.id,text:x.name})),responsible_section_id:sections.map(x=>({value:x.id,text:x.nombre}))}
 const [confirmation,setConfirmation]=useState('')
 if(!flow)return null
 const active=!['resuelto','cerrado','rechazado'].includes(flow.estado)
 const mutate=(path,body,method='POST')=>act(async()=>{await api(`/desk/tickets/${ticket.id}/${path}`,method,body);await refresh()})
 const options=k=>k==='categoria'?(ticket.proceso==='incidentes'?['I0','I1','I2','I3','I4','I5','I6']:['E0','E1','E2','E3']):k==='riesgo'?['bajo','medio','alto']:k==='accion'?['provisionar','revocar']:null
 const convert=()=>Object.fromEntries(Object.entries(data).filter(([key,value])=>key!=='confirmacion'&&value!=='').map(([key,value])=>[key,value===null?null:key==='incidentes_ids'?(Array.isArray(value)?value:String(value).split(',').filter(x=>x.trim()).map(Number)):key.endsWith('_id')||key.endsWith('_horas')?Number(value):key==='programado_para'?new Date(value).toISOString():value]))
 return <section aria-label="Proceso del ticket"><h4>Proceso: {label(ticket.proceso)}</h4>
  <p>Etapa: <strong>{label(flow.estado)}</strong> · ciclo {flow.version} · servicio resultante: {flow.servicio_resultado_id??'Pendiente'}</p>
  {support&&can('atender')&&active?<form className="filter-grid" onSubmit={e=>{e.preventDefault();mutate('proceso/datos',{datos:convert(),motivo:reason},'PATCH')}}>
   {fields[ticket.proceso].map(key=><label key={key}>{label(key)}
    {booleans.has(key)?<select value={data[key]===undefined||data[key]===null?'':String(data[key])} onChange={e=>setData({...data,[key]:e.target.value===''?null:e.target.value==='true'})}><option value="">Sin determinar</option><option value="true">Sí</option><option value="false">No</option></select>
    :options(key)?<select value={data[key]||''} onChange={e=>setData({...data,[key]:e.target.value})}><option value="">Seleccione</option>{options(key).map(x=><option key={x}>{x}</option>)}</select>
    :key==='cola_incidente_id'?<select value={data[key]||''} onChange={e=>setData({...data,[key]:Number(e.target.value)||null})}><option value="">Seleccione cola de incidentes</option>{queues.filter(q=>q.activo&&q.proceso==='incidentes').map(q=><option key={q.id} value={q.id}>{q.nombre}</option>)}</select>
    :key==='beneficiario_id'?<select value={data[key]||''} onChange={e=>setData({...data,[key]:e.target.value})}><option value="">Seleccione beneficiario</option>{users.filter(u=>u.is_active).map(u=><option key={u.id} value={u.id}>{u.username}</option>)}</select>
    :key.endsWith('_id')||key.endsWith('_horas')?<input type="number" step="any" min="0" value={data[key]??''} onChange={e=>setData({...data,[key]:e.target.value})}/>
    :key==='programado_para'?<input type="datetime-local" value={(data[key]||'').slice(0,16)} onChange={e=>setData({...data,[key]:e.target.value})}/>
    :<textarea maxLength={4000} value={Array.isArray(data[key])?data[key].join(','):data[key]??''} onChange={e=>setData({...data,[key]:e.target.value})}/>}
   </label>)}
   <label>Motivo datos del proceso<input required value={reason} onChange={e=>setReason(e.target.value)}/></label><button>Guardar datos del proceso</button>
  </form>:<dl>{Object.entries(flow.datos).map(([key,value])=><div key={key}><dt>{label(key)}</dt><dd>{value===null?'Sin determinar':String(value)}</dd></div>)}</dl>}
  {support&&can('atender')&&<form className="filter-grid" onSubmit={e=>{e.preventDefault();mutate('proceso/transiciones',{estado:destination,motivo:reason})}}>
   <label>Etapa destino<select required value={destination} onChange={e=>setDestination(e.target.value)}><option value="">Seleccione etapa</option>{(active?flow.transiciones.filter(x=>!['aprobado','rechazado'].includes(x)):[...(flow.estado==='resuelto'||flow.estado==='rechazado'?['cerrado']:[]),...(flow.estado==='rechazado'?[]:['abierto'])]).map(x=><option key={x}>{x}</option>)}</select></label>
   <label>Motivo transición<input required value={reason} onChange={e=>setReason(e.target.value)}/></label><button>Avanzar proceso</button>
  </form>}
  {ticket.proceso==='eventos'&&support&&can('atender')&&<button onClick={()=>mutate('proceso/incidente')}>Generar o vincular incidente</button>}
  {ticket.proceso==='nuevos_servicios'&&support&&can('atender')&&flow.estado==='aprobado'&&<form className="filter-grid" onSubmit={e=>{e.preventDefault();mutate('proceso/servicio',{motivo:reason,...(newService?{nuevo:Object.fromEntries(Object.entries(draft).map(([k,v])=>[k,k.endsWith('_id')?Number(v):v]))}:{servicio_id:Number(service)})})}}>
   <label><input type="checkbox" checked={newService} onChange={e=>setNewService(e.target.checked)}/>Crear servicio nuevo</label>
   {newService?Object.keys(draft).map(k=><label key={k}>{({code:'Código',name:'Nombre',level_1_code:'Nivel 1',service_class_id:'Clase del servicio',criticality_id:'Criticidad',service_type_id:'Tipo del servicio',responsible_section_id:'Sección responsable'})[k]}{serviceOptions[k]?<select required value={draft[k]} onChange={e=>setDraft({...draft,[k]:e.target.value})}><option value="">Seleccione</option>{serviceOptions[k].map(x=><option key={x.value} value={x.value}>{x.text}</option>)}</select>:<input required value={draft[k]} onChange={e=>setDraft({...draft,[k]:e.target.value})}/>}</label>):<label>Servicio aprobado<select required value={service} onChange={e=>setService(e.target.value)}><option value="">Seleccione servicio</option>{services.filter(s=>s.active).map(s=><option key={s.id} value={s.id}>{s.code} · {s.name}</option>)}</select></label>}
   <label>Motivo publicación<input required value={reason} onChange={e=>setReason(e.target.value)}/></label><button>Crear o vincular servicio aprobado</button>
  </form>}
  {ticket.proceso==='servicios_tecnologia'&&flow.estado==='confirmacion'&&me.role!=='consulta'&&ticket.solicitante_id===me.id&&<form onSubmit={e=>{e.preventDefault();mutate('proceso/confirmacion',{texto:confirmation})}}><label>Confirmación del solicitante<textarea required value={confirmation} onChange={e=>setConfirmation(e.target.value)}/></label><button>Confirmar cumplimiento</button></form>}
 </section>
}
