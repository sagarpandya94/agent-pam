"""
Guardrail: blocks destructive or dangerous commands before SSH execution.
This is a hard stop — policy engine handles allow-list, this handles deny-list.
"""

DESTRUCTIVE_PREFIXES = [
    "rm -rf",
    "rm -r /",
    "dd if=",
    "mkfs",
    "> /dev/",
    "shutdown",
    "reboot",
    "halt",
    "init 0",
    "chmod 777 /",
    "chown root /",
    ":(){ :|:& };:",   # fork bomb
    "curl | bash",
    "wget | bash",
    "wget -O- | sh",
]

SENSITIVE_READS = [
    "cat /etc/shadow",
    "cat /etc/passwd",
    "cat ~/.ssh/id_rsa",
    "cat ~/.aws/credentials",
]


class CommandBlocked(Exception):
    pass


def check_command(command: str) -> None:
    """
    Raise CommandBlocked if the command matches a destructive or sensitive pattern.
    This runs BEFORE the policy engine check as an absolute safety layer.
    """
    cmd_lower = command.strip().lower()

    for prefix in DESTRUCTIVE_PREFIXES:
        if cmd_lower.startswith(prefix.lower()) or prefix.lower() in cmd_lower:
            raise CommandBlocked(
                f"Command blocked by safety guardrail: '{command}' "
                f"matches destructive pattern '{prefix}'"
            )

    for pattern in SENSITIVE_READS:
        if pattern.lower() in cmd_lower:
            raise CommandBlocked(
                f"Command blocked: attempting to read sensitive file — '{command}'"
            )
