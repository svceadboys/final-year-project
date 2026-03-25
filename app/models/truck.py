from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.session import Base


class Truck(Base):
    """
    Represents a garbage collection truck in the fleet.
    Available statuses: "idle", "en_route", "collecting"
    """
    __tablename__ = "trucks"

    truck_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="idle", nullable=False)
    
    # Mocking real-time GPS location
    current_lat = Column(Float, nullable=False, default=0.0)
    current_lng = Column(Float, nullable=False, default=0.0)
    
    # If the truck is currently assigned to a bin
    assigned_bin_id = Column(Integer, ForeignKey("bins.bin_id"), nullable=True)

    assigned_bin = relationship("Bin")
