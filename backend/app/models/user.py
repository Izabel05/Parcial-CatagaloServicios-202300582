from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class User:
    id: int
    username: str
    email: str
    full_name: str
    password_hash: str
    profile_encrypted: str
    is_active: bool
    role: str
    puesto_id: int
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
        "name": user.full_name or profile.get("display_name", user.username),
        "role": user.role,
        "puesto_id": user.puesto_id,
        "profile": profile,
    }
