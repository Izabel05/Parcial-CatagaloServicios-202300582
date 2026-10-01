from pydantic import BaseModel, ConfigDict


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    level_1_code: str
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
