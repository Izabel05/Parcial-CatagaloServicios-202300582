from datetime import datetime
from typing import Any
from uuid import UUID

from backend.app.database.connection import get_connection


class SessionRepository:
    def create(
        self,
        session_id: UUID,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None,
        ip_address: str | None,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """INSERT INTO user_sessions
                (id, user_id, token_hash, expires_at, user_agent, ip_address)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (session_id, user_id, token_hash, expires_at, user_agent, ip_address),
            )

    def find_active_user_id(self, token_hash: str) -> int | None:
        with get_connection() as connection:
            row = connection.execute(
                """UPDATE user_sessions SET last_seen_at=CURRENT_TIMESTAMP
                WHERE token_hash=%s AND revoked_at IS NULL AND expires_at > CURRENT_TIMESTAMP
                RETURNING user_id""",
                (token_hash,),
            ).fetchone()
        return int(row["user_id"]) if row else None

    def revoke(self, token_hash: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE user_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE token_hash=%s AND revoked_at IS NULL",
                (token_hash,),
            )
