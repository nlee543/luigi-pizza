from pathlib import Path

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

from models import Base


DATABASE_PATH = Path(__file__).resolve().parent / "luigi_pizza.db"
engine = create_engine(URL.create("sqlite", database=str(DATABASE_PATH)))
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print(f"Database initialized: {DATABASE_PATH}")
