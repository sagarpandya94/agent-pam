from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from audit.db import Base
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


# Valid event types
class EventType:
    SESSION_CHECKOUT = "session_checkout"
    SESSION_CHECKIN = "session_checkin"
    COMMAND_EXECUTED = "command_executed"
    COMMAND_BLOCKED = "command_blocked"
    POLICY_VIOLATION = "policy_violation"
    SSH_ERROR = "ssh_error"
    INJECTION_DETECTED = "injection_detected"
    AGENT_ERROR = "agent_error"


# --- SQLAlchemy ORM ---

class AuditEventORM(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    token = Column(String, nullable=True)        # links event to a checkout session
    detail = Column(Text, nullable=True)         # JSON blob
    severity = Column(String, default="info")    # info | warning | critical
    timestamp = Column(DateTime, server_default=func.now())


# --- Pydantic ---

class AuditEventResponse(BaseModel):
    id: str
    event_type: str
    agent_id: str
    token: Optional[str]
    detail: Optional[Any]
    severity: str
    timestamp: datetime

    class Config:
        from_attributes = True
