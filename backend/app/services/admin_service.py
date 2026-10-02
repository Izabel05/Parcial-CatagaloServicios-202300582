from __future__ import annotations

import json
from typing import Any

from psycopg.errors import UniqueViolation

from backend.app.models.user import AuthenticatedContext
from backend.app.repositories.admin_repository import CatalogAdminRepository, OrganizationRepository, UserAdminRepository
from backend.app.repositories.hierarchy_repository import HierarchyDependencyError, HierarchyRepository
from backend.app.security.encryption import AesGcmCipher
from backend.app.security.passwords import PasswordService


class AdminOperationError(Exception):
    """Regla de administración o entidad no encontrada."""


class AdminService:
    def __init__(
        self,
        user_repository: UserAdminRepository | None = None,
        organization_repository: OrganizationRepository | None = None,
        catalog_repository: CatalogAdminRepository | None = None,
        hierarchy_repository: HierarchyRepository | None = None,
        password_service: PasswordService | None = None,
        profile_cipher: AesGcmCipher | None = None,
    ) -> None:
        from backend.app.config.settings import settings

        self._users = user_repository or UserAdminRepository()
        self._organizations = organization_repository or OrganizationRepository()
        self._catalog = catalog_repository or CatalogAdminRepository()
        self._hierarchy = hierarchy_repository or HierarchyRepository()
        self._passwords = password_service or PasswordService()
        self._cipher = profile_cipher or AesGcmCipher(settings.app_encryption_key)

    def list_users(self) -> list[dict[str, Any]]:
        return self._users.list_users()

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        return self._users.get_user(user_id)

    def create_user(self, values: dict[str, Any]) -> dict[str, Any]:
        role = values["role"]
        profile = {"display_name": values.get("name", ""), "phone": values.get("phone", "")}
        params = (
            values["name"].strip(), values["username"].strip(), values["username"].strip().casefold(),
            values["email"].strip(), values["email"].strip().casefold(), self._passwords.hash(values["password"]),
            self._cipher.encrypt_json(profile), role == "administrador", role, values["puesto_id"], values.get("is_active", True),
        )
        try:
            self._hierarchy.ensure_active_position(values["puesto_id"])
        except HierarchyDependencyError as error:
            raise AdminOperationError(str(error)) from error
        try:
            return self._users.create_user(params)
        except UniqueViolation as error:
            raise AdminOperationError("El usuario o correo ya existe") from error

    def set_user_status(self, actor: AuthenticatedContext, user_id: int, is_active: bool) -> dict[str, Any]:
        if actor.user.id == user_id and not is_active:
            raise AdminOperationError("No se puede desactivar la cuenta administradora actual")
        user = self._users.set_status(user_id, is_active)
        if user is None:
            raise AdminOperationError("Usuario no encontrado")
        return user

    def update_user(self, actor: AuthenticatedContext, user_id: int, values: dict[str, Any]) -> dict[str, Any]:
        if actor.user.id == user_id and values.get("is_active") is False:
            raise AdminOperationError("No se puede desactivar la cuenta administradora actual")
        if actor.user.id == user_id and values.get("role") not in (None, "administrador"):
            raise AdminOperationError("No se puede retirar el rol administrador de la sesión actual")
        if values.get("puesto_id") is not None:
            try:
                self._hierarchy.ensure_active_position(values["puesto_id"])
                assigned_sections = self._users.assigned_service_sections(user_id)
                target_section = self._hierarchy.active_position_section(values["puesto_id"])
            except HierarchyDependencyError as error:
                raise AdminOperationError(str(error)) from error
            if assigned_sections and assigned_sections != {target_section}:
                raise AdminOperationError("No se puede mover un usuario responsable a otra sección")
        if values.get("is_active") is True:
            current = self._users.get_user(user_id)
            if current is None:
                raise AdminOperationError("Usuario no encontrado")
            try:
                self._hierarchy.ensure_active_position(values.get("puesto_id", current["puesto_id"]))
            except HierarchyDependencyError as error:
                raise AdminOperationError(str(error)) from error
        password_hash = self._passwords.hash(values["password"]) if values.get("password") else None
        role = values.get("role")
        params = (
            values.get("name"), values.get("username"), values.get("username", "").strip().casefold() if values.get("username") else None,
            values.get("email"), values.get("email", "").strip().casefold() if values.get("email") else None,
            password_hash, role, role, values.get("puesto_id"), values.get("is_active"),
        )
        try:
            user = self._users.update_user(user_id, params)
        except UniqueViolation as error:
            raise AdminOperationError("El usuario o correo ya existe") from error
        if user is None:
            raise AdminOperationError("Usuario no encontrado")
        return user

    def set_user_role(self, actor: AuthenticatedContext, user_id: int, role: str) -> dict[str, Any]:
        if actor.user.id == user_id and role != "administrador":
            raise AdminOperationError("No se puede retirar el rol administrador de la sesión actual")
        user = self._users.set_role(user_id, role)
        if user is None:
            raise AdminOperationError("Usuario no encontrado")
        return user

    def list_organizations(self) -> list[dict[str, Any]]:
        return self._organizations.list_all()

    def create_organization(self, values: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._organizations.create((values["code"].strip(), values["name"].strip(), values.get("description"), values.get("active", True)))
        except UniqueViolation as error:
            raise AdminOperationError("El código de organización ya existe") from error

    def update_organization(self, organization_id: int, values: dict[str, Any]) -> dict[str, Any]:
        organization = self._organizations.update(organization_id, (values.get("name"), values.get("description"), values.get("active")))
        if organization is None:
            raise AdminOperationError("Organización no encontrada")
        return organization

    def update_catalog_service(self, code: str, values: dict[str, Any], actor: AuthenticatedContext) -> dict[str, Any]:
        changes = {
            "manual_override": True,
            "updated_by": actor.user.username,
            "fields": sorted(key for key, value in values.items() if value is not None),
        }
        service = self._catalog.update_service(
            code,
            (
                values.get("name"), values.get("active"), values.get("description"), values.get("metric"),
                values.get("minimum"), values.get("maximum"), values.get("review_status"),
                json.dumps(changes),
            ),
        )
        if service is None:
            raise AdminOperationError("Servicio no encontrado")
        return service
