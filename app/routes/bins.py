from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Bin, BinFillHistory
from app.schemas.bin import BinCreate, BinRead


router = APIRouter()


@router.get("/", response_model=List[BinRead])
def list_bins(db: Session = Depends(get_db)):
    bins = db.query(Bin).all()
    return bins


@router.post("/", response_model=BinRead)
def create_bin(payload: BinCreate, db: Session = Depends(get_db)):
    new_bin = Bin(
        location=payload.location,
        capacity=payload.capacity,
        current_fill=payload.current_fill,
        last_collected=payload.last_collected,
    )
    db.add(new_bin)
    db.commit()
    db.refresh(new_bin)
    return new_bin


@router.get("/{bin_id}", response_model=BinRead)
def get_bin(bin_id: int, db: Session = Depends(get_db)):
    b = db.query(Bin).filter(Bin.bin_id == bin_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bin not found")
    return b


@router.put("/{bin_id}", response_model=BinRead)
def update_bin(bin_id: int, payload: BinCreate, db: Session = Depends(get_db)):
    b = db.query(Bin).filter(Bin.bin_id == bin_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bin not found")

    b.location = payload.location
    b.capacity = payload.capacity
    b.current_fill = payload.current_fill
    b.last_collected = payload.last_collected
    db.commit()
    db.refresh(b)
    return b


@router.post("/{bin_id}/fill-history")
def add_fill_history(
    bin_id: int, fill_level: float, db: Session = Depends(get_db)
):
    b = db.query(Bin).filter(Bin.bin_id == bin_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Bin not found")

    record = BinFillHistory(bin_id=bin_id, fill_level=fill_level)
    db.add(record)

    b.current_fill = fill_level

    db.commit()
    return {"message": "Fill history recorded"}

