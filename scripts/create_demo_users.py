from __future__ import annotations

import argparse
import os
import secrets
import string

from backend.app.config.settings import settings
from backend.app.database.connection import get_connection
from backend.app.security.encryption import AesGcmCipher
from backend.app.security.passwords import PasswordService


def generated_password() -> str:
    alphabet = string.ascii_letters + string.digits + "!@#_-"
    return "Demo-" + "".join(secrets.choice(alphabet) for _ in range(20))


def normalize(value: str) -> str:
    return value.strip().casefold()


def ensure_demo_position(database_url: str | None) -> tuple[int, int]:
    with get_connection(database_url) as connection:
        company = connection.execute(
            """INSERT INTO empresas (codigo,nombre,activo) VALUES ('DEMO','Empresa demo',TRUE)
            ON CONFLICT (codigo) DO UPDATE SET activo=TRUE RETURNING id"""
        ).fetchone()["id"]
        area = connection.execute(
            """INSERT INTO areas (codigo,nombre,activo,empresa_id) VALUES ('DEMO','Área demo',TRUE,%s)
            ON CONFLICT (empresa_id,codigo) DO UPDATE SET activo=TRUE RETURNING id""",
            (company,),
        ).fetchone()["id"]
        department = connection.execute(
            """INSERT INTO departamentos (codigo,nombre,activo,area_id) VALUES ('DEMO','Departamento demo',TRUE,%s)
            ON CONFLICT (area_id,codigo) DO UPDATE SET activo=TRUE RETURNING id""",
            (area,),
        ).fetchone()["id"]
        section = connection.execute(
            """INSERT INTO secciones (codigo,nombre,activo,departamento_id) VALUES ('DEMO','Sección demo',TRUE,%s)
            ON CONFLICT (departamento_id,codigo) DO UPDATE SET activo=TRUE RETURNING id""",
            (department,),
        ).fetchone()["id"]
        position = connection.execute(
            """INSERT INTO puestos (codigo,nombre,activo,seccion_id) VALUES ('DEMO','Puesto demo',TRUE,%s)
            ON CONFLICT (seccion_id,codigo) DO UPDATE SET activo=TRUE RETURNING id""",
            (section,),
        ).fetchone()["id"]
    return int(position), int(section)


def upsert_demo_user(
    username: str,
    email: str,
    password: str,
    role: str,
    puesto_id: int,
    password_service: PasswordService,
    cipher: AesGcmCipher,
    database_url: str | None,
) -> int:
    query = """INSERT INTO users
        (full_name, username, username_normalized, email, email_normalized, password_hash,
         profile_encrypted, is_admin, role, puesto_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (username_normalized) DO UPDATE SET
        email=EXCLUDED.email, email_normalized=EXCLUDED.email_normalized,
        password_hash=EXCLUDED.password_hash, profile_encrypted=EXCLUDED.profile_encrypted,
        full_name=EXCLUDED.full_name, is_admin=EXCLUDED.is_admin, role=EXCLUDED.role,
        puesto_id=EXCLUDED.puesto_id, is_active=TRUE, updated_at=CURRENT_TIMESTAMP
        RETURNING id"""
    values = (
        username, username, normalize(username), email, normalize(email), password_service.hash(password),
        cipher.encrypt_json({"display_name": username, "phone": ""}), role == "administrador", role, puesto_id,
    )
    with get_connection(database_url) as connection:
        user_id = connection.execute(query, values).fetchone()["id"]
        connection.execute("UPDATE user_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE user_id=%s", (user_id,))
    return int(user_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea o actualiza cuentas locales de demostración.")
    parser.add_argument("--admin-password", default="")
    parser.add_argument("--consulta-password", default="")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    args = parser.parse_args()
    admin_password = args.admin_password or generated_password()
    consulta_password = args.consulta_password or generated_password()
    password_service = PasswordService()
    cipher = AesGcmCipher(settings.app_encryption_key)
    puesto_id, section_id = ensure_demo_position(args.database_url)
    admin_id = upsert_demo_user("demo-admin", "demo-admin@local.test", admin_password, "administrador", puesto_id, password_service, cipher, args.database_url)
    consulta_id = upsert_demo_user("demo-consulta", "demo-consulta@local.test", consulta_password, "consulta", puesto_id, password_service, cipher, args.database_url)
    with get_connection(args.database_url) as connection:
        demo_users = [admin_id, consulta_id, admin_id]
        services = connection.execute("SELECT id FROM services ORDER BY code LIMIT 3").fetchall()
        for row, user_id in zip(services, demo_users):
            connection.execute(
                "UPDATE services SET responsible_section_id=%s, responsible_user_id=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                (section_id, user_id, row["id"]),
            )
        if len(services) < 3:
            raise SystemExit("Se requieren al menos tres servicios importados para crear asignaciones demo.")
    print("Cuentas demo configuradas localmente. No guardes estas credenciales en Git.")
    print(f"administrador: username=demo-admin email=demo-admin@local.test password={admin_password} id={admin_id}")
    print(f"consulta: username=demo-consulta email=demo-consulta@local.test password={consulta_password} id={consulta_id}")


if __name__ == "__main__":
    main()
