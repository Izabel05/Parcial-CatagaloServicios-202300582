from backend.app.models.user import AuthenticatedContext
from backend.app.services.directory_service import DirectoryService


class DirectoryController:
    def __init__(self, service: DirectoryService) -> None:
        self._service = service

    def list_entity(self, entity: str, parent_id: int | None = None):
        return self._service.list_entity(entity, parent_id)

    def get_entity(self, entity: str, entity_id: int):
        return self._service.get_entity(entity, entity_id)

    def create_entity(self, entity: str, values: dict):
        return self._service.create_entity(entity, values)

    def update_entity(self, entity: str, entity_id: int, values: dict):
        return self._service.update_entity(entity, entity_id, values)

    def delete_entity(self, entity: str, entity_id: int):
        return self._service.delete_entity(entity, entity_id)

    def list_users(self):
        return self._service.list_users()

    def get_user(self, user_id: int):
        return self._service.get_user(user_id)

    def create_user(self, values: dict):
        return self._service.create_user(values)

    def update_user(self, actor: AuthenticatedContext, user_id: int, values: dict):
        return self._service.update_user(actor, user_id, values)

    def delete_user(self, actor: AuthenticatedContext, user_id: int):
        return self._service.delete_user(actor, user_id)
