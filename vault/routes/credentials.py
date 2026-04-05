import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from vault.db.database import get_db
from vault.models.credential import CredentialORM, CredentialCreate, CredentialResponse
from vault.services.encryption import encrypt

router = APIRouter(prefix="/credentials", tags=["credentials"])


@router.post("/", response_model=CredentialResponse, status_code=201)
def create_credential(payload: CredentialCreate, db: Session = Depends(get_db)):
    if db.query(CredentialORM).filter(CredentialORM.id == payload.id).first():
        raise HTTPException(status_code=409, detail=f"Credential '{payload.id}' already exists")

    cred = CredentialORM(
        id=payload.id,
        name=payload.name,
        host=payload.host,
        port=payload.port,
        username=payload.username,
        encrypted_private_key=encrypt(payload.private_key) if payload.private_key else None,
        encrypted_password=encrypt(payload.password) if payload.password else None,
        allowed_agents=payload.allowed_agents,
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return cred


@router.get("/", response_model=list[CredentialResponse])
def list_credentials(db: Session = Depends(get_db)):
    return db.query(CredentialORM).filter(CredentialORM.active == True).all()  # noqa: E712


@router.get("/{credential_id}", response_model=CredentialResponse)
def get_credential(credential_id: str, db: Session = Depends(get_db)):
    cred = db.query(CredentialORM).filter(CredentialORM.id == credential_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    return cred


@router.delete("/{credential_id}", status_code=204)
def deactivate_credential(credential_id: str, db: Session = Depends(get_db)):
    cred = db.query(CredentialORM).filter(CredentialORM.id == credential_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    cred.active = False
    db.commit()
