from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.routes.classification import router as classification_router
from app.routes.forecast import router as forecast_router
from app.routes.scheduler import router as scheduler_router
from app.routes.bins import router as bins_router
from app.routes.fleet import router as fleet_router
from app.routes.auth import router as auth_router
from app.routes.records import router as records_router

from app.database.session import get_db, SessionLocal, engine
from app.database.session import Base

from app.models.bin import Bin
from app.models.classification import Classification
from app.models.forecast import Forecast as ForecastModel
from app.models.truck import Truck
from app.api.deps import get_current_admin
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

    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    
    app.include_router(classification_router, prefix="/api/classification", tags=["Classification"], dependencies=[Depends(get_current_admin)])
    app.include_router(forecast_router,       prefix="/api/forecast",       tags=["Forecast"], dependencies=[Depends(get_current_admin)])
    app.include_router(scheduler_router,      prefix="/api/scheduler",      tags=["Scheduler"], dependencies=[Depends(get_current_admin)])
    app.include_router(bins_router,           prefix="/api/bins",           tags=["Bins"], dependencies=[Depends(get_current_admin)])
    app.include_router(records_router,        prefix="/api/records",        tags=["Records"], dependencies=[Depends(get_current_admin)])
    app.include_router(fleet_router,          prefix="/api/fleet",          tags=["Fleet Management"], dependencies=[Depends(get_current_admin)])

    @app.on_event("startup")
    def startup_db_seed():
        """Ensure the SQLite DB is created and seeded with Chennai mock data if empty."""
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            if db.query(Bin).count() == 0:
                print("Seeding Bins...")
                bin_data = [
                    {"location": "Main Gate - Block A", "capacity": 100.0, "current_fill": 85.0, "lat": 13.0827, "lng": 80.2707},
                    {"location": "Cafeteria - Block B", "capacity": 150.0, "current_fill": 90.0, "lat": 13.0835, "lng": 80.2715},
                    {"location": "Library - Block C",   "capacity": 80.0,  "current_fill": 15.0, "lat": 13.0815, "lng": 80.2725},
                    {"location": "Hostel - Block D",    "capacity": 200.0, "current_fill": 95.0, "lat": 13.0845, "lng": 80.2690},
                    {"location": "Auditorium - Block E","capacity": 120.0, "current_fill": 45.0, "lat": 13.0820, "lng": 80.2680},
                ]
                for b in bin_data: db.add(Bin(**b))
                db.commit()
                
            current_trucks = db.query(Truck).count()
            if current_trucks < 24:
                print(f"Seeding {24 - current_trucks} additional Trucks in Chennai...")
                import random
                for i in range(current_trucks + 1, 25):
                    t = {
                        "truck_id": f"TRK-{i:03d}",
                        "status": "idle",
                        "current_lat": round(13.08 + (random.uniform(-0.03, 0.03)), 4),
                        "current_lng": round(80.27 + (random.uniform(-0.03, 0.03)), 4)
                    }
                    db.add(Truck(**t))
                db.commit()

    @app.get("/api/dashboard/summary", tags=["Dashboard"])
    def dashboard_summary(db: Session = Depends(get_db), current_admin: str = Depends(get_current_admin)):
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
