from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from vault.db.database import Base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- SQLAlchemy ORM Model ---

class CredentialORM(Base):
    __tablename__ = "credentials"

    id = Column(String, primary_key=True)           # e.g. "prod-ec2-001"
    name = Column(String, nullable=False)            # human-readable label
    host = Column(String, nullable=False)
    port = Column(String, default="22")
    username = Column(String, nullable=False)
    encrypted_private_key = Column(Text, nullable=True)   # Fernet-encrypted
    encrypted_password = Column(Text, nullable=True)      # Fernet-encrypted
    allowed_agents = Column(Text, default="*")            # comma-separated agent IDs or "*"
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


# --- Pydantic Schemas ---

class CredentialCreate(BaseModel):
    id: str
    name: str
    host: str
    port: str = "22"
    username: str
    private_key: Optional[str] = None    # plaintext on input, encrypted at rest
    password: Optional[str] = None
    allowed_agents: str = "*"


class CredentialResponse(BaseModel):
    id: str
    name: str
    host: str
    port: str
    username: str
    allowed_agents: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
