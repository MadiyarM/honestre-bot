import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import Any, List

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

# ────────── CRUD ──────────
async def init_db():
    from models import Review
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def save_review(answers: dict[str, Any]):
    """Сохраняем отзыв, игнорируя лишние ключи."""
    from models import Review
    valid_keys = {c.name for c in Review.__table__.columns}  # type: ignore
    filtered = {k: v for k, v in answers.items() if k in valid_keys}
    async with async_session() as session:
        session.add(Review(**filtered))
        await session.commit()

async def get_reviews_by_complex(name: str) -> List["Review"]:
    from models import Review
    from sqlalchemy import select
    async with async_session() as session:
        stmt = (
            select(Review)
            .where(Review.complex_name.ilike(f"%{name}%"))
            .order_by(Review.id.desc())
        )
        res = await session.execute(stmt)
        return list(res.scalars())
