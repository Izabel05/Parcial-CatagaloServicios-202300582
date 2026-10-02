from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from backend.app.database.connection import get_connection
from backend.app.models.service import Service


SERVICE_SELECT = """SELECT s.id, s.code, s.original_code, s.level_1_code, l.name AS level_1_name,
    s.name, s.active, s.service_class, s.criticality, s.service_type, s.description, s.metric,
    s.minimum, s.maximum, s.review_status, s.service_class_id, c.name AS service_class_name,
    s.criticality_id, cr.name AS criticality_name, s.service_type_id, st.name AS service_type_name,
    s.source_sheet, s.source_row, s.source_range, s.transformations,
    s.responsible_section_id, sec.codigo AS responsible_section_code,
    s.responsible_user_id, u.full_name AS responsible_user_name
    FROM services s
    JOIN service_level_1 l ON l.code=s.level_1_code
    LEFT JOIN service_classes c ON c.id=s.service_class_id
    LEFT JOIN service_criticalities cr ON cr.id=s.criticality_id
    LEFT JOIN service_types st ON st.id=s.service_type_id
    LEFT JOIN secciones sec ON sec.id=s.responsible_section_id
    LEFT JOIN users u ON u.id=s.responsible_user_id"""


class ServiceRepository:
    """Acceso a servicios, niveles 1 y catálogos controlados."""

    def list_page(
        self, search: str | None, level_1_code: str | None, active: bool | None,
        service_class_id: int | None, criticality_id: int | None, service_type_id: int | None,
        page: int, page_size: int,
    ) -> tuple[list[Service], int]:
        conditions: list[str] = []
        params: list[Any] = []
        if search:
            conditions.append("(s.code ILIKE %s OR s.name ILIKE %s)")
            like = f"%{search.strip()}%"
            params.extend((like, like))
        if level_1_code:
            conditions.append("s.level_1_code=%s")
            params.append(level_1_code.strip())
        if active is not None:
            conditions.append("s.active=%s")
            params.append(active)
        for field, value in (("service_class_id", service_class_id), ("criticality_id", criticality_id), ("service_type_id", service_type_id)):
            if value is not None:
                conditions.append(f"s.{field}=%s")
                params.append(value)
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        offset = (page - 1) * page_size
        with get_connection() as connection:
            total = connection.execute(f"SELECT COUNT(*) AS total FROM services s{where}", params).fetchone()["total"]
            rows = connection.execute(
                f"{SERVICE_SELECT}{where} ORDER BY s.level_1_code, s.code LIMIT %s OFFSET %s",
                (*params, page_size, offset),
            ).fetchall()
        return [Service(**row) for row in rows], int(total)

    def get_by_code(self, code: str) -> Service | None:
        with get_connection() as connection:
            row = connection.execute(f"{SERVICE_SELECT} WHERE s.code=%s", (code,)).fetchone()
        return Service(**row) if row else None

    def level_1_is_active(self, code: str) -> bool:
        with get_connection() as connection:
            row = connection.execute("SELECT 1 FROM service_level_1 WHERE code=%s AND active", (code,)).fetchone()
        return row is not None

    def catalog_option_is_active(self, table: str, option_id: int) -> bool:
        if table not in {"service_classes", "service_criticalities", "service_types"}:
            raise ValueError("Catálogo no soportado")
        with get_connection() as connection:
            row = connection.execute(f"SELECT 1 FROM {table} WHERE id=%s AND active", (option_id,)).fetchone()
        return row is not None

    def assignment_is_valid(self, section_id: int | None, user_id: int | None) -> bool:
        if section_id is None:
            return user_id is None
        with get_connection() as connection:
            section = connection.execute("SELECT 1 FROM secciones WHERE id=%s AND activo", (section_id,)).fetchone()
            if section is None:
                return False
            if user_id is None:
                return True
            user = connection.execute(
                """SELECT 1 FROM users u
                JOIN puestos p ON p.id=u.puesto_id AND p.activo
                JOIN secciones s ON s.id=p.seccion_id AND s.activo
                JOIN departamentos d ON d.id=s.departamento_id AND d.activo
                JOIN areas a ON a.id=d.area_id AND a.activo
                JOIN empresas e ON e.id=a.empresa_id AND e.activo
                WHERE u.id=%s AND u.is_active AND s.id=%s""",
                (user_id, section_id),
            ).fetchone()
        return user is not None

    def create(self, values: dict[str, Any]) -> Service:
        query = """INSERT INTO services
            (code, original_code, level_1_code, name, active, service_class, criticality, service_type,
             service_class_id, criticality_id, service_type_id, description, metric, minimum, maximum,
             review_status, source_sheet, source_row, source_range, transformations,
             responsible_section_id, responsible_user_id)
            SELECT %s,%s,l.code,%s,%s,c.name,cr.name,st.name,c.id,cr.id,st.id,%s,%s,%s,%s,%s,
                   'MANUAL',0,'MANUAL',%s,%s,%s
            FROM service_level_1 l
            JOIN service_classes c ON c.id=%s AND c.active
            JOIN service_criticalities cr ON cr.id=%s AND cr.active
            JOIN service_types st ON st.id=%s AND st.active
            WHERE l.code=%s AND l.active
            RETURNING code"""
        params = (
            values["code"], values["code"], values["name"], values["active"], values.get("description"),
            values.get("metric"), values.get("minimum"), values.get("maximum"), values.get("review_status", "OK"),
            Jsonb(values.get("transformations", {})), values["responsible_section_id"], values.get("responsible_user_id"),
            values["service_class_id"], values["criticality_id"], values["service_type_id"], values["level_1_code"],
        )
        with get_connection() as connection:
            row = connection.execute(query, params).fetchone()
        if row is None:
            raise ValueError("El nivel 1 o un catálogo no existe o está inactivo")
        result = self.get_by_code(values["code"])
        if result is None:
            raise ValueError("No se pudo recuperar el servicio creado")
        return result

    def update(self, code: str, values: dict[str, Any]) -> Service | None:
        assignments: list[str] = []
        params: list[Any] = []
        for field in ("level_1_code", "name", "active", "description", "metric", "minimum", "maximum", "review_status", "responsible_section_id", "responsible_user_id"):
            if field in values:
                assignments.append(f"{field}=%s")
                params.append(values[field])
        for id_field, text_field, table in (
            ("service_class_id", "service_class", "service_classes"),
            ("criticality_id", "criticality", "service_criticalities"),
            ("service_type_id", "service_type", "service_types"),
        ):
            if id_field in values:
                assignments.extend((f"{id_field}=%s", f"{text_field}=(SELECT name FROM {table} WHERE id=%s)"))
                params.extend((values[id_field], values[id_field]))
        if not assignments:
            return self.get_by_code(code)
        with get_connection() as connection:
            row = connection.execute(
                f"UPDATE services SET {', '.join(assignments)}, updated_at=CURRENT_TIMESTAMP WHERE code=%s RETURNING code",
                (*params, code),
            ).fetchone()
        return self.get_by_code(row["code"]) if row else None

    def list_level_1(self) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """SELECT code, original_code, name, name_variants, active, review_status,
                source_sheet, source_row, source_range, transformations
                FROM service_level_1 ORDER BY sort_order, code"""
            ).fetchall()
        return [dict(row) for row in rows]

    def get_level_1(self, code: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """SELECT code, original_code, name, name_variants, active, review_status,
                source_sheet, source_row, source_range, transformations
                FROM service_level_1 WHERE code=%s""",
                (code,),
            ).fetchone()
        return dict(row) if row else None

    def create_level_1(self, values: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as connection:
            row = connection.execute(
                """INSERT INTO service_level_1
                (code, original_code, name, name_variants, active, review_status, source_sheet, source_row, source_range, transformations, sort_order)
                VALUES (%s,%s,%s,'[]'::jsonb,%s,'OK','MANUAL',0,'MANUAL','{}'::jsonb,
                        (SELECT COALESCE(MAX(sort_order),0)+1 FROM service_level_1))
                RETURNING code""",
                (values["code"], values["code"], values["name"], values.get("active", True)),
            ).fetchone()
        return self.get_level_1(row["code"])

    def update_level_1(self, code: str, values: dict[str, Any]) -> dict[str, Any] | None:
        assignments: list[str] = []
        params: list[Any] = []
        for field in ("code", "name", "active"):
            if field in values:
                assignments.append(f"{field}=%s")
                params.append(values[field])
        if not assignments:
            return self.get_level_1(code)
        with get_connection() as connection:
            row = connection.execute(
                f"UPDATE service_level_1 SET {', '.join(assignments)} WHERE code=%s RETURNING code",
                (*params, code),
            ).fetchone()
        return self.get_level_1(row["code"]) if row else None

    def can_deactivate_level_1(self, code: str) -> bool:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM services WHERE level_1_code=%s AND active IS TRUE LIMIT 1",
                (code,),
            ).fetchone()
        return row is None

    def list_catalog_options(self) -> dict[str, list[dict[str, Any]]]:
        with get_connection() as connection:
            return {
                "service_classes": [dict(row) for row in connection.execute("SELECT id,code,name,active FROM service_classes WHERE active ORDER BY name").fetchall()],
                "criticalities": [dict(row) for row in connection.execute("SELECT id,code,name,active FROM service_criticalities WHERE active ORDER BY id").fetchall()],
                "service_types": [dict(row) for row in connection.execute("SELECT id,code,name,active FROM service_types WHERE active ORDER BY name").fetchall()],
            }

    def list_catalog(self, catalog: str, include_inactive: bool = False) -> list[dict[str, Any]]:
        table = self._catalog_table(catalog)
        where = "" if include_inactive else " WHERE active"
        with get_connection() as connection:
            rows = connection.execute(f"SELECT id,code,name,active FROM {table}{where} ORDER BY name").fetchall()
        return [dict(row) for row in rows]

    def create_catalog_option(self, catalog: str, values: dict[str, Any]) -> dict[str, Any]:
        table = self._catalog_table(catalog)
        with get_connection() as connection:
            row = connection.execute(
                f"INSERT INTO {table} (code,name,active) VALUES (%s,%s,%s) RETURNING id",
                (values["code"], values["name"], values.get("active", True)),
            ).fetchone()
        return self.get_catalog_option(catalog, int(row["id"]))

    def get_catalog_option(self, catalog: str, option_id: int) -> dict[str, Any] | None:
        table = self._catalog_table(catalog)
        with get_connection() as connection:
            row = connection.execute(f"SELECT id,code,name,active FROM {table} WHERE id=%s", (option_id,)).fetchone()
        return dict(row) if row else None

    def update_catalog_option(self, catalog: str, option_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
        table = self._catalog_table(catalog)
        assignments = [f"{field}=%s" for field in ("code", "name", "active") if field in values]
        if not assignments:
            return self.get_catalog_option(catalog, option_id)
        params = [values[field] for field in ("code", "name", "active") if field in values]
        with get_connection() as connection:
            row = connection.execute(
                f"UPDATE {table} SET {', '.join(assignments)} WHERE id=%s RETURNING id",
                (*params, option_id),
            ).fetchone()
        return self.get_catalog_option(catalog, int(row["id"])) if row else None

    def catalog_option_in_use(self, catalog: str, option_id: int) -> bool:
        field = {"classes": "service_class_id", "criticalities": "criticality_id", "types": "service_type_id"}.get(catalog)
        if field is None:
            raise ValueError("Catálogo no soportado")
        with get_connection() as connection:
            row = connection.execute(f"SELECT 1 FROM services WHERE {field}=%s LIMIT 1", (option_id,)).fetchone()
        return row is not None

    @staticmethod
    def _catalog_table(catalog: str) -> str:
        tables = {"classes": "service_classes", "criticalities": "service_criticalities", "types": "service_types"}
        try:
            return tables[catalog]
        except KeyError as error:
            raise ValueError("Catálogo no soportado") from error
