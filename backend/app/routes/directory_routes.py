from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.controllers.directory_controller import DirectoryController
from backend.app.models.user import AuthenticatedContext
from backend.app.schemas.hierarchy_schema import (
    AreaCreate,
    AreaResponse,
    AreaUpdate,
    DepartamentoCreate,
    DepartamentoResponse,
    DepartamentoUpdate,
    EmpresaCreate,
    EmpresaResponse,
    EmpresaUpdate,
    PuestoCreate,
    PuestoResponse,
    PuestoUpdate,
    SeccionCreate,
    SeccionResponse,
    SeccionUpdate,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)
from backend.app.security.dependencies import require_administrator, require_functional_reader
from backend.app.services.directory_service import DirectoryNotFoundError, DirectoryOperationError, DirectoryService

router = APIRouter(tags=["directorio organizacional"])


def get_directory_service() -> DirectoryService:
    return DirectoryService()


def get_directory_controller(service: DirectoryService = Depends(get_directory_service)) -> DirectoryController:
    return DirectoryController(service)


def _conflict(error: DirectoryOperationError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.get("/empresas", response_model=list[EmpresaResponse])
def list_empresas(
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return controller.list_entity("empresas")


@router.get("/empresas/{entity_id}", response_model=EmpresaResponse)
def get_empresa(
    entity_id: int,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _get_entity("empresas", entity_id, controller)


@router.post("/empresas", response_model=EmpresaResponse, status_code=status.HTTP_201_CREATED)
def create_empresa(
    payload: EmpresaCreate,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    try:
        return controller.create_entity("empresas", payload.model_dump())
    except DirectoryOperationError as error:
        raise _conflict(error) from error


@router.patch("/empresas/{entity_id}", response_model=EmpresaResponse)
def update_empresa(
    entity_id: int,
    payload: EmpresaUpdate,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    try:
        return controller.update_entity("empresas", entity_id, payload.model_dump(exclude_unset=True))
    except DirectoryNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DirectoryOperationError as error:
        raise _conflict(error) from error


@router.delete("/empresas/{entity_id}", response_model=EmpresaResponse)
def delete_empresa(
    entity_id: int,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    try:
        return controller.delete_entity("empresas", entity_id)
    except DirectoryNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DirectoryOperationError as error:
        raise _conflict(error) from error


@router.get("/areas", response_model=list[AreaResponse])
def list_areas(
    empresa_id: int | None = None,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return controller.list_entity("areas", empresa_id)


@router.get("/areas/{entity_id}", response_model=AreaResponse)
def get_area(
    entity_id: int,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _get_entity("areas", entity_id, controller)


@router.post("/areas", response_model=AreaResponse, status_code=status.HTTP_201_CREATED)
def create_area(
    payload: AreaCreate,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    try:
        return controller.create_entity("areas", payload.model_dump())
    except DirectoryOperationError as error:
        raise _conflict(error) from error


@router.patch("/areas/{entity_id}", response_model=AreaResponse)
def update_area(
    entity_id: int,
    payload: AreaUpdate,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _update_entity("areas", entity_id, payload.model_dump(exclude_unset=True), controller)


@router.delete("/areas/{entity_id}", response_model=AreaResponse)
def delete_area(
    entity_id: int,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _delete_entity("areas", entity_id, controller)


@router.get("/departamentos", response_model=list[DepartamentoResponse])
def list_departamentos(
    area_id: int | None = None,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return controller.list_entity("departamentos", area_id)


@router.get("/departamentos/{entity_id}", response_model=DepartamentoResponse)
def get_departamento(
    entity_id: int,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _get_entity("departamentos", entity_id, controller)


@router.post("/departamentos", response_model=DepartamentoResponse, status_code=status.HTTP_201_CREATED)
def create_departamento(
    payload: DepartamentoCreate,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    try:
        return controller.create_entity("departamentos", payload.model_dump())
    except DirectoryOperationError as error:
        raise _conflict(error) from error


@router.patch("/departamentos/{entity_id}", response_model=DepartamentoResponse)
def update_departamento(
    entity_id: int,
    payload: DepartamentoUpdate,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _update_entity("departamentos", entity_id, payload.model_dump(exclude_unset=True), controller)


@router.delete("/departamentos/{entity_id}", response_model=DepartamentoResponse)
def delete_departamento(
    entity_id: int,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _delete_entity("departamentos", entity_id, controller)


@router.get("/secciones", response_model=list[SeccionResponse])
def list_secciones(
    departamento_id: int | None = None,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return controller.list_entity("secciones", departamento_id)


@router.get("/secciones/{entity_id}", response_model=SeccionResponse)
def get_seccion(
    entity_id: int,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _get_entity("secciones", entity_id, controller)


@router.post("/secciones", response_model=SeccionResponse, status_code=status.HTTP_201_CREATED)
def create_seccion(
    payload: SeccionCreate,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    try:
        return controller.create_entity("secciones", payload.model_dump())
    except DirectoryOperationError as error:
        raise _conflict(error) from error


@router.patch("/secciones/{entity_id}", response_model=SeccionResponse)
def update_seccion(
    entity_id: int,
    payload: SeccionUpdate,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _update_entity("secciones", entity_id, payload.model_dump(exclude_unset=True), controller)


@router.delete("/secciones/{entity_id}", response_model=SeccionResponse)
def delete_seccion(
    entity_id: int,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _delete_entity("secciones", entity_id, controller)


@router.get("/puestos", response_model=list[PuestoResponse])
def list_puestos(
    seccion_id: int | None = None,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return controller.list_entity("puestos", seccion_id)


@router.get("/puestos/{entity_id}", response_model=PuestoResponse)
def get_puesto(
    entity_id: int,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _get_entity("puestos", entity_id, controller)


@router.post("/puestos", response_model=PuestoResponse, status_code=status.HTTP_201_CREATED)
def create_puesto(
    payload: PuestoCreate,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    try:
        return controller.create_entity("puestos", payload.model_dump())
    except DirectoryOperationError as error:
        raise _conflict(error) from error


@router.patch("/puestos/{entity_id}", response_model=PuestoResponse)
def update_puesto(
    entity_id: int,
    payload: PuestoUpdate,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _update_entity("puestos", entity_id, payload.model_dump(exclude_unset=True), controller)


@router.delete("/puestos/{entity_id}", response_model=PuestoResponse)
def delete_puesto(
    entity_id: int,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return _delete_entity("puestos", entity_id, controller)


@router.get("/usuarios", response_model=list[UsuarioResponse])
def list_usuarios(
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    return controller.list_users()


@router.get("/usuarios/{user_id}", response_model=UsuarioResponse)
def get_usuario(
    user_id: int,
    _: AuthenticatedContext = Depends(require_functional_reader),
    controller: DirectoryController = Depends(get_directory_controller),
):
    try:
        return controller.get_user(user_id)
    except DirectoryNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def create_usuario(
    payload: UsuarioCreate,
    _: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    try:
        return controller.create_user(payload.model_dump())
    except DirectoryOperationError as error:
        raise _conflict(error) from error


@router.patch("/usuarios/{user_id}", response_model=UsuarioResponse)
def update_usuario(
    user_id: int,
    payload: UsuarioUpdate,
    actor: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    try:
        return controller.update_user(actor, user_id, payload.model_dump(exclude_unset=True))
    except DirectoryNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DirectoryOperationError as error:
        raise _conflict(error) from error


@router.delete("/usuarios/{user_id}", response_model=UsuarioResponse)
def delete_usuario(
    user_id: int,
    actor: AuthenticatedContext = Depends(require_administrator),
    controller: DirectoryController = Depends(get_directory_controller),
):
    try:
        return controller.delete_user(actor, user_id)
    except DirectoryNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DirectoryOperationError as error:
        raise _conflict(error) from error


def _update_entity(entity: str, entity_id: int, values: dict, controller: DirectoryController):
    try:
        return controller.update_entity(entity, entity_id, values)
    except DirectoryNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DirectoryOperationError as error:
        raise _conflict(error) from error


def _get_entity(entity: str, entity_id: int, controller: DirectoryController):
    try:
        return controller.get_entity(entity, entity_id)
    except DirectoryNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


def _delete_entity(entity: str, entity_id: int, controller: DirectoryController):
    try:
        return controller.delete_entity(entity, entity_id)
    except DirectoryNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DirectoryOperationError as error:
        raise _conflict(error) from error
