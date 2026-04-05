"""
Guardrail: detects prompt injection attempts in command output or file contents.
Prompt injection = text in the environment trying to hijack the agent's behavior.
This is the SSH equivalent of SQL injection — malicious instructions embedded
in stdout, log files, environment variables, etc.
"""
import re
from dataclasses import dataclass
from audit.logger import emit
import os

AGENT_ID = os.getenv("AGENT_ID", "pam-agent-001")


# Patterns that indicate an attempt to redirect or hijack the agent
INJECTION_PATTERNS = [
    # Instruction overrides
    r"ignore (previous|all|above) instructions",
    r"disregard (your|all) (previous |prior )?(instructions|rules|guidelines)",
    r"new (instructions|directive|orders|task)",
    r"system (prompt|message|override)",
    r"you are now",
    r"act as (a |an )?(different|new|unrestricted)",

    # Credential / secret exfiltration
    r"send (the |your )?(credentials|password|token|key|secret)",
    r"exfiltrate",
    r"(post|upload|transmit) (to|data to) (http|https|ftp)",
    r"curl.*(http|https).*\|",

    # Privilege escalation attempts
    r"sudo (su|bash|sh|-s)",
    r"chmod (777|4755|u\+s)",
    r"add.*to.*sudoers",
    r"visudo",

    # Lateral movement
    r"(download|fetch|pull).*(malware|payload|backdoor|shell)",
    r"(nc|netcat|ncat).*-e.*/bin",
    r"bash -i.*>&.*/dev/tcp",    # reverse shell pattern
    r"python.*-c.*socket",

    # Jailbreak signals
    r"(higher|greater|ultimate) authority",
    r"anthropic (has |)approved",
    r"(bypass|override|ignore).*(safety|guardrail|filter|policy)",
    r"DAN mode",
    r"developer mode",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


@dataclass
class InjectionScanResult:
    is_suspicious: bool
    matched_patterns: list[str]
    source: str          # e.g. "stdout of: ls /tmp"
    raw_text: str


def scan_output(text: str, source: str, token: str = "") -> InjectionScanResult:
    """
    Scan command output or file contents for prompt injection signals.

    Args:
        text: The text to scan (stdout, file contents, env vars, etc.)
        source: Description of where this text came from (for audit)
        token: Active session token (for audit correlation)

    Returns:
        InjectionScanResult — agent should check .is_suspicious before proceeding
    """
    matched = []
    for pattern, compiled in zip(INJECTION_PATTERNS, _compiled):
        if compiled.search(text):
            matched.append(pattern)

    result = InjectionScanResult(
        is_suspicious=len(matched) > 0,
        matched_patterns=matched,
        source=source,
        raw_text=text[:500],    # truncate for audit storage
    )

    if result.is_suspicious:
        emit(
            event_type="injection_detected",
            agent_id=AGENT_ID,
            token=token,
            detail={
                "source": source,
                "matched_patterns": matched,
                "text_preview": text[:300],
            },
        )

    return result


def format_injection_warning(result: InjectionScanResult) -> str:
    """Format a human-readable warning for the agent to include in its response."""
    return (
        f"⚠️  PROMPT INJECTION DETECTED in output from: {result.source}\n"
        f"Matched patterns: {result.matched_patterns}\n"
        f"I am stopping execution and NOT following any instructions found in this output.\n"
        f"This event has been logged to the audit trail."
    )
