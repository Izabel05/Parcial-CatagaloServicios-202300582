import {useEffect,useState} from 'react'
import {deskRequest} from './deskApi.js'
import DeskPanel from './DeskPanel.jsx'
import AdminPanel from './AdminPanel.jsx'
import FaqPanel from './FaqPanel.jsx'

export default function DeskWorkspace({token}) {
 const [spaces,setSpaces]=useState(null),[mode,setMode]=useState('portal'),[error,setError]=useState('')
 useEffect(()=>{let live=true;deskRequest(token,'/desk/espacios').then(s=>{if(live){setSpaces(s);setMode(s.consola?'consola':'portal')}}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[token])
 return <section aria-label="Espacios Service Desk"><div className="card"><h2>Service Desk</h2><p>Solicitudes, atención y configuración en espacios separados.</p>
  {error&&<p role="alert">{error}</p>}
  {spaces&&<nav className="dashboard-nav" aria-label="Espacios de trabajo">{[['portal','Portal del solicitante'],['consola','Consola del agente'],['administracion','Administración']].filter(([key])=>spaces[key]).map(([key,title])=><button key={key} aria-pressed={mode===key} className={mode===key?'active-tab':''} onClick={()=>setMode(key)}>{title}</button>)}</nav>}
 </div>{spaces&&<><DeskPanel key={mode} token={token} mode={mode}/>
 {mode==='administracion'&&spaces.administrador&&<><AdminPanel token={token}/><FaqPanel token={token} administration/></>}</>}
 </section>
}
