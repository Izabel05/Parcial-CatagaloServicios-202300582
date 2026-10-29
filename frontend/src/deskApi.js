const API=import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function deskRequest(token,path,method='GET',body,headers={}) {
  const raw=body instanceof File
  const response=await fetch(`${API}/api/v1${path}`,{method,headers:{Authorization:`Bearer ${token}`,
    ...(raw?{}:{'Content-Type':'application/json'}),...headers},
    ...(body===undefined?{}:{body:raw?body:JSON.stringify(body)})})
  if (!response.ok) {
    const data=await response.json().catch(()=>({}))
    throw new Error(Array.isArray(data.detail)?data.detail.map((e)=>e.msg).join('; '):data.detail||'Operación rechazada')
  }
  return response.json()
}

export async function downloadAttachment(token,file) {
  const response=await fetch(`${API}/api/v1/desk/adjuntos/${file.id}`,{headers:{Authorization:`Bearer ${token}`}})
  if(!response.ok) throw new Error('Descarga no autorizada o archivo no disponible')
  const url=URL.createObjectURL(await response.blob())
  const link=document.createElement('a'); link.href=url; link.download=file.nombre; link.click()
  setTimeout(()=>URL.revokeObjectURL(url),1000)
}
