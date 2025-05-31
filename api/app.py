from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict

from db import async_session          # ← импорт существующего Session
from models import Review

app = FastAPI(title="HonestRE Mini-app API")

# ───── Dependency ─────
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# ───── Health check ─────
@app.get("/ping")
async def ping():
    return {"ok": True}

# ───── /complexes ─────
@app.get("/complexes")
async def complexes(
    query: str = Query(..., min_length=3, max_length=100),
    session: AsyncSession = Depends(get_session)
) -> List[Dict]:
    # pg_trgm similarity + ILIKE fallback
    stmt = (
        select(
            Review.id.label("id"),
            Review.city.label("city"),
            Review.complex_name.label("name"),
            func.max(Review.id).label("max_id")   # для группировки
        )
        .where(Review.complex_name.ilike(f"%{query}%"))
        .group_by(Review.id, Review.city, Review.complex_name)
        .order_by(func.similarity(Review.complex_name, query).desc())
        .limit(20)
    )
    result = await session.execute(stmt)
    return [row._asdict() for row in result]

# ───── /reviews ─────
@app.get("/reviews")
async def reviews(
    complex_id: int | None = None,
    name: str | None = None,
    session: AsyncSession = Depends(get_session)
) -> List[Dict]:
    if not complex_id and not name:
        raise HTTPException(status_code=400, detail="complex_id or name required")

    stmt = select(Review)
    if complex_id:
        stmt = stmt.where(Review.id == complex_id)
    else:
        stmt = stmt.where(Review.complex_name.ilike(f"%{name}%"))

    result = await session.execute(stmt)
    reviews = result.scalars().all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "city": r.city,
            "complex_name": r.complex_name,
            "status": r.status,
            "heating": r.heating,
            "electricity": r.electricity,
            "gas": r.gas,
            "water": r.water,
            "noise": r.noise,
            "mgmt": r.mgmt,
            "rent_price": r.rent_price,
            "likes": r.likes,
            "annoy": r.annoy,
            "recommend": r.recommend,
            "created_at": r.created_at.isoformat()
        }
        for r in reviews
    ]

