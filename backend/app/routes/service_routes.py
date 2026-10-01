from fastapi import APIRouter, Depends

from backend.app.controllers.service_controller import ServiceController
from backend.app.models.user import AuthenticatedContext
from backend.app.schemas.service_schema import ServiceResponse
from backend.app.security.dependencies import require_authentication

router = APIRouter(prefix="/services", tags=["services"])
controller = ServiceController()


@router.get("", response_model=list[ServiceResponse])
def list_services(_: AuthenticatedContext = Depends(require_authentication)) -> list[ServiceResponse]:
    return controller.list_services()
