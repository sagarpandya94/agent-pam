"""
Tool: ssh_execute
Agent uses this to run a single command on the target machine via SSH.
Validates the command against guardrails + policy before execution.
Every execution is emitted to the audit logger.
"""
import paramiko
import os
from dataclasses import dataclass
from typing import Optional

from agent.guardrails.command_filter import check_command, CommandBlocked
from audit.logger import emit


AGENT_ID = os.getenv("AGENT_ID", "pam-agent-001")

# In-memory store of active SSH connections keyed by token
# Reused across multiple ssh_execute calls within the same session
_active_connections: dict[str, paramiko.SSHClient] = {}


@dataclass
class SSHResult:
    command: str
    stdout: str
    stderr: str
    exit_code: int
    blocked: bool = False
    block_reason: Optional[str] = None


def _get_or_create_connection(
    token: str,
    host: str,
    port: str,
    username: str,
    private_key_str: Optional[str] = None,
    password: Optional[str] = None,
) -> paramiko.SSHClient:
    """Reuse existing connection for the same token, or create a new one."""
    if token in _active_connections:
        client = _active_connections[token]
        transport = client.get_transport()
        if transport and transport.is_active():
            return client
        # Connection dropped — clean up and reconnect
        del _active_connections[token]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = {
        "hostname": host,
        "port": int(port),
        "username": username,
        "timeout": 10,
    }

    if private_key_str:
        import io
        pkey = paramiko.RSAKey.from_private_key(io.StringIO(private_key_str))
        connect_kwargs["pkey"] = pkey
    elif password:
        connect_kwargs["password"] = password
    else:
        # No key provided — disable key/agent auth so password auth is used
        connect_kwargs["look_for_keys"] = False
        connect_kwargs["allow_agent"] = False

    client.connect(**connect_kwargs)
    _active_connections[token] = client
    return client


def ssh_execute(
    token: str,
    host: str,
    port: str,
    username: str,
    command: str,
    allowed_commands: list[str],
    private_key_str: Optional[str] = None,
    password: Optional[str] = None,
) -> SSHResult:
    """
    Execute a single command on the target machine via SSH.
    Runs guardrail check first, then connects and executes.
    Emits an audit event regardless of outcome.

    Args:
        token: Active checkout session token
        host/port/username: Connection details from checkout
        command: The command to run
        allowed_commands: List of allowed command prefixes from policy
        private_key_str: Optional decrypted private key (passed by agent, NOT stored)
        password: Optional password

    Returns:
        SSHResult with stdout, stderr, exit_code
    """
    # 1. Hard guardrail check (destructive commands)
    try:
        check_command(command)
    except CommandBlocked as e:
        result = SSHResult(
            command=command,
            stdout="",
            stderr=str(e),
            exit_code=-1,
            blocked=True,
            block_reason=str(e),
        )
        emit(
            event_type="command_blocked",
            agent_id=AGENT_ID,
            token=token,
            detail={"command": command, "reason": str(e)},
        )
        return result

    # 2. Policy allow-list check
    if allowed_commands:
        cmd_lower = command.strip().lower()
        if not any(cmd_lower.startswith(a.lower()) for a in allowed_commands):
            reason = (
                f"Command '{command}' not in allowed list: {allowed_commands}"
            )
            result = SSHResult(
                command=command,
                stdout="",
                stderr=reason,
                exit_code=-1,
                blocked=True,
                block_reason=reason,
            )
            emit(
                event_type="policy_violation",
                agent_id=AGENT_ID,
                token=token,
                detail={"command": command, "allowed": allowed_commands},
            )
            return result

    # 3. Execute via SSH
    try:
        client = _get_or_create_connection(
            token=token,
            host=host,
            port=port,
            username=username,
            private_key_str=private_key_str,
            password=password,
        )

        stdin, stdout_stream, stderr_stream = client.exec_command(command, timeout=30)
        stdout = stdout_stream.read().decode("utf-8", errors="replace").strip()
        stderr = stderr_stream.read().decode("utf-8", errors="replace").strip()
        exit_code = stdout_stream.channel.recv_exit_status()

        result = SSHResult(
            command=command,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
        )

        emit(
            event_type="command_executed",
            agent_id=AGENT_ID,
            token=token,
            detail={
                "command": command,
                "exit_code": exit_code,
                "stdout_preview": stdout[:300],
                "stderr_preview": stderr[:300],
            },
        )
        return result

    except Exception as e:
        emit(
            event_type="ssh_error",
            agent_id=AGENT_ID,
            token=token,
            detail={"command": command, "error": str(e)},
        )
        return SSHResult(
            command=command,
            stdout="",
            stderr=f"SSH error: {e}",
            exit_code=-1,
        )


def close_connection(token: str) -> None:
    """Close and clean up SSH connection for a session."""
    if token in _active_connections:
        try:
            _active_connections[token].close()
        except Exception:
            pass
        del _active_connections[token]


# Claude tool definition
SSH_TOOL = {
    "name": "ssh_execute",
    "description": (
        "Execute a single shell command on the remote machine via SSH. "
        "You must have a valid checkout token before calling this. "
        "Commands are validated against your policy — blocked commands will return an error. "
        "Every command is logged to the audit trail."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute on the remote machine",
            },
        },
        "required": ["command"],
    },
}
