from backend.app.models.user import AuthenticatedContext
from backend.app.services.admin_service import AdminService


class AdminController:
    def __init__(self, service: AdminService) -> None:
        self._service = service

    def list_users(self):
        return self._service.list_users()

    def create_user(self, values):
        return self._service.create_user(values)

    def set_user_status(self, actor: AuthenticatedContext, user_id: int, is_active: bool):
        return self._service.set_user_status(actor, user_id, is_active)

    def set_user_role(self, actor: AuthenticatedContext, user_id: int, role: str):
        return self._service.set_user_role(actor, user_id, role)

    def list_organizations(self):
        return self._service.list_organizations()

    def create_organization(self, values):
        return self._service.create_organization(values)

    def update_organization(self, organization_id: int, values):
        return self._service.update_organization(organization_id, values)

    def update_catalog_service(self, code: str, values, actor: AuthenticatedContext):
        return self._service.update_catalog_service(code, values, actor)
