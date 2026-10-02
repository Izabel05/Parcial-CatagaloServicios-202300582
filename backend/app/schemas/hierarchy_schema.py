from datetime import datetime
from pydantic import BaseModel, Field

from backend.app.schemas.admin_schema import Role


class EmpresaCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=40)
    nombre: str = Field(min_length=1, max_length=200)
    activo: bool = True


class EmpresaUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=40)
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    activo: bool | None = None


class EmpresaResponse(EmpresaCreate):
    id: int
    created_at: datetime


class AreaCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=40)
    nombre: str = Field(min_length=1, max_length=200)
    empresa_id: int = Field(gt=0)
    activo: bool = True


class AreaUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=40)
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    empresa_id: int | None = Field(default=None, gt=0)
    activo: bool | None = None


class AreaResponse(AreaCreate):
    id: int
    created_at: datetime


class DepartamentoCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=40)
    nombre: str = Field(min_length=1, max_length=200)
    area_id: int = Field(gt=0)
    activo: bool = True


class DepartamentoUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=40)
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    area_id: int | None = Field(default=None, gt=0)
    activo: bool | None = None


class DepartamentoResponse(DepartamentoCreate):
    id: int
    created_at: datetime


class SeccionCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=40)
    nombre: str = Field(min_length=1, max_length=200)
    departamento_id: int = Field(gt=0)
    activo: bool = True


class SeccionUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=40)
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    departamento_id: int | None = Field(default=None, gt=0)
    activo: bool | None = None


class SeccionResponse(SeccionCreate):
    id: int
    created_at: datetime


class PuestoCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=40)
    nombre: str = Field(min_length=1, max_length=200)
    seccion_id: int = Field(gt=0)
    activo: bool = True


class PuestoUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=40)
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    seccion_id: int | None = Field(default=None, gt=0)
    activo: bool | None = None


class PuestoResponse(PuestoCreate):
    id: int
    created_at: datetime


class UsuarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    username: str = Field(min_length=3, max_length=80)
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=10, max_length=256)
    role: Role = "consulta"
    puesto_id: int = Field(gt=0)
    is_active: bool = True


class UsuarioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    username: str | None = Field(default=None, min_length=3, max_length=80)
    email: str | None = Field(default=None, min_length=5, max_length=320)
    password: str | None = Field(default=None, min_length=10, max_length=256)
    role: Role | None = None
    puesto_id: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class UsuarioResponse(BaseModel):
    id: int
    name: str
    username: str
    email: str
    role: Role
    is_active: bool
    puesto_id: int
    created_at: datetime
