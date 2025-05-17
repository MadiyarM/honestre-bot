# db.py
import os
import json
import psycopg2
from psycopg2.extras import Json

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def save_review(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reviews (data) VALUES (%s)",
        (Json(data),)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_reviews_by_complex(name: str) -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT data FROM reviews WHERE data->>'complex_name' = %s ORDER BY created_at DESC",
        (name,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]
