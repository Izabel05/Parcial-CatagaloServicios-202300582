from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.models.user import AuthenticatedContext
from backend.app.services.auth_service import AuthService, InvalidSessionError

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service() -> AuthService:
    return AuthService()


def require_authentication(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthenticatedContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return auth_service.authenticate(credentials.credentials)
    except InvalidSessionError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def require_roles(*allowed_roles: str) -> Callable[..., AuthenticatedContext]:
    """Crea una dependencia de autorización para rutas protegidas por rol."""

    def dependency(context: AuthenticatedContext = Depends(require_authentication)) -> AuthenticatedContext:
        if context.user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El rol no tiene permisos para esta operación",
            )
        return context

    return dependency


require_administrator = require_roles("administrador")
require_functional_reader = require_roles("administrador", "consulta")
