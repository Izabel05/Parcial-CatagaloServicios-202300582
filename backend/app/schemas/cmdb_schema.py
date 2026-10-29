from datetime import date
from typing import Literal
from ipaddress import ip_address

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictPayload(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class CatalogPayload(StrictPayload):
    codigo: str = Field(min_length=1, max_length=80)
    nombre: str = Field(min_length=1, max_length=200)
    padre_id: int | None = Field(default=None, gt=0)
    activo: bool = True


class CIPayload(StrictPayload):
    codigo: str = Field(min_length=1, max_length=80)
    nombre: str = Field(min_length=1, max_length=200)
    clasificacion_id: int = Field(gt=0)
    ubicacion_id: int | None = Field(default=None, gt=0)
    responsable_usuario_id: int | None = Field(default=None, gt=0)
    estado: str = Field(default='Activo', min_length=1, max_length=80)
    activo: bool = True
    es_dispositivo: bool = True
    etiqueta: str | None = Field(default=None, min_length=1, max_length=80)
    descripcion: str | None = Field(default=None, max_length=4000)
    numero_serie: str | None = Field(default=None, max_length=200)
    version: str | None = Field(default=None, max_length=100)
    fecha_adquisicion: date | None = None
    fecha_vencimiento: date | None = None
    ubicacion_original: str | None = Field(default=None, max_length=300)
    responsable_original: str | None = Field(default=None, max_length=300)
    nivel_seguridad: str | None = Field(default=None, max_length=80)
    cumplimiento: str | None = Field(default=None, max_length=80)
    estado_configuracion: str | None = Field(default=None, max_length=80)
    numero_licencia: str | None = Field(default=None, max_length=200)
    relaciones_originales: str | None = Field(default=None, max_length=4000)
    padres_hijos_originales: str | None = Field(default=None, max_length=4000)
    fecha_cambio_original: date | None = None
    descripcion_cambio_original: str | None = Field(default=None, max_length=4000)
    documentacion_relacionada: str | None = Field(default=None, max_length=4000)
    enlaces_incidentes_problemas: str | None = Field(default=None, max_length=4000)
    atributos_tecnicos: dict = Field(default_factory=dict)

    @field_validator('atributos_tecnicos')
    @classmethod
    def technical_attributes(cls, value):
        allowed = {'memoria_gb', 'almacenamiento_gb', 'ip', 'sistema_operativo'}
        if set(value) - allowed:
            raise ValueError('Atributo técnico no definido por el proyecto')
        for key in ('memoria_gb', 'almacenamiento_gb'):
            if key in value and (type(value[key]) is not int or not 1 <= value[key] <= 1000000):
                raise ValueError(f'{key} debe ser un entero positivo')
        if 'ip' in value:
            if not isinstance(value['ip'], str):
                raise ValueError('IP debe ser texto y es opcional')
            ip_address(value['ip'])
        if 'sistema_operativo' in value and (not isinstance(value['sistema_operativo'], str) or not 1 <= len(value['sistema_operativo']) <= 100):
            raise ValueError('Sistema operativo inválido')
        return value


class RelationPayload(StrictPayload):
    origen_ci_id: int = Field(gt=0)
    destino_ci_id: int = Field(gt=0)
    tipo: Literal['depende_de', 'alojado_en', 'componente_de', 'conectado_a']
    justificacion: str = Field(min_length=1, max_length=2000)


class ServiceLinkPayload(StrictPayload):
    servicio_id: int = Field(gt=0)
