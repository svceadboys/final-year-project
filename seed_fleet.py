import os
from app.database.session import SessionLocal, engine, Base

# Ensure models are imported
from app.models import Bin, Classification, Forecast, Schedule, BinFillHistory, Truck

def seed_fleet_and_coords():
    print("Recreating database tables for new schema (adding lat/lng and Truck)...")
    
    # Normally we'd use Alembic, but since this is local SQLite for a project,
    # we can just run create_all (it adds new missing tables but won't alter existing ones).
    # Since we added lat/lng to Bin, let's just create new tables. Wait, SQLite create_all 
    # doesn't alter tables. We need to recreate the DB or use raw SQL to alter.
    # Since we want a clean state for the demo anyway, let's drop and recreate.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # 1. Seed Bins with Coordinates (Simulating a campus or city neighborhood)
    bin_data = [
        {"location": "Main Gate - Block A", "capacity": 100.0, "current_fill": 20.0, "lat": 13.0827, "lng": 80.2707},
        {"location": "Cafeteria - Block B", "capacity": 150.0, "current_fill": 85.0, "lat": 13.0835, "lng": 80.2715},
        {"location": "Library - Block C",   "capacity": 80.0,  "current_fill": 15.0, "lat": 13.0815, "lng": 80.2725},
        {"location": "Hostel - Block D",    "capacity": 200.0, "current_fill": 90.0, "lat": 13.0845, "lng": 80.2690},
        {"location": "Auditorium - Block E","capacity": 120.0, "current_fill": 45.0, "lat": 13.0820, "lng": 80.2680},
    ]
    
    for b_data in bin_data:
        b = Bin(**b_data)
        db.add(b)
        
    # 2. Seed Trucks (Taxis)
    truck_data = [
        {"truck_id": "TRK-001", "status": "idle", "current_lat": 13.0810, "current_lng": 80.2700},
        {"truck_id": "TRK-002", "status": "idle", "current_lat": 13.0850, "current_lng": 80.2720},
        {"truck_id": "TRK-003", "status": "idle", "current_lat": 13.0830, "current_lng": 80.2690},
    ]
    
    for t_data in truck_data:
        t = Truck(**t_data)
        db.add(t)
        
    db.commit()
    db.close()
    print("Successfully seeded bins with coordinates and 3 idle trucks!")

if __name__ == "__main__":
    seed_fleet_and_coords()
