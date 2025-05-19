import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

load_dotenv()

# ────────── Пост‑обработка строки подключения ──────────
DATABASE_URL: str | None = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Переменная окружения DATABASE_URL не задана")

# Heroku‑стиль "postgres://" → правильный dialect драйвер
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL:
    # "postgresql://" → "postgresql+asyncpg://"
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# ────────── Engine / Session ──────────
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

# ────────── CRUD утилиты (как раньше) ──────────
from typing import List, Any

async def init_db() -> None:
    from models import Review
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def save_review(answers: dict[str, Any]) -> None:
    from models import Review
    async with async_session() as session:
        session.add(Review(**answers))
        await session.commit()

async def get_reviews_by_complex(complex_name: str) -> List["Review"]:
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