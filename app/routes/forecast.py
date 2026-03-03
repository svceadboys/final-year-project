from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.forecast.arima_service import forecast_bin_fill, compute_overflow_date
from app.models import Forecast
from app.schemas.forecast import ForecastRead, ForecastResponse


router = APIRouter()


@router.post(
    "/run/{bin_id}",
    response_model=ForecastResponse,
    summary="Run ARIMA forecast for a bin",
)
def run_forecast_for_bin(
    bin_id: int,
    db: Session = Depends(get_db),
):
    try:
        forecasts = forecast_bin_fill(db, bin_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    overflow_date = compute_overflow_date(forecasts)
    return ForecastResponse(
        bin_id=bin_id,
        forecasts=forecasts,
        overflow_date=overflow_date,
    )


@router.get(
    "/{bin_id}",
    response_model=ForecastResponse,
    summary="Get latest forecast for a bin",
)
def get_forecast_for_bin(
    bin_id: int,
    db: Session = Depends(get_db),
):
    forecasts: List[Forecast] = (
        db.query(Forecast)
        .filter(Forecast.bin_id == bin_id)
        .order_by(Forecast.predicted_date.asc())
        .all()
    )
    if not forecasts:
        raise HTTPException(status_code=404, detail="No forecast data for this bin")

    overflow_date = compute_overflow_date(forecasts)
    return ForecastResponse(
        bin_id=bin_id,
        forecasts=forecasts,
        overflow_date=overflow_date,
    )

