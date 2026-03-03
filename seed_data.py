"""
seed_data.py
Populates the database with realistic mock data for demo/testing.

Usage:
    python seed_data.py
"""

import logging
import math
import random
from datetime import datetime, timedelta

from app.database.session import SessionLocal
from app.models import Bin, Classification, BinFillHistory, Forecast, Schedule

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

WASTE_TYPES = ["Organic", "Recyclable", "Hazardous", "Other"]

MOCK_BINS = [
    {"location": "Main Gate - Block A", "capacity": 100.0, "current_fill": 72.0},
    {"location": "Cafeteria - Block B", "capacity": 80.0,  "current_fill": 88.0},
    {"location": "Library - Block C",   "capacity": 60.0,  "current_fill": 45.0},
    {"location": "Sports Complex",      "capacity": 120.0, "current_fill": 91.0},
    {"location": "Admin Block - Gate",  "capacity": 100.0, "current_fill": 60.0},
]

SAMPLE_FILES = [
    "food_waste.png", "banana_peel.png", "paper.jpg", "bottle.jpg",
    "styrofoam.png", "leaves.jpg", "wrapper.png", "battery.jpg",
    "cardboard.png", "glass.jpg",
]


def seed(db) -> None:
    # ── Bins ──────────────────────────────────────────────────────────────────
    if db.query(Bin).count() == 0:
        log.info("Seeding bins...")
        now = datetime.utcnow()
        bins = []
        for i, b in enumerate(MOCK_BINS):
            last_collected = now - timedelta(days=random.randint(1, 10))
            obj = Bin(
                location=b["location"],
                capacity=b["capacity"],
                current_fill=b["current_fill"],
                last_collected=last_collected,
            )
            db.add(obj)
            bins.append(obj)
        db.flush()  # get auto-generated bin_ids
    else:
        log.info("Bins already exist – skipping.")

    bins = db.query(Bin).all()

    # ── Fill History (30 days per bin) ─────────────────────────────────────
    if db.query(BinFillHistory).count() == 0:
        log.info("Seeding fill history...")
        base_date = datetime.utcnow() - timedelta(days=30)
        for idx, b in enumerate(bins):
            base_fill = b.current_fill * 0.5
            for day in range(30):
                ts = base_date + timedelta(days=day)
                # Sine wave + noise for realistic variation
                fill = base_fill + 20 * math.sin(day * 0.4 + idx) + random.gauss(0, 3)
                fill = max(5.0, min(100.0, fill))
                record = BinFillHistory(bin_id=b.bin_id, fill_level=round(fill, 2), timestamp=ts)
                db.add(record)
    else:
        log.info("Fill history already exists – skipping.")

    # ── Classification Records ─────────────────────────────────────────────
    if db.query(Classification).count() == 0:
        log.info("Seeding classification records...")
        base_date = datetime.utcnow() - timedelta(days=30)
        type_cycle = ["Recyclable", "Recyclable", "Organic", "Organic",
                      "Hazardous", "Other", "Recyclable", "Organic",
                      "Recyclable", "Other"]
        for i, waste_type in enumerate(type_cycle):
            b = bins[i % len(bins)]
            ts = base_date + timedelta(days=i * 3, hours=random.randint(0, 20))
            confidence = round(random.uniform(0.70, 0.97), 2)
            record = Classification(
                bin_id=b.bin_id,
                waste_type=waste_type,
                confidence=confidence,
                timestamp=ts,
            )
            db.add(record)
    else:
        log.info("Classification records already exist – skipping.")

    db.commit()
    log.info("Seeding complete ✓")


def main():
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
