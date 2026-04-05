"""
Issues short-lived JWT tokens for agent checkout sessions.
Token payload includes: agent_id, credential_id, policy_id, expiry.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from vault.config import settings


ALGORITHM = "HS256"


def issue_token(
    agent_id: str,
    credential_id: str,
    policy_id: Optional[str],
    expire_minutes: int = None,
) -> tuple[str, datetime]:
    """
    Issue a signed JWT token for a checkout session.
    Returns (token_string, expires_at).
    """
    expire_minutes = expire_minutes or settings.vault_token_expire_minutes
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

    payload = {
        "sub": agent_id,
        "credential_id": credential_id,
        "policy_id": policy_id,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
        "type": "checkout",
    }

    token = jwt.encode(payload, settings.vault_secret_key, algorithm=ALGORITHM)
    return token, expires_at


def verify_token(token: str) -> dict:
    """
    Verify and decode a checkout token.
    Raises JWTError if invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.vault_secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "checkout":
            raise JWTError("Not a checkout token")
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid or expired token: {e}")
