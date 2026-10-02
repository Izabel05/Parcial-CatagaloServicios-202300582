from backend.app.services.service_service import ServiceService


class ServiceController:
    def __init__(self, service: ServiceService | None = None) -> None:
        self.service = service or ServiceService()

    def list_services(self, **filters):
        return self.service.list_services(**filters)

    def get_service(self, code: str):
        return self.service.get_service(code)

    def create_service(self, values):
        return self.service.create_service(values)

    def update_service(self, code: str, values):
        return self.service.update_service(code, values)

    def deactivate_service(self, code: str):
        return self.service.deactivate_service(code)

    def list_level_1(self):
        return self.service.list_level_1()

    def get_level_1(self, code: str):
        return self.service.get_level_1(code)

    def create_level_1(self, values):
        return self.service.create_level_1(values)

    def update_level_1(self, code: str, values):
        return self.service.update_level_1(code, values)

    def list_catalog_options(self):
        return self.service.list_catalog_options()

    def list_catalog(self, catalog: str, include_inactive: bool = False):
        return self.service.list_catalog(catalog, include_inactive)

    def create_catalog_option(self, catalog: str, values):
        return self.service.create_catalog_option(catalog, values)

    def update_catalog_option(self, catalog: str, option_id: int, values):
        return self.service.update_catalog_option(catalog, option_id, values)

    def deactivate_catalog_option(self, catalog: str, option_id: int):
        return self.service.deactivate_catalog_option(catalog, option_id)
