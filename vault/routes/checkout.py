import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from ..services.encryption import decrypt

from vault.db.database import get_db
from vault.models.credential import CredentialORM
from vault.models.session import (
    CheckoutSessionORM,
    CheckoutRequest,
    CheckoutResponse,
    CheckinRequest,
    SessionResponse,
)
from vault.services.token_service import issue_token, verify_token
from vault.services.policy_engine import evaluate_checkout, PolicyDenied
from vault.services.encryption import decrypt

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("/", response_model=CheckoutResponse, status_code=201)
def checkout_credential(payload: CheckoutRequest, db: Session = Depends(get_db)):
    """
    Agent requests a scoped, time-limited session token for a credential.
    Policy is evaluated here — if denied, 403 is returned.
    """
    # 1. Verify credential exists
    cred = db.query(CredentialORM).filter(
        CredentialORM.id == payload.credential_id,
        CredentialORM.active == True,  # noqa: E712
    ).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found or inactive")

    decrypted_password = decrypt(cred.encrypted_password) if cred.encrypted_password else None

    # 2. Evaluate policy
    try:
        policy = evaluate_checkout(db, payload.agent_id, payload.credential_id)
    except PolicyDenied as e:
        raise HTTPException(status_code=403, detail=str(e))

    # 3. Human approval gate (future: webhook / notification)
    if policy.require_human_approval:
        raise HTTPException(
            status_code=202,
            detail="This credential requires human approval. Request queued."
        )

    # 4. Issue token
    max_minutes = int(policy.max_session_minutes)
    token, expires_at = issue_token(
        agent_id=payload.agent_id,
        credential_id=payload.credential_id,
        policy_id=policy.id,
        expire_minutes=max_minutes,
    )

    # 5. Store session record
    session = CheckoutSessionORM(
        token=token,
        agent_id=payload.agent_id,
        credential_id=payload.credential_id,
        task_description=payload.task_description,
        expires_at=expires_at,
        policy_id=policy.id,
    )
    db.add(session)
    db.commit()

    allowed_commands = json.loads(policy.allowed_commands or "[]")

    return CheckoutResponse(
        token=token,
        credential_id=cred.id,
        host=cred.host,
        port=cred.port,
        username=cred.username,
        password=decrypted_password,
        expires_at=expires_at,
        allowed_commands=allowed_commands,
    )


@router.post("/checkin", status_code=200)
def checkin_credential(payload: CheckinRequest, db: Session = Depends(get_db)):
    """Agent explicitly returns the session token after completing its task."""
    session = db.query(CheckoutSessionORM).filter(
        CheckoutSessionORM.token == payload.token,
        CheckoutSessionORM.agent_id == payload.agent_id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.revoked:
        raise HTTPException(status_code=409, detail="Session already revoked")
    if session.checked_in_at:
        raise HTTPException(status_code=409, detail="Session already checked in")

    session.checked_in_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "checked_in", "token": payload.token}


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(agent_id: str = None, db: Session = Depends(get_db)):
    """List all checkout sessions, optionally filtered by agent_id."""
    q = db.query(CheckoutSessionORM)
    if agent_id:
        q = q.filter(CheckoutSessionORM.agent_id == agent_id)
    return q.order_by(CheckoutSessionORM.issued_at.desc()).all()


@router.post("/verify")
def verify_session_token(token: str, db: Session = Depends(get_db)):
    """Verify a token is still valid (not expired, not revoked, not checked in)."""
    try:
        payload = verify_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    session = db.query(CheckoutSessionORM).filter(
        CheckoutSessionORM.token == token
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session record not found")
    if session.revoked:
        raise HTTPException(status_code=401, detail="Session has been revoked")
    if session.checked_in_at:
        raise HTTPException(status_code=401, detail="Session already checked in")

    return {"valid": True, "payload": payload}
