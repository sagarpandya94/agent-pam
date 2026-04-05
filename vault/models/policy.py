from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from vault.db.database import Base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- SQLAlchemy ORM Model ---

class PolicyORM(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    credential_id = Column(String, nullable=False)        # which cred this applies to
    agent_pattern = Column(String, default="*")           # glob: "pam-agent-*" or specific ID
    allowed_commands = Column(Text, nullable=False)       # JSON list of allowed command prefixes
    denied_commands = Column(Text, default="[]")          # JSON list of denied command prefixes
    max_session_minutes = Column(String, default="15")
    require_human_approval = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


# --- Pydantic Schemas ---

class PolicyCreate(BaseModel):
    id: str
    name: str
    credential_id: str
    agent_pattern: str = "*"
    allowed_commands: list[str]          # e.g. ["df", "du", "ls", "cat /var/log"]
    denied_commands: list[str] = []      # e.g. ["rm", "sudo rm", "dd", "mkfs"]
    max_session_minutes: int = 15
    require_human_approval: bool = False


class PolicyResponse(BaseModel):
    id: str
    name: str
    credential_id: str
    agent_pattern: str
    allowed_commands: list[str]
    denied_commands: list[str]
    max_session_minutes: int
    require_human_approval: bool
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
