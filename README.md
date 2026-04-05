# agent-pam

**PAM (Privileged Access Management) for AI Agents**

A proof-of-concept demonstrating governance, credential management, and full auditability for AI agents accessing privileged infrastructure — the emerging frontier of non-human identity (NHI) security.

## Architecture

```
┌─────────────────┐     checkout request      ┌─────────────────┐
│   Claude Agent  │ ─────────────────────────► │   PAM Vault     │
│                 │ ◄───────────────────────── │   (FastAPI)     │
│  - checkout     │     scoped session token   │                 │
│  - ssh_execute  │                            │  - credentials  │
│  - checkin      │                            │  - policies     │
│  - guardrails   │                            │  - tokens       │
└────────┬────────┘                            └─────────────────┘
         │ SSH (scoped token)                           │
         ▼                                             │ all events
┌─────────────────┐                            ┌──────▼──────────┐
│  Target Machine │                            │  Audit Layer    │
│  (Docker/EC2)   │                            │                 │
│                 │                            │  - event log    │
│  mock Ubuntu    │                            │  - session      │
│  SSH enabled    │                            │    replay       │
└─────────────────┘                            │  - anomaly flags│
                                               └─────────────────┘
```

## Layers

| Layer | Tech | Purpose |
|-------|------|---------|
| **Vault** | FastAPI + SQLite + cryptography | Store & issue scoped credentials |
| **Agent** | Claude (claude-sonnet) + Paramiko | Request access, execute tasks |
| **Audit** | SQLite append-only + Streamlit | Log every action, session replay |
| **Target** | Docker (SSH-enabled Ubuntu) | Mock EC2 / privileged machine |

## Quick Start

```bash
# 1. Spin up the mock EC2 target
docker-compose up target -d

# 2. Start the PAM vault
cd vault && uvicorn main:app --reload --port 8000

# 3. Run the agent with a task
cd agent && python pam_agent.py --task "check disk usage on prod-ec2"

# 4. View audit dashboard
cd audit/dashboard && streamlit run app.py
```

## Key Security Concepts Demonstrated

- **JIT (Just-In-Time) access** — agents request credentials per task, no standing access
- **Least privilege** — policies scope what commands an agent can run
- **Session checkout/checkin** — credentials are time-limited and auto-revoked
- **Full audit trail** — every SSH command logged with agent identity + timestamp
- **Prompt injection defense** — guardrails detect and block injection attempts
- **Scope violation detection** — agent cannot exceed its granted policy

## Test Layers

```
tests/
├── unit/           # Encryption, token generation, policy evaluation
├── integration/    # Full checkout → SSH → checkin flow
└── adversarial/    # Prompt injection, scope violation, credential theft
```

## Project Motivation

Traditional PAM was built for human admins. AI agents are non-human identities
that authenticate, call APIs, and execute privileged operations autonomously —
often in milliseconds. This project explores what PAM looks like when the
"user" is an LLM agent.

Inspired by the CyberArk → Palo Alto acquisition and the broader NHI (Non-Human
Identity) security category emerging in 2025-2026.
