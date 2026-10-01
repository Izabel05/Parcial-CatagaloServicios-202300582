from backend.app.models.user import AuthenticatedContext, LoginResult, User
from backend.app.services.auth_service import AuthService


class AuthController:
    def __init__(self, auth_service: AuthService) -> None:
        self._auth = auth_service

    def login(self, identifier: str, password: str, user_agent: str | None, ip_address: str | None) -> LoginResult:
        return self._auth.login(identifier, password, user_agent, ip_address)

    def logout(self, context: AuthenticatedContext) -> None:
        self._auth.logout(context.raw_token)

    def me(self, context: AuthenticatedContext) -> dict[str, object]:
        return self._auth.profile(context.user)

    def profile(self, user: User) -> dict[str, object]:
        return self._auth.profile(user)
