from typing import Any

from backend.app.database.connection import get_connection
from backend.app.models.user import User


class UserRepository:
    def find_by_identifier(self, identifier: str) -> User | None:
        normalized = identifier.strip().casefold()
        query = """
            SELECT id, username, email, full_name, password_hash, profile_encrypted,
                   is_active, role, puesto_id, created_at
            FROM users
            WHERE username_normalized = %s OR email_normalized = %s
        """
        with get_connection() as connection:
            row = connection.execute(query, (normalized, normalized)).fetchone()
        return self._to_model(row) if row else None

    def find_by_id(self, user_id: int) -> User | None:
        query = """
            SELECT id, username, email, full_name, password_hash, profile_encrypted,
                   is_active, role, puesto_id, created_at
            FROM users
            WHERE id = %s
        """
        with get_connection() as connection:
            row = connection.execute(query, (user_id,)).fetchone()
        return self._to_model(row) if row else None

    def update_password_hash(self, user_id: int, password_hash: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE users SET password_hash=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                (password_hash, user_id),
            )

    @staticmethod
    def _to_model(row: Any) -> User:
        return User(**row)
