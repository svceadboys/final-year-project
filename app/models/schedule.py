from datetime import datetime

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.database.session import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    truck_id = Column(String(50), nullable=False)
    bin_id = Column(Integer, ForeignKey("bins.bin_id"), nullable=False, index=True)
    priority_score = Column(Float, nullable=False)
    route_order = Column(Integer, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    bin = relationship("Bin", backref="schedules")

