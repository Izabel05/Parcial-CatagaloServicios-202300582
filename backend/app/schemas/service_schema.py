from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    original_code: str
    level_1_code: str
    level_1_name: str
    name: str
    active: bool | None = None
    service_class: str | None = None
    criticality: str | None = None
    service_type: str | None = None
    description: str | None = None
    metric: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    review_status: str = "OK"
    service_class_id: int | None = None
    service_class_name: str | None = None
    criticality_id: int | None = None
    criticality_name: str | None = None
    service_type_id: int | None = None
    service_type_name: str | None = None
    source_sheet: str | None = None
    source_row: int | None = None
    source_range: str | None = None
    transformations: dict | None = None
    responsible_section_id: int | None = None
    responsible_section_code: str | None = None
    responsible_user_id: int | None = None
    responsible_user_name: str | None = None


class ServicePageResponse(BaseModel):
    items: list[ServiceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ServiceCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    level_1_code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=300)
    active: bool = True
    service_class_id: int = Field(gt=0)
    criticality_id: int = Field(gt=0)
    service_type_id: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=2000)
    metric: str | None = Field(default=None, max_length=300)
    minimum: float | None = None
    maximum: float | None = None
    review_status: Literal["OK", "REVIEW"] = "OK"
    responsible_section_id: int = Field(gt=0)
    responsible_user_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_range(self):
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("mínimo debe ser menor o igual que máximo")
        return self


class ServiceUpdateRequest(BaseModel):
    level_1_code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=300)
    active: bool | None = None
    service_class_id: int | None = Field(default=None, gt=0)
    criticality_id: int | None = Field(default=None, gt=0)
    service_type_id: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=2000)
    metric: str | None = Field(default=None, max_length=300)
    minimum: float | None = None
    maximum: float | None = None
    review_status: Literal["OK", "REVIEW"] | None = None
    responsible_section_id: int | None = Field(default=None, gt=0)
    responsible_user_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_range(self):
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("mínimo debe ser menor o igual que máximo")
        return self


class Level1Response(BaseModel):
    code: str
    original_code: str
    name: str
    name_variants: list[str]
    active: bool
    review_status: str
    source_sheet: str
    source_row: int
    source_range: str
    transformations: dict


class Level1CreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=300)
    active: bool = True


class Level1UpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=300)
    active: bool | None = None


class CatalogOptionResponse(BaseModel):
    id: int
    code: str
    name: str
    active: bool


class CatalogOptionsResponse(BaseModel):
    service_classes: list[CatalogOptionResponse]
    criticalities: list[CatalogOptionResponse]
    service_types: list[CatalogOptionResponse]


class CatalogOptionCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=200)
    active: bool = True


class CatalogOptionUpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=60)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    active: bool | None = None
