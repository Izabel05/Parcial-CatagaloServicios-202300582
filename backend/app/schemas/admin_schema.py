from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["administrador", "consulta"]


class AdminUserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: str
    role: Role
    is_active: bool
    puesto_id: int
    created_at: datetime


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    username: str = Field(min_length=3, max_length=80)
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=10, max_length=256)
    role: Role = "consulta"
    puesto_id: int = Field(gt=0)
    display_name: str = Field(default="", max_length=160)
    phone: str = Field(default="", max_length=40)


class UserStatusRequest(BaseModel):
    is_active: bool


class UserRoleRequest(BaseModel):
    role: Role


class UpdateUserRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    username: str | None = Field(default=None, min_length=3, max_length=80)
    email: str | None = Field(default=None, min_length=5, max_length=320)
    password: str | None = Field(default=None, min_length=10, max_length=256)
    role: Role | None = None
    puesto_id: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class OrganizationResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    active: bool
    created_at: datetime


class OrganizationRequest(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=500)
    active: bool = True


class OrganizationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=500)
    active: bool | None = None


class CatalogServiceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    active: bool | None = None
    description: str | None = Field(default=None, max_length=2000)
    metric: str | None = Field(default=None, max_length=300)
    minimum: float | None = None
    maximum: float | None = None
    review_status: Literal["OK", "REVIEW"] | None = None
