from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class ForecastRead(BaseModel):
    id: int
    bin_id: int
    predicted_fill: float
    predicted_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class ForecastResponse(BaseModel):
    bin_id: int
    forecasts: List[ForecastRead]
    overflow_date: Optional[date]

