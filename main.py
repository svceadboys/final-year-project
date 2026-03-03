from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.routes import classification, forecast, scheduler, bins
from app.routes import records
from app.database.session import get_db
from app.models import Bin, Classification, Forecast as ForecastModel
from datetime import date


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Smart Waste Management API",
        version="1.0.0",
        description="Admin-only backend for AI-based Smart Waste Management System",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(classification.router, prefix="/api/classification", tags=["Classification"])
    app.include_router(forecast.router,       prefix="/api/forecast",       tags=["Forecast"])
    app.include_router(scheduler.router,      prefix="/api/scheduler",      tags=["Scheduler"])
    app.include_router(bins.router,           prefix="/api/bins",           tags=["Bins"])
    app.include_router(records.router,        prefix="/api/records",        tags=["Records"])

    @app.get("/api/dashboard/summary", tags=["Dashboard"])
    def dashboard_summary(db: Session = Depends(get_db)):
        """Aggregate stats for the admin dashboard."""
        all_bins = db.query(Bin).all()
        total_bins = len(all_bins)
        avg_fill = round(
            sum(b.current_fill for b in all_bins) / total_bins, 1
        ) if total_bins else 0

        bins_above_80 = sum(1 for b in all_bins if b.current_fill >= 80)

        # Classifications in last 24h
        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(hours=24)
        recent_count = (
            db.query(func.count(Classification.id))
            .filter(Classification.timestamp >= since)
            .scalar()
        )

        # Waste type distribution
        type_rows = (
            db.query(Classification.waste_type, func.count(Classification.id).label("cnt"))
            .group_by(Classification.waste_type)
            .all()
        )
        waste_distribution = {row.waste_type: row.cnt for row in type_rows}

        # Bins fill levels list
        bin_fill_levels = [
            {"bin_id": b.bin_id, "location": b.location, "current_fill": b.current_fill}
            for b in all_bins
        ]

        # Next overflow (nearest forecast >= 100)
        overflow = (
            db.query(ForecastModel)
            .filter(
                ForecastModel.predicted_fill >= 100,
                ForecastModel.predicted_date >= date.today(),
            )
            .order_by(ForecastModel.predicted_date.asc())
            .first()
        )

        return {
            "total_bins": total_bins,
            "avg_fill_level": avg_fill,
            "bins_need_collection": bins_above_80,
            "classifications_today": recent_count,
            "waste_distribution": waste_distribution,
            "bin_fill_levels": bin_fill_levels,
            "next_overflow": {
                "bin_id": overflow.bin_id,
                "predicted_date": str(overflow.predicted_date),
                "predicted_fill": overflow.predicted_fill,
            } if overflow else None,
        }

    # ── Root redirect ──────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/index.html")

    # ── Serve frontend as static files (MUST be last) ──────────────────────
    frontend_dir = Path(__file__).resolve().parent / "frontend"
    if frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    return app


app = create_app()
