import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings


def get_connection():
    return psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=RealDictCursor
    )


def test_connection() -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 AS ok;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result["ok"] == 1
    except Exception as e:
        print(f"Error de conexión a PostgreSQL: {e}")
        return False