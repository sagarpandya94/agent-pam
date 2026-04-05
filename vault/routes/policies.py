import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from vault.db.database import get_db
from vault.models.policy import PolicyORM, PolicyCreate, PolicyResponse

router = APIRouter(prefix="/policies", tags=["policies"])


@router.post("/", response_model=PolicyResponse, status_code=201)
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db)):
    if db.query(PolicyORM).filter(PolicyORM.id == payload.id).first():
        raise HTTPException(status_code=409, detail=f"Policy '{payload.id}' already exists")

    policy = PolicyORM(
        id=payload.id,
        name=payload.name,
        credential_id=payload.credential_id,
        agent_pattern=payload.agent_pattern,
        allowed_commands=json.dumps(payload.allowed_commands),
        denied_commands=json.dumps(payload.denied_commands),
        max_session_minutes=str(payload.max_session_minutes),
        require_human_approval=payload.require_human_approval,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return _to_response(policy)


@router.get("/", response_model=list[PolicyResponse])
def list_policies(db: Session = Depends(get_db)):
    policies = db.query(PolicyORM).filter(PolicyORM.active == True).all()  # noqa: E712
    return [_to_response(p) for p in policies]


@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy(policy_id: str, db: Session = Depends(get_db)):
    policy = db.query(PolicyORM).filter(PolicyORM.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return _to_response(policy)


def _to_response(policy: PolicyORM) -> PolicyResponse:
    return PolicyResponse(
        id=policy.id,
        name=policy.name,
        credential_id=policy.credential_id,
        agent_pattern=policy.agent_pattern,
        allowed_commands=json.loads(policy.allowed_commands or "[]"),
        denied_commands=json.loads(policy.denied_commands or "[]"),
        max_session_minutes=int(policy.max_session_minutes),
        require_human_approval=policy.require_human_approval,
        active=policy.active,
        created_at=policy.created_at,
    )
