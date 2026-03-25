from pathlib import Path
import tempfile
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.ml.predict import load_model, predict_image
from app.ml.fill_predictor import predictor
from app.scheduler.service import auto_dispatch_trucks
from app.models import Bin, Classification
from app.schemas.classification import ClassificationRead

router = APIRouter()


_model = None


def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model


@router.post(
    "/predict",
    response_model=ClassificationRead,
    summary="Upload a single image for waste classification",
)
async def classify_waste(
    bin_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    b = db.query(Bin).filter(Bin.bin_id == bin_id).first()
    if not b:
        # Dynamically auto-provision new bins for prototype testing
        import random
        r_lat = 13.05 + random.random() * 0.1
        r_lng = 80.20 + random.random() * 0.1
        b = Bin(bin_id=bin_id, location=f"Sector {bin_id} Hub", capacity=1000, current_fill=0, lat=r_lat, lng=r_lng)
        db.add(b)
        db.commit()

    suffix = Path(file.filename).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        model = get_model()
        label, confidence = predict_image(tmp_path, model)
        
        # Calculate percentage fill using our CV heuristic
        with open(tmp_path, "rb") as f:
            fill_pct = predictor.predict_fill(f.read())
    finally:
        tmp_path.unlink(missing_ok=True)

    # Autonomously sync the bin's core system tracking level
    b.current_fill = fill_pct

    record = Classification(
        bin_id=bin_id,
        waste_type=label,
        confidence=confidence,
        predicted_fill=fill_pct,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.post(
    "/predict/batch",
    response_model=List[ClassificationRead],
    summary="Upload multiple images for batch waste classification",
)
async def classify_waste_batch(
    bin_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    b = db.query(Bin).filter(Bin.bin_id == bin_id).first()
    if not b:
        # Dynamically auto-provision newly tested bins
        import random
        r_lat = 13.05 + random.random() * 0.1
        r_lng = 80.20 + random.random() * 0.1
        b = Bin(bin_id=bin_id, location=f"Sector {bin_id} Hub", capacity=1000, current_fill=0, lat=r_lat, lng=r_lng)
        db.add(b)
        db.commit()

    model = get_model()
    results = []

    for file in files:
        suffix = Path(file.filename).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            label, confidence = predict_image(tmp_path, model)
            with open(tmp_path, "rb") as f:
                fill_pct = predictor.predict_fill(f.read())
        except Exception:
            label, confidence, fill_pct = "unknown", 0.0, 50.0
        finally:
            tmp_path.unlink(missing_ok=True)

        b.current_fill = fill_pct

        record = Classification(
            bin_id=bin_id,
            waste_type=label,
            confidence=round(confidence, 4),
            predicted_fill=fill_pct,
        )
        db.add(record)
        db.flush()
        db.refresh(record)
        # Attach filename for frontend (not stored in DB)
        record._filename = file.filename
        results.append(record)

    db.commit()
    return results


@router.get(
    "/history/{bin_id}",
    response_model=List[ClassificationRead],
    summary="Get classification history for a bin",
)
def get_classification_history(bin_id: int, db: Session = Depends(get_db)):
    records = (
        db.query(Classification)
        .filter(Classification.bin_id == bin_id)
        .order_by(Classification.timestamp.desc())
        .all()
    )
    return records

