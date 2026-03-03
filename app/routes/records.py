from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Classification
from app.schemas.classification import ClassificationRead

import csv
import io
from datetime import datetime

router = APIRouter()


@router.get(
    "/",
    response_model=List[ClassificationRead],
    summary="List all classification records, optionally filtered by waste_type",
)
def list_records(
    waste_type: Optional[str] = Query(None, description="Filter by waste type"),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Classification)
    if waste_type:
        q = q.filter(Classification.waste_type == waste_type)
    records = (
        q.order_by(Classification.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return records


@router.get(
    "/stats",
    summary="Get count of classifications per waste type",
)
def classification_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    rows = (
        db.query(Classification.waste_type, func.count(Classification.id).label("count"))
        .group_by(Classification.waste_type)
        .all()
    )
    return {row.waste_type: row.count for row in rows}


@router.get(
    "/download",
    summary="Download all classification records as CSV",
)
def download_csv(db: Session = Depends(get_db)):
    records = (
        db.query(Classification)
        .order_by(Classification.timestamp.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Bin ID", "Waste Type", "Confidence", "Timestamp"])
    for r in records:
        writer.writerow([
            f"WR-{r.id:04d}",
            r.bin_id,
            r.waste_type,
            f"{r.confidence:.1%}",
            r.timestamp.strftime("%d/%m/%Y, %H:%M:%S") if r.timestamp else "",
        ])

    output.seek(0)
    filename = f"waste_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
