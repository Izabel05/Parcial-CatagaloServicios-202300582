from backend.app.models.service import Service
from backend.app.repositories.service_repository import ServiceRepository


class ServiceService:
    def __init__(self, repository: ServiceRepository | None = None) -> None:
        self.repository = repository or ServiceRepository()

    def list_services(self) -> list[Service]:
        return self.repository.list_all()
