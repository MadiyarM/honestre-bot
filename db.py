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


def get_reviews_by_complex(complex_name: str) -> list[dict]:
    """
    Возвращает список отзывов для переданного названия ЖК, упорядоченных по дате создания (DESC).
    Каждый отзыв возвращается как словарь (dict).
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT data FROM reviews WHERE data->>%s = %s ORDER BY created_at DESC",
                ('complex_name', complex_name)
            )
            rows = cur.fetchall()
        # Извлекаем чистые словари из результата
        return [row['data'] for row in rows]
    finally:
        conn.close()