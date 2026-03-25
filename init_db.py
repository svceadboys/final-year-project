"""
init_db.py

A utility script to initialize the database schema and create all tables explicitly.
This is useful when deploying to a fresh environment or transitioning to a MySQL database,
ensuring all SQLAlchemy models are safely instantiated.

Usage:
    python init_db.py
"""

import logging
from app.database.session import engine, Base
# Import models so Base.metadata knows about them implicitly
from app.models import Bin, Classification, BinFillHistory, Forecast, Schedule, Truck

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def run_migrations():
    log.info("Connecting to the configured database engine...")
    log.info(f"Engine URL: {engine.url}")
    
    log.info("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    log.info("Database initialization completed successfully! ✓")

if __name__ == "__main__":
    run_migrations()
