from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from vault.config import settings

engine = create_engine(
    settings.vault_db_url,
    connect_args={"check_same_thread": False}  # SQLite only
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called on app startup."""
    from vault.models import credential, session, policy  # noqa: F401 - registers models
    Base.metadata.create_all(bind=engine)
