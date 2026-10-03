from __future__ import annotations

import hashlib
from ipaddress import ip_address
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.app.config.settings import settings
from backend.app.models.user import AuthenticatedContext, LoginResult, User, public_profile
from backend.app.repositories.session_repository import SessionRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.security.encryption import AesGcmCipher
from backend.app.security.passwords import PasswordService


class InvalidCredentialsError(Exception):
    """Credenciales inexistentes, incorrectas o de usuario inactivo."""


class InvalidSessionError(Exception):
    """Token ausente, revocado o expirado."""


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository | None = None,
        session_repository: SessionRepository | None = None,
        password_service: PasswordService | None = None,
        profile_cipher: AesGcmCipher | None = None,
    ) -> None:
        self._users = user_repository or UserRepository()
        self._sessions = session_repository or SessionRepository()
        self._passwords = password_service or PasswordService()
        self._profile_cipher = profile_cipher or AesGcmCipher(settings.app_encryption_key)

    def login(
        self,
        identifier: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> LoginResult:
        user = self._users.find_by_identifier(identifier)
        if user is None or not user.is_active or not self._passwords.verify(user.password_hash, password):
            raise InvalidCredentialsError("Usuario o contraseña inválidos")
        if self._passwords.needs_rehash(user.password_hash):
            self._users.update_password_hash(user.id, self._passwords.hash(password))

        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.session_expire_minutes)
        self._sessions.create(
            session_id=uuid4(),
            user_id=user.id,
            token_hash=self._hash_token(raw_token),
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=self._normalize_ip_address(ip_address),
        )
        return LoginResult(raw_token, "bearer", expires_at, user)

    def authenticate(self, raw_token: str) -> AuthenticatedContext:
        user_id = self._sessions.find_active_user_id(self._hash_token(raw_token))
        if user_id is None:
            raise InvalidSessionError("Sesión inválida o expirada")
        user = self._users.find_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidSessionError("Sesión inválida o usuario inactivo")
        return AuthenticatedContext(user=user, raw_token=raw_token)

    def logout(self, raw_token: str) -> None:
        self._sessions.revoke(self._hash_token(raw_token))

    def profile(self, user: User) -> dict[str, object]:
        decrypted_profile = self._profile_cipher.decrypt_json(user.profile_encrypted)
        return public_profile(user, decrypted_profile)

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_ip_address(value: str | None) -> str | None:
        """Evita insertar hosts de prueba o valores no válidos en una columna INET."""
        if not value:
            return None
        try:
            return str(ip_address(value))
        except ValueError:
            return None
