from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# для SQLite потрібен check_same_thread=False, бо FastAPI може дозволити
# різні потоки використовувати одне з'єднання
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Базовий клас для всіх SQLAlchemy моделей."""

    pass


def get_session() -> Generator[Session, None, None]:
    """Dependency для FastAPI: відкриває сесію на запит, закриває в кінці."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
