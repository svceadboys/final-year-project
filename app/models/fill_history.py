from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database.session import Base


class BinFillHistory(Base):
    __tablename__ = "bin_fill_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bin_id = Column(Integer, ForeignKey("bins.bin_id"), nullable=False, index=True)
    fill_level = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    bin = relationship("Bin", backref="fill_history")

