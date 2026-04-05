import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

AUDIT_DB_URL = os.getenv("AUDIT_DB_URL", "sqlite:///./audit.db")

engine = create_engine(
    AUDIT_DB_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_audit_db():
    from audit.models import audit_event  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_audit_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
