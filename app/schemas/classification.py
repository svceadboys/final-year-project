from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ClassificationCreate(BaseModel):
    bin_id: int
    waste_type: str
    confidence: float


class ClassificationRead(ClassificationCreate):
    id: int
    predicted_fill: Optional[float] = None
    timestamp: datetime

    model_config = {"from_attributes": True}

