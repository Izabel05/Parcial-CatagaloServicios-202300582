from typing import Literal
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Request, HTTPException, Response
from backend.app.controllers.desk_controller import DeskController
from backend.app.models.user import AuthenticatedContext
from backend.app.security.dependencies import require_authentication
from backend.app.schemas.desk_schema import (
    QueuePayload, PermissionsPayload, RolesPayload, TicketPayload, TicketEditPayload,
    AssignmentPayload, TransferPayload, StatePayload, CommentPayload, LinkPayload, ApprovalPayload, Process)
from backend.app.services.desk_service import MAX_ATTACHMENT, PROCESSES, PERMISSIONS, TYPE_MAP

router=APIRouter(prefix='/desk',tags=['Service Desk'])


def controller(): return DeskController()


@router.get('/me')
def me(a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('me',a.user.id)


@router.get('/opciones')
def options(_:AuthenticatedContext=Depends(require_authentication)):
    return {'procesos':PROCESSES,'permisos':PERMISSIONS,'tipos_por_proceso':TYPE_MAP,
            'estados':['abierto','en_atencion','resuelto','cerrado'],'adjunto_max_bytes':MAX_ATTACHMENT}


@router.put('/usuarios/{user_id}/roles')
def roles(user_id:int,p:RolesPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('roles',a.user.id,user_id,p.roles)


@router.get('/usuarios/{user_id}/roles')
def user_roles(user_id:int,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('user_roles',a.user.id,user_id)


@router.get('/colas')
def queues(a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('queues',a.user.id)


@router.post('/colas',status_code=201)
def create_queue(p:QueuePayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('queue',a.user.id,p.model_dump())


@router.get('/colas/{queue_id}/historial')
def queue_history(queue_id:int,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('queue_history',a.user.id,queue_id)


@router.put('/colas/{queue_id}')
def update_queue(queue_id:int,p:QueuePayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('queue',a.user.id,p.model_dump(),queue_id)


@router.delete('/colas/{queue_id}')
def deactivate_queue(queue_id:int,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('deactivate_queue',a.user.id,queue_id)


@router.put('/colas/{queue_id}/permisos')
def permissions(queue_id:int,p:PermissionsPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('permissions',a.user.id,queue_id,[x.model_dump() for x in p.permisos])


@router.get('/tickets')
def tickets(search:str=Query('',max_length=200),cola_id:int|None=Query(None,gt=0),servicio_id:int|None=Query(None,gt=0),
            estado:str|None=None,prioridad:int|None=Query(None,ge=1,le=4),responsable_id:int|None=Query(None,gt=0),
            ambito:Literal['visibles','propios','colas']='visibles',proceso:Process|None=None,desde:datetime|None=None,hasta:datetime|None=None,
            page:int=Query(1,ge=1,le=1000000),page_size:int=Query(25,ge=1,le=100),
            a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    if desde and desde.tzinfo is None: desde=desde.replace(tzinfo=timezone.utc)
    if hasta and hasta.tzinfo is None: hasta=hasta.replace(tzinfo=timezone.utc)
    if desde and hasta and desde>hasta: raise HTTPException(422,'Rango de fechas inválido')
    return c.run('list_tickets',a.user.id,dict(search=search,cola_id=cola_id,servicio_id=servicio_id,
        estado=estado,prioridad=prioridad,responsable_id=responsable_id,ambito=ambito,proceso=proceso,desde=desde,hasta=hasta),page,page_size)


@router.post('/tickets',status_code=201)
def create_ticket(p:TicketPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('create',a.user.id,p.model_dump())


@router.get('/tickets/{ticket_id}')
def detail(ticket_id:int,ambito:Literal['visibles','propios','colas']='visibles',a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('detail',a.user.id,ticket_id,ambito)


@router.put('/tickets/{ticket_id}')
def edit(ticket_id:int,p:TicketEditPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('edit',a.user.id,ticket_id,p.model_dump())


@router.post('/tickets/{ticket_id}/tomar')
def claim(ticket_id:int,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('assign',a.user.id,ticket_id)


@router.post('/tickets/{ticket_id}/asignar')
def assign(ticket_id:int,p:AssignmentPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('assign',a.user.id,ticket_id,p.usuario_id,p.motivo)


@router.post('/tickets/{ticket_id}/transferir')
def transfer(ticket_id:int,p:TransferPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('transfer',a.user.id,ticket_id,p.cola_id,p.motivo)


@router.post('/tickets/{ticket_id}/escalar')
def escalate(ticket_id:int,p:TransferPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('transfer',a.user.id,ticket_id,p.cola_id,p.motivo,True)


@router.post('/tickets/{ticket_id}/estado')
def state(ticket_id:int,p:StatePayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('state',a.user.id,ticket_id,p.estado,p.motivo,p.resolucion)


@router.post('/tickets/{ticket_id}/comentarios',status_code=201)
def comment(ticket_id:int,p:CommentPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('comment',a.user.id,ticket_id,p.texto,p.interno)


@router.post('/tickets/{ticket_id}/vinculos',status_code=201)
def link(ticket_id:int,p:LinkPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('link',a.user.id,ticket_id,p.ticket_id,p.tipo)


@router.post('/tickets/{ticket_id}/aprobaciones',status_code=201)
def approval(ticket_id:int,p:ApprovalPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('approval',a.user.id,ticket_id,p.aprobado,p.motivo)


@router.post('/tickets/{ticket_id}/adjuntos',status_code=201)
async def upload(ticket_id:int,request:Request,nombre:str=Query(min_length=1,max_length=150),interno:bool=False,
                 a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    c.run('detail',a.user.id,ticket_id)
    data=bytearray()
    async for chunk in request.stream():
        if len(data)+len(chunk)>MAX_ATTACHMENT: raise HTTPException(413,'Máximo 5 MiB por adjunto')
        data.extend(chunk)
    mime=request.headers.get('content-type','').split(';')[0].strip().lower()
    return c.run('upload',a.user.id,ticket_id,nombre,mime,bytes(data),interno)


@router.get('/adjuntos/{attachment_id}')
def download(attachment_id:int,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    data=c.run('download',a.user.id,attachment_id)
    return Response(bytes(data['contenido']),media_type=data['mime'],headers={
        'Content-Disposition':"attachment; filename*=UTF-8''"+quote(data['nombre'],safe=''),
        'X-Content-Type-Options':'nosniff','Cache-Control':'no-store'})
