from typing import Any

from backend.app.database.connection import get_connection


class UserAdminRepository:
    def get_user(self, user_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """SELECT id, full_name AS name, username, email, role, is_active, puesto_id, created_at
                FROM users WHERE id=%s""",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def assigned_service_sections(self, user_id: int) -> set[int]:
        with get_connection() as connection:
            rows = connection.execute(
                """SELECT DISTINCT responsible_section_id FROM services
                WHERE responsible_user_id=%s AND responsible_section_id IS NOT NULL""",
                (user_id,),
            ).fetchall()
        return {int(row["responsible_section_id"]) for row in rows}

    def list_users(self) -> list[dict[str, Any]]:
        with get_connection() as connection:
            return list(connection.execute(
                """SELECT id, full_name AS name, username, email, role, is_active, puesto_id, created_at
                FROM users ORDER BY username_normalized"""
            ).fetchall())

    def create_user(self, values: tuple[Any, ...]) -> dict[str, Any]:
        query = """INSERT INTO users
            (full_name, username, username_normalized, email, email_normalized, password_hash,
             profile_encrypted, is_admin, role, puesto_id, is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id, full_name AS name, username, email, role, is_active, puesto_id, created_at"""
        with get_connection() as connection:
            return dict(connection.execute(query, values).fetchone())

    def set_status(self, user_id: int, is_active: bool) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """UPDATE users SET is_active=%s, updated_at=CURRENT_TIMESTAMP
                WHERE id=%s RETURNING id, full_name AS name, username, email, role, is_active, puesto_id, created_at""",
                (is_active, user_id),
            ).fetchone()
            if row and not is_active:
                connection.execute(
                    "UPDATE user_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE user_id=%s AND revoked_at IS NULL",
                    (user_id,),
                )
        return dict(row) if row else None

    def set_role(self, user_id: int, role: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """UPDATE users SET role=%s, is_admin=%s, updated_at=CURRENT_TIMESTAMP
                WHERE id=%s RETURNING id, full_name AS name, username, email, role, is_active, puesto_id, created_at""",
                (role, role == "administrador", user_id),
            ).fetchone()
        return dict(row) if row else None

    def update_user(self, user_id: int, values: tuple[Any, ...]) -> dict[str, Any] | None:
        query = """UPDATE users SET
            full_name=COALESCE(%s,full_name),
            username=COALESCE(%s,username),
            username_normalized=COALESCE(%s,username_normalized),
            email=COALESCE(%s,email),
            email_normalized=COALESCE(%s,email_normalized),
            password_hash=COALESCE(%s,password_hash),
            role=COALESCE(%s,role),
            is_admin=(COALESCE(%s,role)='administrador'),
            puesto_id=COALESCE(%s,puesto_id),
            is_active=COALESCE(%s,is_active),
            updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            RETURNING id, full_name AS name, username, email, role, is_active, puesto_id, created_at"""
        with get_connection() as connection:
            row = connection.execute(query, (*values, user_id)).fetchone()
            if row and values[-1] is False:
                connection.execute(
                    "UPDATE user_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE user_id=%s AND revoked_at IS NULL",
                    (user_id,),
                )
        return dict(row) if row else None


class OrganizationRepository:
    def list_all(self) -> list[dict[str, Any]]:
        with get_connection() as connection:
            return list(connection.execute(
                """SELECT id, code, name, description, active, created_at
                FROM organization_units ORDER BY code"""
            ).fetchall())

    def create(self, values: tuple[Any, ...]) -> dict[str, Any]:
        with get_connection() as connection:
            return dict(connection.execute(
                """INSERT INTO organization_units (code,name,description,active)
                VALUES (%s,%s,%s,%s)
                RETURNING id, code, name, description, active, created_at""",
                values,
            ).fetchone())

    def update(self, organization_id: int, values: tuple[Any, ...]) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """UPDATE organization_units SET name=COALESCE(%s,name), description=COALESCE(%s,description),
                active=COALESCE(%s,active), updated_at=CURRENT_TIMESTAMP WHERE id=%s
                RETURNING id, code, name, description, active, created_at""",
                (*values, organization_id),
            ).fetchone()
        return dict(row) if row else None


class CatalogAdminRepository:
    def update_service(self, code: str, values: tuple[Any, ...]) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """UPDATE services SET name=COALESCE(%s,name), active=COALESCE(%s,active),
                description=COALESCE(%s,description), metric=COALESCE(%s,metric), minimum=COALESCE(%s,minimum),
                maximum=COALESCE(%s,maximum), review_status=COALESCE(%s,review_status),
                transformations=transformations || %s::jsonb, updated_at=CURRENT_TIMESTAMP
                WHERE code=%s
                RETURNING id, code, level_1_code, name, active, service_class, criticality, service_type,
                description, metric, minimum, maximum, review_status""",
                (*values, code),
            ).fetchone()
        return dict(row) if row else None
