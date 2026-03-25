from typing import Optional
from pydantic import BaseModel


class TruckBase(BaseModel):
    status: str
    current_lat: float
    current_lng: float
    assigned_bin_id: Optional[int] = None


class TruckRead(TruckBase):
    truck_id: str

    model_config = {"from_attributes": True}


class DispatchResponse(BaseModel):
    dispatched_count: int
    messages: list[str]
