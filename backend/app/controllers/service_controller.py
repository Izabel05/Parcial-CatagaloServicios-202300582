from backend.app.schemas.service_schema import ServiceResponse
from backend.app.services.service_service import ServiceService


class ServiceController:
    def __init__(self, service: ServiceService | None = None) -> None:
        self.service = service or ServiceService()

    def list_services(self) -> list[ServiceResponse]:
        return [ServiceResponse.model_validate(item, from_attributes=True) for item in self.service.list_services()]
