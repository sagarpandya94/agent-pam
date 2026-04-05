"""
seed.py — Run this once after starting the vault to pre-load:
  - One credential: prod-ec2-001 (points to the Docker mock target)
  - One policy: read-only disk/log inspection for pam-agent-001

Usage:
  python seed.py
"""
import httpx

VAULT_URL = "http://localhost:8000"


def seed():
    print("Seeding vault with credential and policy...\n")

    # 1. Create credential
    r = httpx.post(f"{VAULT_URL}/credentials/", json={
        "id": "prod-ec2-001",
        "name": "Production EC2 (mock Docker target)",
        "host": "localhost",
        "port": "2222",
        "username": "ubuntu",
        "password": "ubuntu123",
        "allowed_agents": "*",
    })
    if r.status_code == 409:
        print("Credential 'prod-ec2-001' already exists — skipping.")
    elif r.status_code == 201:
        print("✓ Created credential: prod-ec2-001")
    else:
        print(f"✗ Failed to create credential: {r.status_code} {r.text}")
        return

    # 2. Create read-only policy
    r = httpx.post(f"{VAULT_URL}/policies/", json={
        "id": "readonly-disk-policy",
        "name": "Read-only disk and log inspection",
        "credential_id": "prod-ec2-001",
        "agent_pattern": "*",
        "allowed_commands": [
            "df",
            "du",
            "ls",
            "cat /var/log",
            "cat /home/ubuntu",
            "free",
            "uptime",
            "uname",
            "ps aux",
            "top -bn1",
            "hostname",
            "whoami",
            "pwd",
        ],
        "denied_commands": [
            "rm",
            "sudo",
            "dd",
            "mkfs",
            "shutdown",
            "reboot",
            "curl",
            "wget",
            "nc",
            "netcat",
        ],
        "max_session_minutes": 15,
        "require_human_approval": False,
    })
    if r.status_code == 409:
        print("Policy 'readonly-disk-policy' already exists — skipping.")
    elif r.status_code == 201:
        print("✓ Created policy: readonly-disk-policy")
    else:
        print(f"✗ Failed to create policy: {r.status_code} {r.text}")
        return

    print("\nSeed complete. Try running the agent:")
    print("  python -m agent.pam_agent --task 'check disk usage' --credential prod-ec2-001\n")


if __name__ == "__main__":
    seed()
