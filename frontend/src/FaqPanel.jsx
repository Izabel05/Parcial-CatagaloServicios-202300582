import {useEffect,useState} from 'react'
import {deskRequest} from './deskApi.js'
const empty={titulo:'',pregunta:'',respuesta:'',servicio_id:'',publicado:false}

export default function FaqPanel({token,administration=false}) {
 const [items,setItems]=useState([]),[search,setSearch]=useState(''),[query,setQuery]=useState(''),[revision,setRevision]=useState(0)
 const [form,setForm]=useState(empty),[id,setId]=useState(null),[error,setError]=useState(''),[notice,setNotice]=useState(''),[services,setServices]=useState([])
 useEffect(()=>{let live=true;deskRequest(token,`/desk/faq?search=${encodeURIComponent(query)}&administracion=${administration}`).then(r=>{if(live)setItems(r)}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[token,query,revision,administration])
 useEffect(()=>{if(administration)deskRequest(token,'/services?page_size=100').then(r=>setServices(r.items)).catch(e=>setError(e.message))},[token,administration])
 async function save(e){e.preventDefault();setError('');setNotice('');try{await deskRequest(token,`/desk/faq${id?'/'+id:''}`,id?'PUT':'POST',{...form,servicio_id:form.servicio_id?Number(form.servicio_id):null});setForm(empty);setId(null);setRevision(x=>x+1);setNotice('Artículo guardado')}catch(e){setError(e.message)}}
 return <section className="card" aria-label={administration?'Administración FAQ':'Autoservicio FAQ'}><h2>{administration?'Administrar FAQ':'FAQ y autoservicio'}</h2>
  <p>Busca una respuesta antes de abrir un ticket. No incluyas contraseñas ni datos sensibles en tus solicitudes.</p>
  {error&&<p role="alert" className="error">{error}</p>}{notice&&<p role="status">{notice}</p>}
  <form className="filter-grid" onSubmit={e=>{e.preventDefault();setQuery(search)}}><label>Buscar en FAQ<input maxLength={200} value={search} onChange={e=>setSearch(e.target.value)}/></label><button>Buscar respuestas</button></form>
  <p>{items.length} artículos</p>{items.length===0&&<p>No hay respuestas para esta búsqueda. Puedes crear una solicitud desde el portal.</p>}
  {items.map(item=><article key={item.id} className="faq-article"><details><summary>{item.titulo}</summary><h3>{item.pregunta}</h3><p className="preserve-lines">{item.respuesta}</p>{item.servicio_codigo&&<p>Servicio: {item.servicio_codigo}</p>}<small>Actualizado: {new Date(item.updated_at).toLocaleString()}</small></details>
   {administration&&<><p>{item.publicado?'Publicado':'Borrador'}</p><button onClick={()=>{setId(item.id);setForm(Object.fromEntries(Object.keys(empty).map(k=>[k,item[k]??''])))}}>Editar {item.titulo}</button></>}
  </article>)}
  {administration&&<form className="filter-grid" onSubmit={save}><h3>{id?'Editar artículo':'Nuevo artículo'}</h3>{['titulo','pregunta','respuesta'].map(k=><label key={k}>{({titulo:'Título FAQ',pregunta:'Pregunta FAQ',respuesta:'Respuesta FAQ'})[k]}<textarea required maxLength={k==='respuesta'?8000:k==='pregunta'?500:200} value={form[k]} onChange={e=>setForm({...form,[k]:e.target.value})}/></label>)}
   <label>Servicio FAQ<select value={form.servicio_id} onChange={e=>setForm({...form,servicio_id:e.target.value})}><option value="">General</option>{services.filter(s=>s.active).map(s=><option key={s.id} value={s.id}>{s.code} · {s.name}</option>)}</select></label>
   <label><input type="checkbox" checked={form.publicado} onChange={e=>setForm({...form,publicado:e.target.checked})}/>Publicado en autoservicio</label><button>Guardar artículo FAQ</button><button type="button" onClick={()=>{setId(null);setForm(empty)}}>Cancelar artículo</button>
  </form>}
 </section>
}
