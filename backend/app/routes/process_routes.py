from fastapi import APIRouter, Depends
from backend.app.controllers.desk_controller import DeskController
from backend.app.models.user import AuthenticatedContext
from backend.app.security.dependencies import require_authentication
from backend.app.schemas.process_schema import ProcessPatch, TransitionPayload, ConfirmationPayload, PublishServicePayload
from backend.app.services.process_service import ProcessService

router=APIRouter(prefix='/desk/tickets',tags=['Procesos Service Desk'])


def controller(): return DeskController(ProcessService())


@router.patch('/{ticket_id}/proceso/datos')
def patch(ticket_id:int,p:ProcessPatch,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('patch',a.user.id,ticket_id,p.datos,p.motivo)


@router.post('/{ticket_id}/proceso/transiciones')
def transition(ticket_id:int,p:TransitionPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('transition',a.user.id,ticket_id,p.estado,p.motivo)


@router.post('/{ticket_id}/proceso/incidente')
def event(ticket_id:int,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('event',a.user.id,ticket_id)


@router.post('/{ticket_id}/proceso/confirmacion')
def confirm(ticket_id:int,p:ConfirmationPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('confirm',a.user.id,ticket_id,p.texto)


@router.post('/{ticket_id}/proceso/servicio')
def publish(ticket_id:int,p:PublishServicePayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('publish',a.user.id,ticket_id,p.servicio_id,p.nuevo.model_dump() if p.nuevo else None,p.motivo)
