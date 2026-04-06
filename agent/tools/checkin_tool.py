"""
Tool: checkin_credential
Agent calls this when its task is complete to release the session token.
Also closes the SSH connection.
"""
import httpx
import os
from agent.tools.ssh_tool import close_connection
from audit.logger import emit


VAULT_BASE_URL = os.getenv("VAULT_BASE_URL", "http://localhost:8000")
AGENT_ID = os.getenv("AGENT_ID", "pam-agent-001")


class CheckinError(Exception):
    pass


def checkin_credential(token: str) -> dict:
    """
    Return a session token to the vault and close the SSH connection.

    Args:
        token: The checkout token issued by the vault

    Returns:
        Dict with status confirmation
    """
    # 1. Close SSH connection first
    close_connection(token)

    # 2. Notify vault
    try:
        response = httpx.post(
            f"{VAULT_BASE_URL}/checkout/checkin",
            json={
                "token": token,
                "agent_id": AGENT_ID,
            },
            timeout=10.0,
        )
    except httpx.ConnectError:
        raise CheckinError("Cannot reach PAM vault during checkin. Token may expire naturally.")

    if response.status_code == 404:
        raise CheckinError("Session not found — may have already expired")
    if response.status_code == 409:
        # Already checked in or revoked — not a fatal error
        return {"status": "already_closed", "token": token}
    if response.status_code != 200:
        raise CheckinError(f"Vault returned {response.status_code} during checkin: {response.text}")

    emit(
        event_type="session_checkin",
        agent_id=AGENT_ID,
        token=token,
        detail={"status": "checked_in"},
    )

    return {"status": "checked_in"}


# Claude tool definition
CHECKIN_TOOL = {
    "name": "checkin_credential",
    "description": (
        "Return your session token to the PAM vault after completing your task. "
        "This closes your SSH connection and marks the session as complete in the audit log. "
        "You MUST call this when your task is done, even if something went wrong."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "token": {
                "type": "string",
                "description": "The checkout token you received from checkout_credential",
            },
        },
        "required": ["token"],
    },
}
