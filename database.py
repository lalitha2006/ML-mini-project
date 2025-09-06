import os
from typing import Generator

from sqlalchemy import Column, DateTime, Integer, String, create_engine, func, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session


# Determine database URL from environment, prefer MySQL; fallback to SQLite for local/dev
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST") or "localhost"
DB_PORT = os.getenv("DB_PORT") or "3306"
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL: str
if DB_USER and DB_PASSWORD and DB_NAME:
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
else:
    # Fallback to SQLite to ensure the app can still run without MySQL env vars
    DATABASE_URL = "sqlite:///./data.db"


engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)

