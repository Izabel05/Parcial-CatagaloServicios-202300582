from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Service:
    id: int
    code: str
    level_1_code: str
    level_1_name: str
    original_code: str
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
    transformations: dict[str, Any] | None = None
    responsible_section_id: int | None = None
    responsible_section_code: str | None = None
    responsible_user_id: int | None = None
    responsible_user_name: str | None = None
