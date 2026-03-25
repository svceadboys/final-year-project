from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Bin, Truck, Schedule
from app.schemas.truck import DispatchResponse, TruckRead
from app.scheduler.service import auto_dispatch_trucks

router = APIRouter()


@router.get("/trucks", response_model=List[TruckRead], summary="Get fleet status")
def get_fleet_status(db: Session = Depends(get_db)):
    """Return the status and location of all trucks."""
    return db.query(Truck).all()


@router.get("/pending", summary="Get unassigned critical bins")
def get_pending_dispatches(db: Session = Depends(get_db)):
    """Return bins >= 80% full that do NOT have a truck currently en route."""
    full_bins = db.query(Bin).filter(Bin.current_fill >= 80.0).all()
    active_dispatches = db.query(Truck).filter(Truck.status == "en_route").all()
    currently_served_bins = {t.assigned_bin_id for t in active_dispatches if t.assigned_bin_id}
    unassigned = [b for b in full_bins if b.bin_id not in currently_served_bins]
    return unassigned


@router.post("/dispatch", response_model=DispatchResponse, summary="Run auto-dispatcher")
def run_auto_dispatch(bin_id: int | None = None, db: Session = Depends(get_db)):
    """
    Trigger the autonomous dispatch algorithm.
    Finds full bins and assigns the nearest 'idle' trucks to them (or a targeted bin).
    """
    count, msgs = auto_dispatch_trucks(db, min_fill=80.0, target_bin_id=bin_id)
    return DispatchResponse(dispatched_count=count, messages=msgs)


@router.post("/{truck_id}/complete", summary="Mark truck's current assignment as complete")
def complete_collection(truck_id: str, db: Session = Depends(get_db)):
    """
    Called when a truck finishes emptying a bin.
    1. Bin fill level is reset to 0.
    2. Truck status goes back to 'idle'.
    3. Assigned bin is cleared.
    """
    truck = db.query(Truck).filter(Truck.truck_id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
        
    if truck.status != "en_route" or not truck.assigned_bin_id:
        raise HTTPException(status_code=400, detail="Truck is not currently on a collection assignment")
        
    # Mark bin as empty
    b = db.query(Bin).filter(Bin.bin_id == truck.assigned_bin_id).first()
    if b:
        b.current_fill = 0.0
        
    # Relocate truck to the bin's coordinates
    # (Simulating that the truck is now at the bin)
    truck.current_lat = b.lat if b else truck.current_lat
    truck.current_lng = b.lng if b else truck.current_lng
    
    # Reset truck
    truck.status = "idle"
    truck.assigned_bin_id = None
    
    db.commit()
    return {"message": f"Truck {truck_id} completed collection and is now idle."}
