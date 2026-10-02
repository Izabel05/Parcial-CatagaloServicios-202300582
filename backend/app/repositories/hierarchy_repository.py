from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.database.connection import get_connection


class HierarchyNotFoundError(Exception):
    """La entidad o el padre solicitado no existe."""


class HierarchyDependencyError(Exception):
    """La operación violaría la jerarquía o la política de bajas lógicas."""


@dataclass(frozen=True, slots=True)
class EntityDefinition:
    table: str
    parent_table: str | None = None
    parent_column: str | None = None

    @property
    def parent_alias(self) -> str | None:
        return self.parent_column


EMPRESA = EntityDefinition("empresas")
AREA = EntityDefinition("areas", "empresas", "empresa_id")
DEPARTAMENTO = EntityDefinition("departamentos", "areas", "area_id")
SECCION = EntityDefinition("secciones", "departamentos", "departamento_id")
PUESTO = EntityDefinition("puestos", "secciones", "seccion_id")

DEFINITIONS = {
    "empresas": EMPRESA,
    "areas": AREA,
    "departamentos": DEPARTAMENTO,
    "secciones": SECCION,
    "puestos": PUESTO,
}

CHILDREN = {
    "empresas": ("areas", "empresa_id"),
    "areas": ("departamentos", "area_id"),
    "departamentos": ("secciones", "departamento_id"),
    "secciones": ("puestos", "seccion_id"),
}


class HierarchyRepository:
    def list(self, definition: EntityDefinition, parent_id: int | None = None) -> list[dict[str, Any]]:
        parent_select = f", {definition.parent_column}" if definition.parent_column else ""
        where = f" WHERE {definition.parent_column}=%s" if parent_id is not None and definition.parent_column else ""
        params = (parent_id,) if where else ()
        query = f"""SELECT id, codigo, nombre, activo{parent_select}, created_at
            FROM {definition.table}{where} ORDER BY codigo"""
        with get_connection() as connection:
            return [dict(row) for row in connection.execute(query, params).fetchall()]

    def get(self, definition: EntityDefinition, entity_id: int) -> dict[str, Any] | None:
        parent_select = f", {definition.parent_column}" if definition.parent_column else ""
        query = f"""SELECT id, codigo, nombre, activo{parent_select}, created_at
            FROM {definition.table} WHERE id=%s"""
        with get_connection() as connection:
            row = connection.execute(query, (entity_id,)).fetchone()
        return dict(row) if row else None

    def create(
        self,
        definition: EntityDefinition,
        code: str,
        name: str,
        parent_id: int | None,
        active: bool,
    ) -> dict[str, Any]:
        parent_select = f", {definition.parent_column}" if definition.parent_column else ""
        returning = f"id, codigo, nombre, activo{parent_select}, created_at"
        with get_connection() as connection:
            if definition.parent_column and definition.parent_table:
                row = connection.execute(
                    f"""INSERT INTO {definition.table} (codigo, nombre, activo, {definition.parent_column})
                    SELECT %s, %s, %s, id FROM {definition.parent_table}
                    WHERE id=%s AND activo RETURNING {returning}""",
                    (code, name, active, parent_id),
                ).fetchone()
                if row is None:
                    raise HierarchyDependencyError("El padre no existe o está inactivo")
            else:
                row = connection.execute(
                    f"""INSERT INTO {definition.table} (codigo, nombre, activo)
                    VALUES (%s, %s, %s) RETURNING {returning}""",
                    (code, name, active),
                ).fetchone()
        return dict(row)

    def update(
        self,
        definition: EntityDefinition,
        entity_id: int,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        parent_column = definition.parent_column
        parent_id = values.get(parent_column) if parent_column else None
        with get_connection() as connection:
            current = connection.execute(
                f"SELECT id, activo{', ' + parent_column if parent_column else ''} FROM {definition.table} WHERE id=%s FOR UPDATE",
                (entity_id,),
            ).fetchone()
            if current is None:
                raise HierarchyNotFoundError("Registro no encontrado")

            target_parent = parent_id if parent_id is not None else (current[parent_column] if parent_column else None)
            if parent_column and (parent_id is not None or values.get("activo") is True):
                self._ensure_parent_active(connection, definition, target_parent)
            if values.get("activo") is False and current["activo"]:
                self._ensure_can_deactivate(connection, definition, entity_id)

            assignments = ["codigo=COALESCE(%s,codigo)", "nombre=COALESCE(%s,nombre)", "activo=COALESCE(%s,activo)"]
            params: list[Any] = [values.get("codigo"), values.get("nombre"), values.get("activo")]
            if parent_column:
                assignments.append(f"{parent_column}=COALESCE(%s,{parent_column})")
                params.append(parent_id)
            assignments.append("updated_at=CURRENT_TIMESTAMP")
            parent_select = f", {parent_column}" if parent_column else ""
            row = connection.execute(
                f"""UPDATE {definition.table} SET {', '.join(assignments)}
                WHERE id=%s RETURNING id, codigo, nombre, activo{parent_select}, created_at""",
                (*params, entity_id),
            ).fetchone()
        return dict(row)

    def ensure_active_position(self, position_id: int) -> None:
        with get_connection() as connection:
            row = connection.execute(
                """SELECT p.id FROM puestos p
                JOIN secciones s ON s.id=p.seccion_id AND s.activo
                JOIN departamentos d ON d.id=s.departamento_id AND d.activo
                JOIN areas a ON a.id=d.area_id AND a.activo
                JOIN empresas e ON e.id=a.empresa_id AND e.activo
                WHERE p.id=%s AND p.activo""",
                (position_id,),
            ).fetchone()
        if row is None:
            raise HierarchyDependencyError("El puesto no existe o su jerarquía está inactiva")

    def active_position_section(self, position_id: int) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """SELECT p.seccion_id FROM puestos p
                JOIN secciones s ON s.id=p.seccion_id AND s.activo
                JOIN departamentos d ON d.id=s.departamento_id AND d.activo
                JOIN areas a ON a.id=d.area_id AND a.activo
                JOIN empresas e ON e.id=a.empresa_id AND e.activo
                WHERE p.id=%s AND p.activo""",
                (position_id,),
            ).fetchone()
        if row is None:
            raise HierarchyDependencyError("El puesto no existe o su jerarquía está inactiva")
        return int(row["seccion_id"])

    @staticmethod
    def _ensure_parent_active(connection: Any, definition: EntityDefinition, parent_id: int | None) -> None:
        if parent_id is None:
            raise HierarchyDependencyError("La relación con el padre es obligatoria")
        row = connection.execute(
            f"SELECT id FROM {definition.parent_table} WHERE id=%s AND activo",
            (parent_id,),
        ).fetchone()
        if row is None:
            raise HierarchyDependencyError("El padre no existe o está inactivo")

    @staticmethod
    def _ensure_can_deactivate(connection: Any, definition: EntityDefinition, entity_id: int) -> None:
        child = CHILDREN.get(definition.table)
        if child:
            child_table, child_column = child
            row = connection.execute(
                f"SELECT 1 FROM {child_table} WHERE {child_column}=%s AND activo LIMIT 1",
                (entity_id,),
            ).fetchone()
            if row:
                raise HierarchyDependencyError("Desactive primero las entidades hijas activas")
        if definition.table == "puestos":
            row = connection.execute(
                "SELECT 1 FROM users WHERE puesto_id=%s AND is_active LIMIT 1",
                (entity_id,),
            ).fetchone()
            if row:
                raise HierarchyDependencyError("El puesto tiene usuarios activos; desactívelos primero")
