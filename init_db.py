"""
init_db.py
Run this once to create all database tables in your MySQL instance.

Usage:
    python init_db.py
"""

import logging

from app.database.session import Base, engine

# Import all models so they register with Base.metadata
from app.models import Bin, Classification, Forecast, Schedule, BinFillHistory  # noqa: F401

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def init_db() -> None:
    log.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    log.info("All tables created successfully.")


if __name__ == "__main__":
    init_db()
