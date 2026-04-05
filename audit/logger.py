"""
Audit logger — append-only event store.
Called from ssh_tool, checkin_tool, injection_detector, and pam_agent.
Designed to be a tamper-evident record: no updates, no deletes.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from audit.db import SessionLocal, init_audit_db
from audit.models.audit_event import AuditEventORM

# Severity mapping by event type
_SEVERITY = {
    "session_checkout": "info",
    "session_checkin": "info",
    "command_executed": "info",
    "command_blocked": "warning",
    "policy_violation": "warning",
    "ssh_error": "warning",
    "injection_detected": "critical",
    "agent_error": "warning",
}

# Initialize DB on import
init_audit_db()


def emit(
    event_type: str,
    agent_id: str,
    token: Optional[str] = None,
    detail: Optional[dict[str, Any]] = None,
) -> None:
    """
    Write an audit event to the append-only store.
    Silently swallows DB errors — audit should never crash the agent.
    """
    try:
        db = SessionLocal()
        event = AuditEventORM(
            id=str(uuid.uuid4()),
            event_type=event_type,
            agent_id=agent_id,
            token=token,
            detail=json.dumps(detail or {}),
            severity=_SEVERITY.get(event_type, "info"),
        )
        db.add(event)
        db.commit()
        db.close()
    except Exception as e:
        # Never let audit failures crash the agent
        print(f"[AUDIT WARNING] Failed to emit event '{event_type}': {e}")


def get_events_for_session(token: str) -> list[AuditEventORM]:
    """Retrieve all audit events for a given checkout session token."""
    db = SessionLocal()
    events = (
        db.query(AuditEventORM)
        .filter(AuditEventORM.token == token)
        .order_by(AuditEventORM.timestamp.asc())
        .all()
    )
    db.close()
    return events


def get_recent_events(limit: int = 100) -> list[AuditEventORM]:
    """Retrieve the most recent N audit events across all sessions."""
    db = SessionLocal()
    events = (
        db.query(AuditEventORM)
        .order_by(AuditEventORM.timestamp.desc())
        .limit(limit)
        .all()
    )
    db.close()
    return events
