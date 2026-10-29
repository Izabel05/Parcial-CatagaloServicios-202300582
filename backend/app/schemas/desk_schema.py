from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Process = Literal['nuevos_servicios','cambios','incidentes','eventos','problemas','accesos','servicios_tecnologia']
Permission = Literal['consultar','atender','transferir','aprobar','administrar']
Role = Literal['administrador','consulta','solicitante','agente','aprobador']


class Payload(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Grant(Payload):
    rol: Role | None = None
    usuario_id: int | None = Field(None, gt=0)
    permiso: Permission

    @model_validator(mode='after')
    def subject(self):
        if (self.rol is None) == (self.usuario_id is None):
            raise ValueError('Indique exactamente un rol o un usuario')
        return self


class QueuePayload(Payload):
    codigo: str = Field(min_length=1, max_length=80)
    nombre: str = Field(min_length=1, max_length=200)
    descripcion: str = Field('', max_length=4000)
    proceso: Process
    activo: bool = True
    nivel_soporte: int = Field(1, ge=0, le=4)
    ordenamiento: Literal['prioridad_antiguedad'] = 'prioridad_antiguedad'
    objetivo_primera_atencion_min: int | None = Field(None, gt=0)
    objetivo_resolucion_min: int | None = Field(None, gt=0)
    responsables_ids: list[int] = Field(default_factory=list, max_length=100)


class PermissionsPayload(Payload):
    permisos: list[Grant] = Field(max_length=200)


class RolesPayload(Payload):
    roles: list[Literal['solicitante','agente','aprobador']] = Field(max_length=3)


class TicketPayload(Payload):
    titulo: str = Field(min_length=1, max_length=200)
    descripcion: str = Field(min_length=1, max_length=10000)
    solicitante_id: int | None = Field(None, gt=0)
    servicio_id: int = Field(gt=0)
    cola_id: int = Field(gt=0)
    prioridad: int = Field(3, ge=1, le=4)
    impacto: Literal['bajo','medio','alto'] = 'medio'
    urgencia: Literal['baja','media','alta'] = 'media'
    canal: Literal['portal','telefono','correo','presencial','otro'] = 'portal'
    ci_ids: list[int] = Field(default_factory=list, max_length=100)
    motivo_sin_ci: str | None = Field(None, min_length=1, max_length=1000)

    @model_validator(mode='after')
    def ci_reason(self):
        if not self.ci_ids and not self.motivo_sin_ci:
            raise ValueError('Asocie CI o justifique por qué no aplica')
        return self


class CommentPayload(Payload):
    texto: str = Field(min_length=1, max_length=10000)
    interno: bool = False


class TicketEditPayload(Payload):
    titulo: str = Field(min_length=1,max_length=200)
    descripcion: str = Field(min_length=1,max_length=10000)
    servicio_id: int = Field(gt=0)
    prioridad: int = Field(3,ge=1,le=4)
    impacto: Literal['bajo','medio','alto'] = 'medio'
    urgencia: Literal['baja','media','alta'] = 'media'
    canal: Literal['portal','telefono','correo','presencial','otro'] = 'portal'
    ci_ids: list[int] = Field(default_factory=list,max_length=100)
    motivo_sin_ci: str | None = Field(None,min_length=1,max_length=1000)
    motivo: str = Field(min_length=1,max_length=2000)

    @model_validator(mode='after')
    def ci_reason(self):
        if not self.ci_ids and not self.motivo_sin_ci:
            raise ValueError('Asocie CI o justifique por qué no aplica')
        return self


class AssignmentPayload(Payload):
    usuario_id: int = Field(gt=0)
    motivo: str = Field(min_length=1, max_length=2000)


class TransferPayload(Payload):
    cola_id: int = Field(gt=0)
    motivo: str = Field(min_length=1, max_length=2000)


class StatePayload(Payload):
    estado: Literal['en_atencion','resuelto','cerrado','abierto']
    motivo: str = Field(min_length=1, max_length=2000)
    resolucion: str | None = Field(None, min_length=1, max_length=10000)


class LinkPayload(Payload):
    ticket_id: int = Field(gt=0)
    tipo: Literal['relacionado','duplicado','incidente_problema','problema_cambio'] = 'relacionado'


class ApprovalPayload(Payload):
    aprobado: bool
    motivo: str = Field(min_length=1, max_length=2000)
