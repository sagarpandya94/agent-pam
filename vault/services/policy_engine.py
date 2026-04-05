"""
Policy engine: evaluates whether an agent may check out a credential
and whether a given command is permitted under the active policy.
"""
import json
import fnmatch
from typing import Optional
from sqlalchemy.orm import Session
from vault.models.policy import PolicyORM


class PolicyDenied(Exception):
    pass


def find_policy(
    db: Session,
    credential_id: str,
    agent_id: str,
) -> Optional[PolicyORM]:
    """
    Find the most specific active policy for (credential_id, agent_id).
    Prefers exact agent match over wildcard.
    """
    policies = (
        db.query(PolicyORM)
        .filter(
            PolicyORM.credential_id == credential_id,
            PolicyORM.active == True,  # noqa: E712
        )
        .all()
    )

    # Prefer exact match, fall back to glob match
    exact = [p for p in policies if p.agent_pattern == agent_id]
    if exact:
        return exact[0]

    globs = [p for p in policies if fnmatch.fnmatch(agent_id, p.agent_pattern)]
    return globs[0] if globs else None


def evaluate_checkout(
    db: Session,
    agent_id: str,
    credential_id: str,
) -> PolicyORM:
    """
    Evaluate whether an agent can check out a credential.
    Returns the matching policy or raises PolicyDenied.
    """
    policy = find_policy(db, credential_id, agent_id)

    if not policy:
        raise PolicyDenied(
            f"No policy grants agent '{agent_id}' access to credential '{credential_id}'"
        )

    return policy


def evaluate_command(policy: PolicyORM, command: str) -> None:
    """
    Check whether a command is permitted under a policy.
    Raises PolicyDenied if:
      - command matches a denied prefix
      - command does not match any allowed prefix
    """
    command_lower = command.strip().lower()

    denied = json.loads(policy.denied_commands or "[]")
    for denied_prefix in denied:
        if command_lower.startswith(denied_prefix.lower()):
            raise PolicyDenied(
                f"Command '{command}' is explicitly denied by policy '{policy.id}'"
            )

    allowed = json.loads(policy.allowed_commands or "[]")
    if allowed and not any(
        command_lower.startswith(a.lower()) for a in allowed
    ):
        raise PolicyDenied(
            f"Command '{command}' is not in the allowed list for policy '{policy.id}'. "
            f"Allowed: {allowed}"
        )
