from sqlalchemy import (
    Column, Integer, BigInteger, String, SmallInteger, Text, DateTime, Boolean, func
)
from db import Base

class Review(Base):
    __tablename__ = "reviews"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(BigInteger, index=True)        # Telegram user ID (no PII)

    city         = Column(String(128), nullable=False)
    complex_name = Column(String(256), index=True, nullable=False)
    status       = Column(String(32), nullable=False)

    heating      = Column(SmallInteger)
    electricity  = Column(SmallInteger)
    gas          = Column(SmallInteger)
    water        = Column(SmallInteger)
    noise        = Column(SmallInteger)
    mgmt         = Column(SmallInteger)

    rent_price   = Column(String(64))
    likes        = Column(Text)
    annoy        = Column(Text)
    recommend    = Column(Boolean)

    created_at   = Column(DateTime(timezone=True), server_default=func.now())
