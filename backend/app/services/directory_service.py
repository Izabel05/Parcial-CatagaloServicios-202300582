from __future__ import annotations

from typing import Any

from psycopg.errors import UniqueViolation

from backend.app.models.user import AuthenticatedContext
from backend.app.repositories.hierarchy_repository import (
    DEFINITIONS,
    HierarchyDependencyError,
    HierarchyNotFoundError,
    HierarchyRepository,
)
from backend.app.services.admin_service import AdminOperationError, AdminService


class DirectoryOperationError(Exception):
    """Error de negocio del directorio organizacional."""


class DirectoryNotFoundError(DirectoryOperationError):
    """Entidad solicitada inexistente."""


class DirectoryService:
    def __init__(
        self,
        hierarchy_repository: HierarchyRepository | None = None,
        admin_service: AdminService | None = None,
    ) -> None:
        self._hierarchy = hierarchy_repository or HierarchyRepository()
        self._admin = admin_service or AdminService(hierarchy_repository=self._hierarchy)

    def list_entity(self, entity: str, parent_id: int | None = None) -> list[dict[str, Any]]:
        return self._hierarchy.list(self._definition(entity), parent_id)

    def get_entity(self, entity: str, entity_id: int) -> dict[str, Any]:
        result = self._hierarchy.get(self._definition(entity), entity_id)
        if result is None:
            raise DirectoryNotFoundError("Registro no encontrado")
        return result

    def create_entity(self, entity: str, values: dict[str, Any]) -> dict[str, Any]:
        definition = self._definition(entity)
        try:
            return self._hierarchy.create(
                definition,
                values["codigo"].strip(),
                values["nombre"].strip(),
                values.get(definition.parent_column) if definition.parent_column else None,
                values.get("activo", True),
            )
        except (HierarchyDependencyError, UniqueViolation) as error:
            raise DirectoryOperationError(str(error) or "El código ya existe o el padre no es válido") from error

    def update_entity(self, entity: str, entity_id: int, values: dict[str, Any]) -> dict[str, Any]:
        clean_values = dict(values)
        for field in ("codigo", "nombre"):
            if clean_values.get(field) is not None:
                clean_values[field] = clean_values[field].strip()
        try:
            return self._hierarchy.update(self._definition(entity), entity_id, clean_values)
        except HierarchyNotFoundError as error:
            raise DirectoryNotFoundError(str(error)) from error
        except (HierarchyDependencyError, UniqueViolation) as error:
            raise DirectoryOperationError(str(error) or "La modificación no es válida") from error

    def delete_entity(self, entity: str, entity_id: int) -> dict[str, Any]:
        try:
            return self._hierarchy.update(self._definition(entity), entity_id, {"activo": False})
        except HierarchyNotFoundError as error:
            raise DirectoryNotFoundError(str(error)) from error
        except HierarchyDependencyError as error:
            raise DirectoryOperationError(str(error)) from error

    def list_users(self) -> list[dict[str, Any]]:
        return self._admin.list_users()

    def get_user(self, user_id: int) -> dict[str, Any]:
        result = self._admin.get_user(user_id)
        if result is None:
            raise DirectoryNotFoundError("Usuario no encontrado")
        return result

    def create_user(self, values: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._admin.create_user(values)
        except AdminOperationError as error:
            raise DirectoryOperationError(str(error)) from error

    def update_user(self, actor: AuthenticatedContext, user_id: int, values: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._admin.update_user(actor, user_id, values)
        except AdminOperationError as error:
            raise DirectoryOperationError(str(error)) from error

    def delete_user(self, actor: AuthenticatedContext, user_id: int) -> dict[str, Any]:
        try:
            return self._admin.set_user_status(actor, user_id, False)
        except AdminOperationError as error:
            raise DirectoryOperationError(str(error)) from error

    @staticmethod
    def _definition(entity: str):
        try:
            return DEFINITIONS[entity]
        except KeyError as error:
            raise DirectoryOperationError("Entidad de jerarquía no soportada") from error
