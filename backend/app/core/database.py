import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector

load_dotenv()


def get_connection():
    url = os.getenv("DATABASE_URL")

    if not url:
        raise RuntimeError("DATABASE_URL is not configured")

    conn = psycopg.connect(
        url,
        row_factory=dict_row,
        connect_timeout=5
    )

    try:
        register_vector(conn)
        return conn

    except Exception:
        conn.close()
        raise


def check_database():
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT current_database() AS database, "
            "version() AS version"
        )

        return cursor.fetchone()
