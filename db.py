# db.py
import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor

# Берём URL из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """
    Создаёт и возвращает новое подключение к базе данных.
    """
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def save_review(data: dict):
    """
    Сохраняет отзыв (словарь) в таблицу reviews, в колонку data JSONB.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO reviews (data) VALUES (%s)",
                (Json(data, ensure_ascii=False),)
            )
        conn.commit()
    finally:
        conn.close()


def get_reviews_by_complex(complex_name):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
              phone,
              city,
              complex_name,
              status,
              heating,
              electricity,
              gas,
              water,
              noise,
              mgmt,
              rent_price,
              likes,
              annoy,
              recommend
            FROM reviews
            WHERE complex_name = %s
        """, (complex_name,))
        return cur.fetchall()