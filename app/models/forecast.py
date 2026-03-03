from datetime import datetime

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship

from app.database.session import Base


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bin_id = Column(Integer, ForeignKey("bins.bin_id"), nullable=False, index=True)
    predicted_fill = Column(Float, nullable=False)
    predicted_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    bin = relationship("Bin", backref="forecasts")

