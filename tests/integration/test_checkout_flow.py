"""
Integration tests: full checkout → verify → checkin flow through the vault API.
Uses FastAPI TestClient with an in-memory SQLite DB.
"""
import pytest
import os
os.environ["VAULT_DB_URL"] = "sqlite:///./test_vault.db"
os.environ["VAULT_SECRET_KEY"] = "test-secret-key-for-integration"

from cryptography.fernet import Fernet
os.environ["VAULT_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

from fastapi.testclient import TestClient
from vault.main import app
from vault.db.database import init_db

init_db()
client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_vault():
    """Seed a credential and policy before each test."""
    client.post("/credentials/", json={
        "id": "test-ec2-001",
        "name": "Test EC2",
        "host": "localhost",
        "port": "2222",
        "username": "ubuntu",
        "password": "ubuntu123",
    })
    client.post("/policies/", json={
        "id": "test-policy-001",
        "name": "Test read-only policy",
        "credential_id": "test-ec2-001",
        "agent_pattern": "*",
        "allowed_commands": ["df", "ls", "uptime"],
        "denied_commands": ["rm", "curl"],
        "max_session_minutes": 15,
    })
    yield
    # Cleanup handled by fresh DB each test run


class TestCheckoutFlow:
    def test_successful_checkout(self):
        r = client.post("/checkout/", json={
            "agent_id": "test-agent-001",
            "credential_id": "test-ec2-001",
            "task_description": "Check disk usage",
        })
        assert r.status_code == 201
        data = r.json()
        assert "token" in data
        assert data["host"] == "localhost"
        assert "df" in data["allowed_commands"]

    def test_checkout_unknown_credential_returns_404(self):
        r = client.post("/checkout/", json={
            "agent_id": "test-agent-001",
            "credential_id": "nonexistent-cred",
            "task_description": "Some task",
        })
        assert r.status_code == 404

    def test_checkout_without_policy_returns_403(self):
        # Create a credential with no policy
        client.post("/credentials/", json={
            "id": "orphan-cred",
            "name": "No policy cred",
            "host": "localhost",
            "port": "22",
            "username": "ubuntu",
        })
        r = client.post("/checkout/", json={
            "agent_id": "test-agent-001",
            "credential_id": "orphan-cred",
            "task_description": "Should be denied",
        })
        assert r.status_code == 403

    def test_checkin_after_checkout(self):
        # Checkout first
        r = client.post("/checkout/", json={
            "agent_id": "test-agent-001",
            "credential_id": "test-ec2-001",
            "task_description": "Test checkin",
        })
        token = r.json()["token"]

        # Checkin
        r = client.post("/checkout/checkin", json={
            "token": token,
            "agent_id": "test-agent-001",
        })
        assert r.status_code == 200
        assert r.json()["status"] == "checked_in"

    def test_double_checkin_returns_409(self):
        r = client.post("/checkout/", json={
            "agent_id": "test-agent-001",
            "credential_id": "test-ec2-001",
            "task_description": "Double checkin test",
        })
        token = r.json()["token"]

        client.post("/checkout/checkin", json={"token": token, "agent_id": "test-agent-001"})
        r2 = client.post("/checkout/checkin", json={"token": token, "agent_id": "test-agent-001"})
        assert r2.status_code == 409

    def test_token_verify_valid(self):
        r = client.post("/checkout/", json={
            "agent_id": "test-agent-001",
            "credential_id": "test-ec2-001",
            "task_description": "Verify test",
        })
        token = r.json()["token"]

        r2 = client.post(f"/checkout/verify?token={token}")
        assert r2.status_code == 200
        assert r2.json()["valid"] is True
