from typing import Literal
from fastapi import APIRouter, Depends, Query
from pydantic import Field
from backend.app.schemas.desk_schema import Payload, Process
from backend.app.models.user import AuthenticatedContext
from backend.app.security.dependencies import require_authentication
from backend.app.controllers.desk_controller import DeskController
from backend.app.services.experience_service import ExperienceService

router=APIRouter(prefix='/desk',tags=['Pantallas y autoservicio'])


class FaqPayload(Payload):
    titulo:str=Field(min_length=1,max_length=200)
    pregunta:str=Field(min_length=1,max_length=500)
    respuesta:str=Field(min_length=1,max_length=8000)
    servicio_id:int|None=Field(None,gt=0)
    publicado:bool=False


def controller(): return DeskController(ExperienceService())


@router.get('/espacios')
def spaces(a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('spaces',a.user.id)


@router.get('/tablero')
def dashboard(ambito:Literal['propios','colas']='propios',cola_id:int|None=Query(None,gt=0),proceso:Process|None=None,
              page:int=Query(1,ge=1,le=1000000),page_size:int=Query(25,ge=1,le=100),
              a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('dashboard',a.user.id,ambito,cola_id,proceso,page,page_size)


@router.get('/faq')
def faqs(search:str=Query('',max_length=200),administracion:bool=False,
         a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('faqs',a.user.id,search,administracion)


@router.post('/faq',status_code=201)
def create_faq(p:FaqPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('faq',a.user.id,p.model_dump())


@router.put('/faq/{faq_id}')
def edit_faq(faq_id:int,p:FaqPayload,a:AuthenticatedContext=Depends(require_authentication),c=Depends(controller)):
    return c.run('faq',a.user.id,p.model_dump(),faq_id)
