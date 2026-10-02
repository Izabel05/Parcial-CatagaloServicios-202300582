from __future__ import annotations

import argparse
import getpass
import os
from typing import Any

from backend.app.config.settings import settings
from backend.app.database.connection import get_connection
from backend.app.security.encryption import AesGcmCipher
from backend.app.security.passwords import PasswordService


def normalize(value: str) -> str:
    return value.strip().casefold()


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea un usuario local para el catálogo.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--phone", default="")
    parser.add_argument("--role", choices=("administrador", "consulta"), default="consulta")
    parser.add_argument("--puesto-id", required=True, type=int)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    args = parser.parse_args()

    password = getpass.getpass("Contraseña: ")
    confirmation = getpass.getpass("Confirmar contraseña: ")
    if password != confirmation:
        raise SystemExit("Las contraseñas no coinciden.")
    if len(password) < 10:
        raise SystemExit("La contraseña debe tener al menos 10 caracteres.")

    password_service = PasswordService()
    cipher = AesGcmCipher(settings.app_encryption_key)
    profile: dict[str, Any] = {"display_name": args.display_name, "phone": args.phone}
    query = """INSERT INTO users
        (full_name, username, username_normalized, email, email_normalized, password_hash,
         profile_encrypted, is_admin, role, puesto_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id"""
    values = (
        args.display_name.strip(), args.username.strip(), normalize(args.username), args.email.strip(),
        normalize(args.email), password_service.hash(password), cipher.encrypt_json(profile),
        args.role == "administrador", args.role, args.puesto_id,
    )
    with get_connection(args.database_url) as connection:
        user_id = connection.execute(query, values).fetchone()["id"]
    print(f"Usuario creado: id={user_id}, username={args.username.strip()}")


if __name__ == "__main__":
    main()
