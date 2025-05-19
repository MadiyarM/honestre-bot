from sqlalchemy import (
    Column, Integer, String, Boolean, SmallInteger, Text, DateTime, func
)
from db import Base

class Review(Base):
    __tablename__ = "reviews"

    id           = Column(Integer, primary_key=True)
    phone        = Column(String(32))
    city         = Column(String(128))
    complex_name = Column(String(256), index=True)
    status       = Column(String(32))

    heating      = Column(SmallInteger)
    electricity  = Column(SmallInteger)
    gas          = Column(SmallInteger)
    water        = Column(SmallInteger)
    noise        = Column(SmallInteger)
    mgmt         = Column(SmallInteger)

    rent_price   = Column(String(64))
    likes        = Column(Text)
    annoy        = Column(Text)
    recommend    = Column(Boolean, nullable=False)

    created_at   = Column(DateTime(timezone=True), server_default=func.now())
