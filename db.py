import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from typing import List

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# ────────── Engine / Session ──────────
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


# ────────── CRUD‑утилиты ──────────
async def init_db() -> None:
    """
    Создаёт таблицы при первом запуске.
    Вызывается из main.py.
    """
    # импорт здесь, чтобы избежать циклической зависимости
    from models import Review
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_review(answers: dict) -> None:
    """
    Асинхронно сохраняет отзыв; ключи answers
    1‑в‑1 соответствуют колонкам модели Review.
    """
    from models import Review
    async with async_session() as session:
        session.add(Review(**answers))
        await session.commit()


async def get_reviews_by_complex(complex_name: str) -> List["Review"]:
    """
    Возвращает все отзывы по названию ЖК
    (регистр не учитывается, ищем вхождение).
    """
    from models import Review
    from sqlalchemy import select
    async with async_session() as session:
        stmt = (
            select(Review)
            .where(Review.complex_name.ilike(f"%{complex_name}%"))
            .order_by(Review.id.desc())
        )
        res = await session.execute(stmt)
        return list(res.scalars())
