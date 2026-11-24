import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector
from app.core.config import settings

def get_connection():
    conn = psycopg.connect(settings.database_url, row_factory=dict_row, connect_timeout=5)
    try:
        register_vector(conn)
        return conn
    except Exception:
        conn.close()
        raise

def check_database():
    with get_connection() as conn:
        return conn.execute('SELECT current_database() AS database, version() AS version').fetchone()
