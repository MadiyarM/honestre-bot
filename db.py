import os
from typing import Any, List
from dotenv import load_dotenv
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

# ────────── DB init ──────────
async def init_db():
    from models import Review
    async with engine.begin() as conn:
        # ensure pg_trgm extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.create_all)

# ────────── CRUD helpers ──────────
async def save_review(answers: dict[str, Any]):
    from models import Review
    valid = {c.name for c in Review.__table__.columns}  # type: ignore
    filtered = {k: v for k, v in answers.items() if k in valid}
    async with async_session() as session:
        session.add(Review(**filtered))
        await session.commit()

async def get_reviews_by_complex_pg(query: str, *, similarity_threshold: float = 0.8, limit: int = 20):
    """Возвращает отзывы с похожим названием ЖК, используя trigram‑similarity."""
    from models import Review
    async with async_session() as session:
        stmt = (
            select(Review)
            .where(func.similarity(Review.complex_name, query) >= similarity_threshold)
            .order_by(func.similarity(Review.complex_name, query).desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars())
