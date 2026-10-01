from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class User:
    id: int
    username: str
    email: str
    password_hash: str
    profile_encrypted: str
    is_active: bool
    is_admin: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuthenticatedContext:
    user: User
    raw_token: str


@dataclass(frozen=True, slots=True)
class LoginResult:
    access_token: str
    token_type: str
    expires_at: datetime
    user: User


def public_profile(user: User, profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin,
        "profile": profile,
    }
