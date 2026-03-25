from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database.session import Base


class Bin(Base):
    __tablename__ = "bins"

    bin_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    location = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False, default=0.0)
    lng = Column(Float, nullable=False, default=0.0)
    capacity = Column(Float, nullable=False)
    current_fill = Column(Float, nullable=False, default=0.0)
    last_collected = Column(DateTime, nullable=True, default=None)
    created_at = Column(DateTime, default=datetime.utcnow)

