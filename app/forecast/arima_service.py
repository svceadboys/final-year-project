from datetime import date, datetime, timedelta
from typing import List, Dict

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from statsmodels.tsa.arima.model import ARIMA

from app.models import BinFillHistory, Forecast, Bin


def get_fill_history(db: Session, bin_id: int, min_points: int = 10) -> pd.Series:
    """Return time series of fill levels for a bin, indexed by timestamp."""
    records: List[BinFillHistory] = (
        db.query(BinFillHistory)
        .filter(BinFillHistory.bin_id == bin_id)
        .order_by(BinFillHistory.timestamp.asc())
        .all()
    )
    if len(records) < min_points:
        raise ValueError("Not enough historical points for ARIMA forecasting.")

    ts = pd.Series(
        [r.fill_level for r in records],
        index=pd.to_datetime([r.timestamp for r in records]),
        name="fill_level",
    )
    ts = ts.asfreq("D").interpolate()
    return ts


def forecast_bin_fill(
    db: Session,
    bin_id: int,
    days_ahead: int = 7,
    arima_order: tuple = (1, 1, 1),
) -> List[Forecast]:
    ts = get_fill_history(db, bin_id)

    model = ARIMA(ts, order=arima_order)
    model_fit = model.fit()
    forecast_res = model_fit.forecast(steps=days_ahead)

    today = date.today()
    forecasts: List[Forecast] = []
    for i, value in enumerate(forecast_res):
        pred_date = today + timedelta(days=i + 1)
        predicted_fill = float(max(0.0, min(100.0, value)))
        forecasts.append(
            Forecast(
                bin_id=bin_id,
                predicted_fill=predicted_fill,
                predicted_date=pred_date,
            )
        )

    # Remove existing future forecasts for this bin before inserting new ones
    db.query(Forecast).filter(
        Forecast.bin_id == bin_id, Forecast.predicted_date >= today
    ).delete(synchronize_session=False)

    db.add_all(forecasts)
    db.commit()

    db.refresh(forecasts[0])
    return forecasts


def compute_overflow_date(
    forecasts: List[Forecast], threshold: float = 100.0
) -> date | None:
    for f in forecasts:
        if f.predicted_fill >= threshold:
            return f.predicted_date
    return None

