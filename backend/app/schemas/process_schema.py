from datetime import datetime
from typing import Literal
from pydantic import Field
from backend.app.schemas.desk_schema import Payload
from backend.app.schemas.service_schema import ServiceCreateRequest

Text = str | None


class NewServiceData(Payload):
    necesidad: Text = Field(None,max_length=4000)
    analisis_viabilidad: Text = Field(None,max_length=4000)
    viable: bool | None = None
    plan_implementacion: Text = Field(None,max_length=4000)
    evidencia_implementacion: Text = Field(None,max_length=4000)
    validacion: Text = Field(None,max_length=4000)


class ChangeData(Payload):
    evaluacion_impacto: Text = Field(None,max_length=4000)
    riesgo: Literal['bajo','medio','alto'] | None = None
    plan_pruebas: Text = Field(None,max_length=4000)
    plan_reversion: Text = Field(None,max_length=4000)
    programado_para: datetime | None = None
    resultado_ejecucion: Text = Field(None,max_length=4000)
    resultado_pruebas: Text = Field(None,max_length=4000)
    validacion: Text = Field(None,max_length=4000)


class IncidentData(Payload):
    categoria: Literal['I0','I1','I2','I3','I4','I5','I6'] | None = None
    interrupcion: bool | None = None
    degradacion: bool = False
    seguridad: bool = False
    duracion_estimada_horas: float | None = Field(None,ge=0,le=1000000,allow_inf_nan=False)
    duracion_real_horas: float | None = Field(None,ge=0,le=1000000,allow_inf_nan=False)
    redundancia_disponible: bool | None = None
    justificacion_categoria: Text = Field(None,max_length=4000)
    diagnostico: Text = Field(None,max_length=4000)
    solucion: Text = Field(None,max_length=4000)
    evidencia_recuperacion: Text = Field(None,max_length=4000)


class EventData(Payload):
    categoria: Literal['E0','E1','E2','E3'] | None = None
    evaluacion: Text = Field(None,max_length=4000)
    cola_incidente_id: int | None = Field(None,gt=0)
    incidente_id: int | None = Field(None,gt=0)


class ProblemData(Payload):
    incidentes_ids: list[int] = Field(default_factory=list,max_length=100)
    causa_raiz: Text = Field(None,max_length=4000)
    solucion_temporal: Text = Field(None,max_length=4000)
    error_conocido: bool = False
    solucion_definitiva: Text = Field(None,max_length=4000)
    cambio_correctivo_id: int | None = Field(None,gt=0)


class AccessData(Payload):
    beneficiario_id: int | None = Field(None,gt=0)
    recurso: Text = Field(None,max_length=4000)
    permiso_solicitado: Text = Field(None,max_length=4000)
    accion: Literal['provisionar','revocar'] = 'provisionar'
    validacion_solicitud: Text = Field(None,max_length=4000)
    evidencia_provision: Text = Field(None,max_length=4000)
    validacion: Text = Field(None,max_length=4000)


class TechnologyServiceData(Payload):
    detalle_solicitud: Text = Field(None,max_length=4000)
    validacion: Text = Field(None,max_length=4000)
    evidencia_cumplimiento: Text = Field(None,max_length=4000)
    confirmacion: Text = Field(None,max_length=4000)


SCHEMAS={'nuevos_servicios':NewServiceData,'cambios':ChangeData,'incidentes':IncidentData,
         'eventos':EventData,'problemas':ProblemData,'accesos':AccessData,'servicios_tecnologia':TechnologyServiceData}


class ProcessPatch(Payload):
    datos: dict
    motivo: str = Field(min_length=1,max_length=2000)


class TransitionPayload(Payload):
    estado: str = Field(min_length=1,max_length=80)
    motivo: str = Field(min_length=1,max_length=2000)


class ConfirmationPayload(Payload):
    texto: str = Field(min_length=1,max_length=4000)


class PublishServicePayload(Payload):
    servicio_id: int | None = Field(None,gt=0)
    nuevo: ServiceCreateRequest | None = None
    motivo: str = Field(min_length=1,max_length=2000)
