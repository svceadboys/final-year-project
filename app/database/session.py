import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

load_dotenv()

# ── Database URL ────────────────────────────────────────────────────────────
# Default: SQLite (zero-config, file created automatically next to this project)
# To use MySQL, set DATABASE_URL in .env:
#   DATABASE_URL=mysql+pymysql://user:password@localhost:3306/smart_waste

_BASE_DIR = Path(__file__).resolve().parents[2]
_DEFAULT_URL = f"sqlite:///{_BASE_DIR / 'smart_waste.db'}"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_URL)

# SQLite needs check_same_thread=False
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

