import sqlite3
import json

DB_PATH = 'reviews.db'

# Инициализация таблицы
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    data TEXT NOT NULL
)
''')
conn.commit()
conn.close()


def save_review(data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO reviews (data) VALUES (?)', (json.dumps(data, ensure_ascii=False),))
    conn.commit()
    conn.close()

def get_reviews_by_complex(name: str) -> list:
    """Возвращает список словарей с данными отзывов для ЖК name."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT data FROM reviews WHERE json_extract(data, '$.complex_name') = ?",
        (name,)
    )
    rows = cursor.fetchall()
    conn.close()
    # Преобразуем JSON-строки обратно в dict
    return [json.loads(row[0]) for row in rows]
