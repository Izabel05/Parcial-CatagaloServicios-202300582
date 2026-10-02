from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.models.service import Service
from backend.app.repositories.service_repository import ServiceRepository


class ServiceOperationError(Exception):
    """Regla de negocio o referencia inválida del catálogo."""


class ServiceNotFoundError(ServiceOperationError):
    """Servicio o nivel 1 no encontrado."""


@dataclass(frozen=True, slots=True)
class ServicePage:
    items: list[Service]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        return max(1, (self.total + self.page_size - 1) // self.page_size)


class ServiceService:
    def __init__(self, repository: ServiceRepository | None = None) -> None:
        self.repository = repository or ServiceRepository()

    def list_services(
        self, search: str | None = None, level_1_code: str | None = None, active: bool | None = None,
        service_class_id: int | None = None, criticality_id: int | None = None, service_type_id: int | None = None,
        page: int = 1, page_size: int = 20,
    ) -> ServicePage:
        if page < 1 or page_size < 1 or page_size > 100:
            raise ServiceOperationError("La paginación debe usar page >= 1 y page_size entre 1 y 100")
        items, total = self.repository.list_page(
            search, level_1_code, active, service_class_id, criticality_id, service_type_id, page, page_size,
        )
        return ServicePage(items, total, page, page_size)

    def get_service(self, code: str) -> Service:
        result = self.repository.get_by_code(code)
        if result is None:
            raise ServiceNotFoundError("Servicio no encontrado")
        return result

    def create_service(self, values: dict[str, Any]) -> Service:
        clean = self._clean(values)
        self._validate_common(clean, current=None)
        try:
            return self.repository.create(clean)
        except UniqueViolation as error:
            raise ServiceOperationError("El código del servicio ya existe") from error

    def update_service(self, code: str, values: dict[str, Any]) -> Service:
        current = self.get_service(code)
        clean = self._clean(values)
        self._validate_common(clean, current=current)
        try:
            result = self.repository.update(code, clean)
        except UniqueViolation as error:
            raise ServiceOperationError("El código o la referencia del servicio ya existe") from error
        if result is None:
            raise ServiceNotFoundError("Servicio no encontrado")
        return result

    def deactivate_service(self, code: str) -> Service:
        return self.update_service(code, {"active": False})

    def list_level_1(self) -> list[dict[str, Any]]:
        return self.repository.list_level_1()

    def get_level_1(self, code: str) -> dict[str, Any]:
        result = self.repository.get_level_1(code)
        if result is None:
            raise ServiceNotFoundError("Servicio de nivel 1 no encontrado")
        return result

    def create_level_1(self, values: dict[str, Any]) -> dict[str, Any]:
        try:
            return self.repository.create_level_1(self._clean(values))
        except UniqueViolation as error:
            raise ServiceOperationError("El código del nivel 1 ya existe") from error

    def update_level_1(self, code: str, values: dict[str, Any]) -> dict[str, Any]:
        self.get_level_1(code)
        if values.get("active") is False and not self.repository.can_deactivate_level_1(code):
            raise ServiceOperationError("No se puede desactivar un nivel 1 con servicios activos")
        try:
            result = self.repository.update_level_1(code, self._clean(values))
        except (UniqueViolation, ForeignKeyViolation) as error:
            raise ServiceOperationError("El código del nivel 1 ya existe o tiene servicios asociados") from error
        return result or self.get_level_1(code)

    def list_catalog_options(self) -> dict[str, list[dict[str, Any]]]:
        return self.repository.list_catalog_options()

    def list_catalog(self, catalog: str, include_inactive: bool = False) -> list[dict[str, Any]]:
        try:
            return self.repository.list_catalog(catalog, include_inactive)
        except ValueError as error:
            raise ServiceOperationError(str(error)) from error

    def create_catalog_option(self, catalog: str, values: dict[str, Any]) -> dict[str, Any]:
        try:
            return self.repository.create_catalog_option(catalog, self._clean(values))
        except UniqueViolation as error:
            raise ServiceOperationError("El código o nombre del catálogo ya existe") from error

    def update_catalog_option(self, catalog: str, option_id: int, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("active") is False and self.repository.catalog_option_in_use(catalog, option_id):
            raise ServiceOperationError("No se puede desactivar una opción utilizada por servicios")
        try:
            result = self.repository.update_catalog_option(catalog, option_id, self._clean(values))
        except UniqueViolation as error:
            raise ServiceOperationError("El código o nombre del catálogo ya existe") from error
        if result is None:
            raise ServiceNotFoundError("Opción de catálogo no encontrada")
        return result

    def deactivate_catalog_option(self, catalog: str, option_id: int) -> dict[str, Any]:
        return self.update_catalog_option(catalog, option_id, {"active": False})

    def _validate_common(self, values: dict[str, Any], current: Service | None) -> None:
        level_1_code = values.get("level_1_code", current.level_1_code if current else None)
        if not level_1_code or not self.repository.level_1_is_active(level_1_code):
            raise ServiceOperationError("El servicio debe pertenecer a un nivel 1 existente y activo")

        for field, table in (("service_class_id", "service_classes"), ("criticality_id", "service_criticalities"), ("service_type_id", "service_types")):
            option_id = values.get(field, getattr(current, field, None) if current else None)
            if current is None and option_id is None:
                raise ServiceOperationError(f"El campo {field} es obligatorio")
            if option_id is not None and not self.repository.catalog_option_is_active(table, option_id):
                raise ServiceOperationError(f"La referencia {field} no existe o está inactiva")

        section_id = values.get("responsible_section_id", current.responsible_section_id if current else None)
        user_id = values.get("responsible_user_id", current.responsible_user_id if current else None)
        if current is None and section_id is None:
            raise ServiceOperationError("La sección responsable es obligatoria para servicios nuevos")
        if not self.repository.assignment_is_valid(section_id, user_id):
            raise ServiceOperationError("La sección o el usuario responsable no pertenecen a una asignación válida")

        minimum = values.get("minimum", current.minimum if current else None)
        maximum = values.get("maximum", current.maximum if current else None)
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ServiceOperationError("mínimo debe ser menor o igual que máximo")

    @staticmethod
    def _clean(values: dict[str, Any]) -> dict[str, Any]:
        clean = dict(values)
        for field in ("code", "level_1_code", "name", "description", "metric"):
            if clean.get(field) is not None and isinstance(clean[field], str):
                clean[field] = clean[field].strip()
        return clean
