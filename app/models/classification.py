from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.session import Base


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bin_id = Column(Integer, ForeignKey("bins.bin_id"), nullable=False, index=True)
    waste_type = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    predicted_fill = Column(Float, nullable=True, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    bin = relationship("Bin", backref="classifications")

