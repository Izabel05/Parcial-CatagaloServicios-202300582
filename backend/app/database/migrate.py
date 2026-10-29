"""Migraciones aditivas, transaccionales y verificadas mediante checksum."""
import hashlib
from pathlib import Path

from backend.app.database.connection import get_connection


def migrate(database_url=None):
    applied = []
    with get_connection(database_url) as connection:
        connection.execute("SELECT pg_advisory_xact_lock(7200582)")
        connection.execute("""CREATE TABLE IF NOT EXISTS schema_migrations
            (nombre TEXT PRIMARY KEY, sha256 TEXT NOT NULL,
             aplicada_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        for path in sorted((Path(__file__).resolve().parents[2] / 'db' / 'migrations').glob('*.sql')):
            raw = path.read_bytes().replace(b'\r\n', b'\n')
            digest = hashlib.sha256(raw).hexdigest()
            row = connection.execute('SELECT sha256 FROM schema_migrations WHERE nombre=%s', (path.name,)).fetchone()
            if row:
                if row['sha256'] != digest:
                    raise RuntimeError(f'Migración aplicada modificada: {path.name}')
                continue
            connection.execute(raw.decode('utf-8'))
            connection.execute('INSERT INTO schema_migrations(nombre,sha256) VALUES (%s,%s)', (path.name, digest))
            applied.append(path.name)
    return applied


if __name__ == '__main__':
    print({'migraciones_aplicadas': migrate()})
