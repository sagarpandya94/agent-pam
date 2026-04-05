"""
Tool: checkout_credential
Agent calls this to request a scoped, time-limited session token from the vault.
Returns connection details + allowed commands. Never returns raw secrets.
"""
import httpx
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


VAULT_BASE_URL = os.getenv("VAULT_BASE_URL", "http://localhost:8000")
AGENT_ID = os.getenv("AGENT_ID", "pam-agent-001")


@dataclass
class CheckoutResult:
    token: str
    credential_id: str
    host: str
    port: str
    username: str
    password: Optional[str]
    expires_at: datetime
    allowed_commands: list[str]


class CheckoutError(Exception):
    pass


def checkout_credential(credential_id: str, task_description: str) -> CheckoutResult:
    """
    Request a scoped session token for a credential from the PAM vault.

    Args:
        credential_id: The ID of the credential to check out (e.g. "prod-ec2-001")
        task_description: Human-readable description of what the agent intends to do

    Returns:
        CheckoutResult with connection details and allowed commands

    Raises:
        CheckoutError if vault denies access or credential not found
    """
    try:
        response = httpx.post(
            f"{VAULT_BASE_URL}/checkout/",
            json={
                "agent_id": AGENT_ID,
                "credential_id": credential_id,
                "task_description": task_description,
            },
            timeout=10.0,
        )
    except httpx.ConnectError:
        raise CheckoutError("Cannot reach PAM vault. Is it running on localhost:8000?")

    if response.status_code == 403:
        raise CheckoutError(f"Access denied by vault policy: {response.json().get('detail')}")
    if response.status_code == 404:
        raise CheckoutError(f"Credential '{credential_id}' not found in vault")
    if response.status_code == 202:
        raise CheckoutError("This credential requires human approval before checkout")
    if response.status_code != 201:
        raise CheckoutError(f"Vault returned unexpected status {response.status_code}: {response.text}")

    data = response.json()
    return CheckoutResult(
        token=data["token"],
        credential_id=data["credential_id"],
        host=data["host"],
        port=data["port"],
        username=data["username"],
        password=data.get("password"),
        expires_at=datetime.fromisoformat(data["expires_at"]),
        allowed_commands=data["allowed_commands"],
    )


# Claude tool definition
CHECKOUT_TOOL = {
    "name": "checkout_credential",
    "description": (
        "Request a scoped, time-limited session token from the PAM vault to access a remote machine. "
        "You MUST call this before attempting any SSH connection. "
        "Returns connection details and the list of commands you are permitted to run."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "credential_id": {
                "type": "string",
                "description": "The ID of the credential to check out (e.g. 'prod-ec2-001')",
            },
            "task_description": {
                "type": "string",
                "description": "Clear description of what you intend to do with this access",
            },
        },
        "required": ["credential_id", "task_description"],
    },
}
