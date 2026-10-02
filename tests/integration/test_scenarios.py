from __future__ import annotations

import base64
import os
import unittest
from pathlib import Path

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
if TEST_DATABASE_URL:
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("APP_ENCRYPTION_KEY", base64.urlsafe_b64encode(bytes(range(32))).decode())

try:
    import psycopg
    from fastapi.testclient import TestClient
    from psycopg.rows import dict_row

    from backend.app.config.settings import settings
    from backend.app.importer.catalog_importer import execute_schema, parse_workbook, run_import
    from backend.app.main import app
    from backend.app.security.encryption import AesGcmCipher
    from backend.app.security.passwords import PasswordService

    INTEGRATION_AVAILABLE = True
except ModuleNotFoundError:
    INTEGRATION_AVAILABLE = False


@unittest.skipUnless(
    INTEGRATION_AVAILABLE and TEST_DATABASE_URL,
    "Requiere dependencias backend y TEST_DATABASE_URL apuntando a una base de pruebas aislada",
)
class ScenarioIntegrationTest(unittest.TestCase):
    """Cubre P01-P11 con una base exclusiva de pruebas; no toca el volumen de evaluación."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._reset_test_database()
        cls._seed_hierarchy_and_users()
        cls.first_import = run_import(cls._source_file(), "Servicios Externos", TEST_DATABASE_URL)
        cls.second_import = run_import(cls._source_file(), "Servicios Externos", TEST_DATABASE_URL)
        cls.client = TestClient(app)

    @classmethod
    def _source_file(cls) -> Path:
        return Path(__file__).resolve().parents[2] / "data" / "CatalogoServicios.xlsx"

    @classmethod
    def _reset_test_database(cls) -> None:
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute("DROP SCHEMA public CASCADE")
            connection.execute("CREATE SCHEMA public")
        with psycopg.connect(TEST_DATABASE_URL, row_factory=dict_row) as connection:
            with connection.transaction():
                execute_schema(connection)

    @classmethod
    def _seed_hierarchy_and_users(cls) -> None:
        with psycopg.connect(TEST_DATABASE_URL, row_factory=dict_row) as connection:
            with connection.transaction():
                company = connection.execute(
                    "INSERT INTO empresas (codigo,nombre) VALUES ('TEST','Empresa de pruebas') RETURNING id"
                ).fetchone()["id"]
                area = connection.execute(
                    "INSERT INTO areas (codigo,nombre,empresa_id) VALUES ('TEST','Área de pruebas',%s) RETURNING id",
                    (company,),
                ).fetchone()["id"]
                department = connection.execute(
                    "INSERT INTO departamentos (codigo,nombre,area_id) VALUES ('TEST','Departamento de pruebas',%s) RETURNING id",
                    (area,),
                ).fetchone()["id"]
                section = connection.execute(
                    "INSERT INTO secciones (codigo,nombre,departamento_id) VALUES ('TEST','Sección de pruebas',%s) RETURNING id",
                    (department,),
                ).fetchone()["id"]
                position = connection.execute(
                    "INSERT INTO puestos (codigo,nombre,seccion_id) VALUES ('TEST','Puesto de pruebas',%s) RETURNING id",
                    (section,),
                ).fetchone()["id"]
                cls.test_section = int(section)
                cls.test_position = int(position)
                passwords = PasswordService()
                cipher = AesGcmCipher(settings.app_encryption_key)
                for username, email, role, password in (
                    ("integration-admin", "integration-admin@test.local", "administrador", "Admin-Test-12345"),
                    ("integration-consulta", "integration-consulta@test.local", "consulta", "Consulta-Test-12345"),
                    ("integration-inactive", "integration-inactive@test.local", "consulta", "Inactive-Test-12345"),
                ):
                    row = connection.execute(
                        """INSERT INTO users
                        (full_name,username,username_normalized,email,email_normalized,password_hash,profile_encrypted,is_admin,role,puesto_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (username, username, username.casefold(), email, email.casefold(), passwords.hash(password),
                         cipher.encrypt_json({"display_name": username}), role == "administrador", role, position),
                    ).fetchone()
                    setattr(cls, f"{username.replace('-', '_')}_id", int(row["id"]))

    def auth(self, username: str, password: str) -> dict[str, str]:
        response = self.client.post("/api/v1/auth/login", json={"identifier": username, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_P01_to_P11_auth_hierarchy_catalog_and_import(self) -> None:
        # P01: credencial válida e inválida.
        valid = self.client.post("/api/v1/auth/login", json={"identifier": "integration-admin", "password": "Admin-Test-12345"})
        self.assertEqual(valid.status_code, 200)
        invalid = self.client.post("/api/v1/auth/login", json={"identifier": "integration-admin", "password": "incorrecta"})
        self.assertEqual(invalid.status_code, 401)
        admin_headers = {"Authorization": f"Bearer {valid.json()['access_token']}"}

        # P02: sin sesión, logout y usuario inactivo.
        self.assertEqual(self.client.get("/api/v1/services").status_code, 401)
        inactive = self.auth("integration-inactive", "Inactive-Test-12345")
        self.assertEqual(self.client.post("/api/v1/auth/logout", headers=inactive).status_code, 204)
        self.assertEqual(self.client.get("/api/v1/services", headers=inactive).status_code, 401)
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            connection.execute("UPDATE users SET is_active=FALSE WHERE username=%s", ("integration-inactive",))
        self.assertEqual(self.client.post("/api/v1/auth/login", json={"identifier": "integration-inactive", "password": "Inactive-Test-12345"}).status_code, 401)

        # P03: consulta puede leer, pero no escribir.
        consulta_headers = self.auth("integration-consulta", "Consulta-Test-12345")
        self.assertEqual(self.client.get("/api/v1/services?page_size=2", headers=consulta_headers).status_code, 200)
        self.assertEqual(self.client.post("/api/v1/empresas", headers=consulta_headers, json={"codigo": "NO", "nombre": "No permitido"}).status_code, 403)

        # P04: crear jerarquía y asignar usuario.
        company = self.client.post("/api/v1/empresas", headers=admin_headers, json={"codigo": "P04", "nombre": "Empresa P04"}).json()
        area = self.client.post("/api/v1/areas", headers=admin_headers, json={"codigo": "P04", "nombre": "Área P04", "empresa_id": company["id"]}).json()
        department = self.client.post("/api/v1/departamentos", headers=admin_headers, json={"codigo": "P04", "nombre": "Departamento P04", "area_id": area["id"]}).json()
        section = self.client.post("/api/v1/secciones", headers=admin_headers, json={"codigo": "P04", "nombre": "Sección P04", "departamento_id": department["id"]}).json()
        position = self.client.post("/api/v1/puestos", headers=admin_headers, json={"codigo": "P04", "nombre": "Puesto P04", "seccion_id": section["id"]}).json()
        created_user = self.client.post("/api/v1/usuarios", headers=admin_headers, json={
            "name": "Usuario P04", "username": "p04-user", "email": "p04-user@test.local",
            "password": "P04-User-Test-123", "role": "consulta", "puesto_id": position["id"],
        })
        self.assertEqual(created_user.status_code, 201, created_user.text)
        self.assertEqual(self.client.get(f"/api/v1/usuarios/{created_user.json()['id']}", headers=consulta_headers).json()["puesto_id"], position["id"])

        # P05: duplicados y referencias inexistentes.
        duplicate = self.client.post("/api/v1/empresas", headers=admin_headers, json={"codigo": "P04", "nombre": "Duplicada"})
        self.assertEqual(duplicate.status_code, 409)
        missing_parent = self.client.post("/api/v1/areas", headers=admin_headers, json={"codigo": "X", "nombre": "Huérfana", "empresa_id": 999999})
        self.assertEqual(missing_parent.status_code, 409)

        # P06/P07: controles de importación e idempotencia.
        self.assertEqual((self.first_import["level_1"], self.first_import["level_2"]), (12, 46))
        self.assertEqual(self.second_import["created"], 0)
        self.assertEqual(self.second_import["unchanged"], 46)

        # P08: conflicto SE.12, códigos y ausencias.
        levels, services, observations, _ = parse_workbook(self._source_file(), "Servicios Externos")
        self.assertEqual(levels["SE.12"]["name"], "Suministrar Analitica")
        self.assertEqual(levels["SE.12"]["name_variants"], ["Suministrar Analitica", "Mantener Tableros de Control"])
        self.assertEqual([s["code"] for s in services if s["code"].startswith("SE.12.")], ["SE.12.1", "SE.12.2", "SE.12.3"])
        self.assertTrue(any(item.reason == "INCOMPLETE_ATTRIBUTES" for item in observations))

        options = self.client.get("/api/v1/services/catalog-options", headers=admin_headers).json()
        level_1 = self.client.get("/api/v1/services/level-1", headers=admin_headers).json()[0]["code"]
        class_id = options["service_classes"][0]["id"]
        criticality_id = options["criticalities"][0]["id"]
        type_id = options["service_types"][0]["id"]

        # P09: mínimo mayor que máximo al crear y editar.
        invalid_create = self.client.post("/api/v1/services", headers=admin_headers, json={
            "code": "P09-BAD", "level_1_code": level_1, "name": "Inválido", "service_class_id": class_id,
            "criticality_id": criticality_id, "service_type_id": type_id, "responsible_section_id": section["id"],
            "minimum": 10, "maximum": 1,
        })
        self.assertEqual(invalid_create.status_code, 422)
        valid_service = self.client.post("/api/v1/services", headers=admin_headers, json={
            "code": "P09-OK", "level_1_code": level_1, "name": "Servicio P09", "service_class_id": class_id,
            "criticality_id": criticality_id, "service_type_id": type_id, "responsible_section_id": section["id"],
            "minimum": 1, "maximum": 10,
        })
        self.assertEqual(valid_service.status_code, 201, valid_service.text)
        invalid_update = self.client.patch("/api/v1/services/P09-OK", headers=admin_headers, json={"minimum": 20})
        self.assertEqual(invalid_update.status_code, 409)

        # P10: búsqueda, filtro y paginación.
        filtered = self.client.get("/api/v1/services", headers=consulta_headers, params={"search": "SE.12", "level_1_code": "SE.12", "page_size": 2})
        self.assertEqual(filtered.status_code, 200)
        self.assertLessEqual(len(filtered.json()["items"]), 2)
        self.assertGreaterEqual(filtered.json()["total"], 3)
        self.assertTrue(all(item["level_1_code"] == "SE.12" for item in filtered.json()["items"]))

        # P11: usuario de otra sección no puede ser responsable.
        department_b = self.client.post("/api/v1/departamentos", headers=admin_headers, json={"codigo": "B", "nombre": "Departamento B", "area_id": area["id"]}).json()
        section_b = self.client.post("/api/v1/secciones", headers=admin_headers, json={"codigo": "B", "nombre": "Sección B", "departamento_id": department_b["id"]}).json()
        position_b = self.client.post("/api/v1/puestos", headers=admin_headers, json={"codigo": "B", "nombre": "Puesto B", "seccion_id": section_b["id"]}).json()
        user_b = self.client.post("/api/v1/usuarios", headers=admin_headers, json={
            "name": "Usuario B", "username": "user-b", "email": "user-b@test.local", "password": "User-B-Test-123",
            "role": "consulta", "puesto_id": position_b["id"],
        }).json()
        wrong_assignment = self.client.post("/api/v1/services", headers=admin_headers, json={
            "code": "P11-BAD", "level_1_code": level_1, "name": "Asignación inválida", "service_class_id": class_id,
            "criticality_id": criticality_id, "service_type_id": type_id, "responsible_section_id": section["id"],
            "responsible_user_id": user_b["id"],
        })
        self.assertEqual(wrong_assignment.status_code, 409)


if __name__ == "__main__":
    unittest.main()
