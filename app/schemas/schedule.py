from datetime import date, datetime
from typing import List

from pydantic import BaseModel


class ScheduleRead(BaseModel):
    id: int
    truck_id: str
    bin_id: int
    priority_score: float
    route_order: int
    scheduled_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleRequest(BaseModel):
    truck_id: str
    # Distance matrix represented as { "src_bin_id-dst_bin_id": distance }
    distance_matrix: dict[str, float]
    depot_bin_id: int | None = None


class ScheduleResponse(BaseModel):
    schedule: List[ScheduleRead]

