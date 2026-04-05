from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from vault.db.database import Base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- SQLAlchemy ORM Model ---

class CheckoutSessionORM(Base):
    __tablename__ = "checkout_sessions"

    token = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False)
    credential_id = Column(String, nullable=False)
    task_description = Column(Text, nullable=True)    # what the agent said it needs this for
    issued_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    checked_in_at = Column(DateTime, nullable=True)   # null = still active
    revoked = Column(Boolean, default=False)
    policy_id = Column(String, nullable=True)         # which policy was applied


# --- Pydantic Schemas ---

class CheckoutRequest(BaseModel):
    agent_id: str
    credential_id: str
    task_description: str


class CheckoutResponse(BaseModel):
    token: str
    credential_id: str
    host: str
    port: str
    username: str
    password: Optional[str] = None
    expires_at: datetime
    allowed_commands: list[str]


class CheckinRequest(BaseModel):
    token: str
    agent_id: str


class SessionResponse(BaseModel):
    token: str
    agent_id: str
    credential_id: str
    task_description: Optional[str]
    issued_at: datetime
    expires_at: datetime
    checked_in_at: Optional[datetime]
    revoked: bool

    class Config:
        from_attributes = True
