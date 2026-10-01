from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.app.controllers.auth_controller import AuthController
from backend.app.models.user import AuthenticatedContext
from backend.app.schemas.auth_schema import LoginRequest, LoginResponse, UserResponse
from backend.app.security.dependencies import get_auth_service, require_authentication
from backend.app.services.auth_service import AuthService, InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_controller(auth_service: AuthService = Depends(get_auth_service)) -> AuthController:
    return AuthController(auth_service)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    controller: AuthController = Depends(get_auth_controller),
) -> LoginResponse:
    try:
        result = controller.login(
            payload.identifier,
            payload.password,
            request.headers.get("user-agent"),
            request.client.host if request.client else None,
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return LoginResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        expires_at=result.expires_at,
        user=UserResponse.model_validate(controller.profile(result.user)),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    context: AuthenticatedContext = Depends(require_authentication),
    controller: AuthController = Depends(get_auth_controller),
) -> None:
    controller.logout(context)


@router.get("/me", response_model=UserResponse)
def me(
    context: AuthenticatedContext = Depends(require_authentication),
    controller: AuthController = Depends(get_auth_controller),
) -> UserResponse:
    return UserResponse.model_validate(controller.me(context))
