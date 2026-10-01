from backend.app.database.connection import get_connection
from backend.app.models.service import Service


class ServiceRepository:
    """Acceso a servicios persistidos en PostgreSQL."""

    def list_all(self) -> list[Service]:
        query = """
            SELECT id, code, level_1_code, name, active, service_class,
                   criticality, service_type, description, metric, minimum, maximum, review_status
            FROM services
            ORDER BY level_1_code, code
        """
        with get_connection() as connection:
            rows = connection.execute(query).fetchall()
        return [Service(**row) for row in rows]
