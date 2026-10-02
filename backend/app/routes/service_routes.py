from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.controllers.service_controller import ServiceController
from backend.app.models.user import AuthenticatedContext
from backend.app.schemas.service_schema import (
    CatalogOptionCreateRequest,
    CatalogOptionResponse,
    CatalogOptionUpdateRequest,
    CatalogOptionsResponse,
    Level1CreateRequest,
    Level1Response,
    Level1UpdateRequest,
    ServiceCreateRequest,
    ServicePageResponse,
    ServiceResponse,
    ServiceUpdateRequest,
)
from backend.app.security.dependencies import require_administrator, require_functional_reader
from backend.app.services.service_service import ServiceNotFoundError, ServiceOperationError

router = APIRouter(prefix="/services", tags=["services"])


def get_service_controller() -> ServiceController:
    return ServiceController()


def _conflict(error: ServiceOperationError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.get("", response_model=ServicePageResponse)
def list_services(
    search: str | None = Query(default=None),
    level_1_code: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    service_class_id: int | None = Query(default=None, gt=0),
    criticality_id: int | None = Query(default=None, gt=0),
    service_type_id: int | None = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: ServiceController = Depends(get_service_controller),
):
    try:
        result = controller.list_services(
            search=search, level_1_code=level_1_code, active=active,
            service_class_id=service_class_id, criticality_id=criticality_id,
            service_type_id=service_type_id, page=page, page_size=page_size,
        )
        return ServicePageResponse(
            items=[ServiceResponse.model_validate(item, from_attributes=True) for item in result.items],
            total=result.total, page=result.page, page_size=result.page_size, pages=result.pages,
        )
    except ServiceOperationError as error:
        raise _conflict(error) from error


@router.get("/catalog-options", response_model=CatalogOptionsResponse)
def list_catalog_options(
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: ServiceController = Depends(get_service_controller),
):
    return controller.list_catalog_options()


@router.get("/level-1", response_model=list[Level1Response])
def list_level_1(
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: ServiceController = Depends(get_service_controller),
):
    return controller.list_level_1()


@router.get("/level-1/{code}", response_model=Level1Response)
def get_level_1(
    code: str,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: ServiceController = Depends(get_service_controller),
):
    try:
        return controller.get_level_1(code)
    except ServiceNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/level-1", response_model=Level1Response, status_code=status.HTTP_201_CREATED)
def create_level_1(
    payload: Level1CreateRequest,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: ServiceController = Depends(get_service_controller),
):
    try:
        return controller.create_level_1(payload.model_dump())
    except ServiceOperationError as error:
        raise _conflict(error) from error


@router.patch("/level-1/{code}", response_model=Level1Response)
def update_level_1(
    code: str,
    payload: Level1UpdateRequest,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: ServiceController = Depends(get_service_controller),
):
    try:
        return controller.update_level_1(code, payload.model_dump(exclude_unset=True))
    except ServiceNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ServiceOperationError as error:
        raise _conflict(error) from error


@router.delete("/level-1/{code}", response_model=Level1Response)
def delete_level_1(
    code: str,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: ServiceController = Depends(get_service_controller),
):
    try:
        return controller.update_level_1(code, {"active": False})
    except ServiceNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ServiceOperationError as error:
        raise _conflict(error) from error


@router.get("/{code}", response_model=ServiceResponse)
def get_service(
    code: str,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: ServiceController = Depends(get_service_controller),
):
    try:
        return ServiceResponse.model_validate(controller.get_service(code), from_attributes=True)
    except ServiceNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(
    payload: ServiceCreateRequest,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: ServiceController = Depends(get_service_controller),
):
    try:
        return ServiceResponse.model_validate(controller.create_service(payload.model_dump()), from_attributes=True)
    except ServiceOperationError as error:
        raise _conflict(error) from error


@router.patch("/{code}", response_model=ServiceResponse)
def update_service(
    code: str,
    payload: ServiceUpdateRequest,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: ServiceController = Depends(get_service_controller),
):
    try:
        return ServiceResponse.model_validate(
            controller.update_service(code, payload.model_dump(exclude_unset=True)), from_attributes=True,
        )
    except ServiceNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ServiceOperationError as error:
        raise _conflict(error) from error


@router.delete("/{code}", response_model=ServiceResponse)
def delete_service(
    code: str,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: ServiceController = Depends(get_service_controller),
):
    try:
        return ServiceResponse.model_validate(controller.deactivate_service(code), from_attributes=True)
    except ServiceNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ServiceOperationError as error:
        raise _conflict(error) from error


def _catalog_route_name(name: str) -> str:
    return name


for _catalog_name in ("classes", "criticalities", "types"):
    @router.get(f"/catalog/{_catalog_name}", response_model=list[CatalogOptionResponse], name=f"list_{_catalog_name}_catalog")
    def list_catalog(
        catalog_name: str = _catalog_name,
        _: AuthenticatedContext = Depends(require_functional_reader),
        controller: ServiceController = Depends(get_service_controller),
    ):
        return controller.list_catalog(catalog_name)

    @router.post(f"/catalog/{_catalog_name}", response_model=CatalogOptionResponse, status_code=status.HTTP_201_CREATED, name=f"create_{_catalog_name}_catalog")
    def create_catalog(
        payload: CatalogOptionCreateRequest,
        catalog_name: str = _catalog_name,
        _: AuthenticatedContext = Depends(require_administrator),
        controller: ServiceController = Depends(get_service_controller),
    ):
        try:
            return controller.create_catalog_option(catalog_name, payload.model_dump())
        except ServiceOperationError as error:
            raise _conflict(error) from error

    @router.patch(f"/catalog/{_catalog_name}/{{option_id}}", response_model=CatalogOptionResponse, name=f"update_{_catalog_name}_catalog")
    def update_catalog(
        option_id: int,
        payload: CatalogOptionUpdateRequest,
        catalog_name: str = _catalog_name,
        _: AuthenticatedContext = Depends(require_administrator),
        controller: ServiceController = Depends(get_service_controller),
    ):
        try:
            return controller.update_catalog_option(catalog_name, option_id, payload.model_dump(exclude_unset=True))
        except ServiceNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        except ServiceOperationError as error:
            raise _conflict(error) from error

    @router.delete(f"/catalog/{_catalog_name}/{{option_id}}", response_model=CatalogOptionResponse, name=f"delete_{_catalog_name}_catalog")
    def delete_catalog(
        option_id: int,
        catalog_name: str = _catalog_name,
        _: AuthenticatedContext = Depends(require_administrator),
        controller: ServiceController = Depends(get_service_controller),
    ):
        try:
            return controller.deactivate_catalog_option(catalog_name, option_id)
        except ServiceNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        except ServiceOperationError as error:
            raise _conflict(error) from error
