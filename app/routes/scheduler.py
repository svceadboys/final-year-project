from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Schedule
from app.schemas.schedule import ScheduleRead, ScheduleRequest, ScheduleResponse
from app.scheduler.service import generate_schedule


router = APIRouter()


def _parse_distance_matrix(raw: Dict[str, float]) -> Dict[Tuple[int, int], float]:
    matrix: Dict[Tuple[int, int], float] = {}
    for key, dist in raw.items():
        try:
            src_str, dst_str = key.split("-")
            src = int(src_str)
            dst = int(dst_str)
        except ValueError:
            continue
        matrix[(src, dst)] = float(dist)
        matrix[(dst, src)] = float(dist)
    return matrix


@router.post(
    "/generate",
    response_model=ScheduleResponse,
    summary="Generate smart collection schedule for a truck",
)
def generate_smart_schedule(
    payload: ScheduleRequest,
    db: Session = Depends(get_db),
):
    matrix = _parse_distance_matrix(payload.distance_matrix)

    schedules = generate_schedule(
        db,
        truck_id=payload.truck_id,
        distance_matrix=matrix,
        depot_bin_id=payload.depot_bin_id,
    )

    return ScheduleResponse(schedule=schedules)


@router.get(
    "/today/{truck_id}",
    response_model=List[ScheduleRead],
    summary="Get today's schedule for a truck",
)
def get_today_schedule(
    truck_id: str,
    db: Session = Depends(get_db),
):
    schedules: List[Schedule] = db.query(Schedule).filter(
        Schedule.truck_id == truck_id
    ).all()
    return schedules

