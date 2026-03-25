from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BinBase(BaseModel):
    location: str
    lat: float = 0.0
    lng: float = 0.0
    capacity: float
    current_fill: float = 0.0
    last_collected: Optional[datetime] = None


class BinCreate(BinBase):
    pass


class BinRead(BinBase):
    bin_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

