import os

import psycopg
from psycopg.rows import dict_row

from backend.app.config.settings import settings


def get_connection(database_url: str | None = None) -> psycopg.Connection:
    return psycopg.connect(database_url or os.getenv("DATABASE_URL") or settings.database_url, row_factory=dict_row)
