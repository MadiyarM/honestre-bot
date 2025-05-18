# db.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# подгружаем .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# открываем постоянное подключение
conn = psycopg2.connect(DATABASE_URL)


def save_review(answers: dict):
    """
    Сохраняем один отзыв в виде набора столбцов.
    Ключи answers должны совпадать с именами колонок.
    """
    columns = ", ".join(answers.keys())
    placeholders = ", ".join(f"%({k})s" for k in answers.keys())
    sql = (
        f"INSERT INTO reviews ({columns}) "
        f"VALUES ({placeholders})"
    )
    with conn:
        with conn.cursor() as cur:
            cur.execute(sql, answers)


def get_reviews_by_complex(complex_name: str) -> list[dict]:
    """
    Возвращает список отзывов по точному совпадению поля complex_name.
    Каждый отзыв — dict со всеми полями таблицы.
    """
    sql = """
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
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, (complex_name,))
        return cur.fetchall()
