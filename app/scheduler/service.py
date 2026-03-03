from datetime import date
from typing import Dict, List, Tuple

import networkx as nx
from sqlalchemy.orm import Session

from app.models import Bin, Forecast, Schedule


def calculate_priority(
    predicted_fill: float, days_since_last_collection: int
) -> float:
    return (predicted_fill * 0.6) + (days_since_last_collection * 0.4)


def get_bins_to_schedule(
    db: Session, min_predicted_fill: float = 80.0
) -> List[Tuple[Bin, Forecast, float]]:
    today = date.today()

    bins: List[Bin] = db.query(Bin).all()
    result: List[Tuple[Bin, Forecast, float]] = []

    for b in bins:
        latest_forecast: Forecast | None = (
            db.query(Forecast)
            .filter(Forecast.bin_id == b.bin_id, Forecast.predicted_date >= today)
            .order_by(Forecast.predicted_date.asc())
            .first()
        )
        if not latest_forecast:
            continue

        predicted_fill = latest_forecast.predicted_fill
        if predicted_fill < min_predicted_fill:
            continue

        last_collected = b.last_collected.date() if b.last_collected else today
        days_since = (today - last_collected).days
        priority_score = calculate_priority(predicted_fill, days_since)
        result.append((b, latest_forecast, priority_score))

    # Sort bins by highest priority first
    result.sort(key=lambda x: x[2], reverse=True)
    return result


def build_distance_graph(
    bins: List[Bin], distance_matrix: Dict[Tuple[int, int], float]
) -> nx.Graph:
    """Build an undirected graph where nodes are bin_ids and edges are distances."""
    G = nx.Graph()
    for b in bins:
        G.add_node(b.bin_id)

    for (src, dst), dist in distance_matrix.items():
        if src in G.nodes and dst in G.nodes:
            G.add_edge(src, dst, weight=dist)
    return G


def optimize_route(
    bin_ids: List[int],
    distance_matrix: Dict[Tuple[int, int], float],
    depot_bin_id: int | None = None,
) -> List[int]:
    """
    Use a greedy strategy with Dijkstra to construct a short route.

    - Start from depot_bin_id if provided, else first bin in list.
    - Repeatedly go to the nearest next bin (shortest path distance).
    """
    if not bin_ids:
        return []

    bins = [Bin(bin_id=b_id, location="", capacity=0, current_fill=0) for b_id in bin_ids]
    G = build_distance_graph(bins, distance_matrix)

    remaining = set(bin_ids)
    current = depot_bin_id if depot_bin_id in remaining else next(iter(remaining))
    route = [current]
    remaining.remove(current)

    while remaining:
        best_next = None
        best_distance = float("inf")
        for candidate in remaining:
            try:
                length = nx.dijkstra_path_length(G, current, candidate, weight="weight")
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
            if length < best_distance:
                best_distance = length
                best_next = candidate

        if best_next is None:
            # no more reachable nodes; stop
            break

        current = best_next
        route.append(current)
        remaining.remove(current)

    return route


def generate_schedule(
    db: Session,
    truck_id: str,
    distance_matrix: Dict[Tuple[int, int], float],
    depot_bin_id: int | None = None,
) -> List[Schedule]:
    """
    Generate and persist a schedule for the given truck based on current forecasts.

    distance_matrix is a dict with keys (bin_id1, bin_id2) mapping to distance (float).
    """
    today = date.today()

    bin_tuples = get_bins_to_schedule(db)
    if not bin_tuples:
        return []

    bins_only = [b for (b, _, _) in bin_tuples]
    bin_ids = [b.bin_id for b in bins_only]

    route = optimize_route(bin_ids, distance_matrix, depot_bin_id)
    order_map: Dict[int, int] = {b_id: idx for idx, b_id in enumerate(route)}

    schedules: List[Schedule] = []
    for b, _, priority_score in bin_tuples:
        if b.bin_id not in order_map:
            continue
        schedules.append(
            Schedule(
                truck_id=truck_id,
                bin_id=b.bin_id,
                priority_score=priority_score,
                route_order=order_map[b.bin_id],
                scheduled_date=today,
            )
        )

    # Remove existing schedule for this truck and date
    db.query(Schedule).filter(
        Schedule.truck_id == truck_id, Schedule.scheduled_date == today
    ).delete(synchronize_session=False)

    db.add_all(schedules)
    db.commit()

    for s in schedules:
        db.refresh(s)
    return schedules

