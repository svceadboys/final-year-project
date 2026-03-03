"""
seed_real_data.py
Batch-classifies real images from TrashType_Image_Dataset through the CNN model
and populates the database with real classification results + fill history.

Usage:
    python seed_real_data.py
"""

import logging
import math
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from app.database.session import SessionLocal
from app.models import Bin, Classification, BinFillHistory
from app.ml.predict import load_model, predict_image

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

DATASET_DIR = Path(__file__).resolve().parent / "TrashType_Image_Dataset"

MOCK_BINS = [
    {"location": "Main Gate - Block A",   "capacity": 100.0, "current_fill": 72.0},
    {"location": "Cafeteria - Block B",   "capacity": 80.0,  "current_fill": 88.0},
    {"location": "Library - Block C",     "capacity": 60.0,  "current_fill": 45.0},
    {"location": "Sports Complex",        "capacity": 120.0, "current_fill": 91.0},
    {"location": "Admin Block - Gate",    "capacity": 100.0, "current_fill": 60.0},
]

# How many images to classify per category (to keep it fast)
IMAGES_PER_CATEGORY = 10


def seed_bins(db):
    """Create bins if they don't exist."""
    if db.query(Bin).count() > 0:
        log.info("Bins already exist – skipping.")
        return db.query(Bin).all()

    log.info("Creating 5 bins...")
    now = datetime.utcnow()
    for b in MOCK_BINS:
        last_collected = now - timedelta(days=random.randint(1, 10))
        obj = Bin(
            location=b["location"],
            capacity=b["capacity"],
            current_fill=b["current_fill"],
            last_collected=last_collected,
        )
        db.add(obj)
    db.flush()
    return db.query(Bin).all()


def seed_fill_history(db, bins):
    """Create 30-day fill history for each bin (for ARIMA)."""
    if db.query(BinFillHistory).count() > 0:
        log.info("Fill history already exists – skipping.")
        return

    log.info("Seeding 30-day fill history per bin...")
    base_date = datetime.utcnow() - timedelta(days=30)
    for idx, b in enumerate(bins):
        base_fill = b.current_fill * 0.5
        for day in range(30):
            ts = base_date + timedelta(days=day)
            fill = base_fill + 20 * math.sin(day * 0.4 + idx) + random.gauss(0, 3)
            fill = max(5.0, min(100.0, fill))
            db.add(BinFillHistory(bin_id=b.bin_id, fill_level=round(fill, 2), timestamp=ts))


def seed_real_classifications(db, bins, model):
    """
    Classify real images from TrashType_Image_Dataset using the CNN model
    and store results as real classification records.
    """
    # Clear existing classification records so we start fresh
    existing = db.query(Classification).count()
    if existing > 0:
        log.info(f"Clearing {existing} existing dummy classification records...")
        db.query(Classification).delete(synchronize_session=False)
        db.flush()

    categories = sorted([d.name for d in DATASET_DIR.iterdir() if d.is_dir()])
    log.info(f"Found dataset categories: {categories}")

    total_classified = 0
    base_date = datetime.utcnow() - timedelta(days=30)

    for cat_dir in categories:
        cat_path = DATASET_DIR / cat_dir
        images = sorted([f for f in cat_path.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png")])

        # Take a sample
        sample = images[:IMAGES_PER_CATEGORY]
        log.info(f"  Classifying {len(sample)} images from '{cat_dir}/' ...")

        for i, img_path in enumerate(sample):
            try:
                label, confidence = predict_image(img_path, model)
            except Exception as e:
                log.warning(f"    Skip {img_path.name}: {e}")
                continue

            # Assign to a random bin
            b = random.choice(bins)

            # Spread timestamps across the last 30 days
            ts = base_date + timedelta(
                days=random.randint(0, 29),
                hours=random.randint(6, 22),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )

            record = Classification(
                bin_id=b.bin_id,
                waste_type=label,
                confidence=round(confidence, 4),
                timestamp=ts,
            )
            db.add(record)
            total_classified += 1

    log.info(f"✓ Classified {total_classified} real images total.")
    return total_classified


def main():
    db = SessionLocal()
    try:
        # 1) Bins
        bins = seed_bins(db)
        db.commit()

        # 2) Fill history for ARIMA
        seed_fill_history(db, bins)
        db.commit()

        # 3) Load CNN model once
        log.info("Loading MobileNetV2 model...")
        model = load_model()

        # 4) Classify real images
        count = seed_real_classifications(db, bins, model)
        db.commit()

        log.info(f"\n{'='*50}")
        log.info(f"  DONE! {count} real classifications saved to database.")
        log.info(f"  Open http://localhost:8000 to see the dashboard.")
        log.info(f"{'='*50}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
