from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.controllers.admin_controller import AdminController
from backend.app.controllers.service_controller import ServiceController
from backend.app.models.user import AuthenticatedContext
from backend.app.schemas.admin_schema import (
    AdminUserResponse,
    CreateUserRequest,
    OrganizationRequest,
    OrganizationResponse,
    OrganizationUpdateRequest,
    UserRoleRequest,
    UserStatusRequest,
)
from backend.app.schemas.service_schema import ServiceResponse, ServiceUpdateRequest
from backend.app.security.dependencies import require_administrator, require_functional_reader
from backend.app.services.admin_service import AdminOperationError, AdminService
from backend.app.services.service_service import ServiceNotFoundError, ServiceOperationError

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_service() -> AdminService:
    return AdminService()


def get_admin_controller(admin_service: AdminService = Depends(get_admin_service)) -> AdminController:
    return AdminController(admin_service)


def get_service_controller() -> ServiceController:
    return ServiceController()


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(
    _: AuthenticatedContext = Depends(require_administrator),
    controller: AdminController = Depends(get_admin_controller),
):
    return controller.list_users()


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: AdminController = Depends(get_admin_controller),
):
    try:
        return controller.create_user(payload.model_dump())
    except AdminOperationError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
def set_user_status(
    user_id: int,
    payload: UserStatusRequest,
    actor: AuthenticatedContext = Depends(require_administrator),
    controller: AdminController = Depends(get_admin_controller),
):
    try:
        return controller.set_user_status(actor, user_id, payload.is_active)
    except AdminOperationError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
def set_user_role(
    user_id: int,
    payload: UserRoleRequest,
    actor: AuthenticatedContext = Depends(require_administrator),
    controller: AdminController = Depends(get_admin_controller),
):
    try:
        return controller.set_user_role(actor, user_id, payload.role)
    except AdminOperationError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/organizations", response_model=list[OrganizationResponse])
def list_organizations(
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: AdminController = Depends(get_admin_controller),
):
    return controller.list_organizations()


@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationRequest,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: AdminController = Depends(get_admin_controller),
):
    try:
        return controller.create_organization(payload.model_dump())
    except AdminOperationError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.patch("/organizations/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: int,
    payload: OrganizationUpdateRequest,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: AdminController = Depends(get_admin_controller),
):
    try:
        return controller.update_organization(organization_id, payload.model_dump())
    except AdminOperationError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.put("/services/{code}", response_model=ServiceResponse)
def update_catalog_service(
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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
