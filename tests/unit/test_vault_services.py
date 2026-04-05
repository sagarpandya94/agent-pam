"""
Unit tests for vault services: encryption, token_service, policy_engine
"""
import pytest
import os
os.environ["VAULT_ENCRYPTION_KEY"] = "test-key-placeholder"

from cryptography.fernet import Fernet
os.environ["VAULT_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

from vault.services.encryption import encrypt, decrypt
from vault.services.token_service import issue_token, verify_token
from vault.services.policy_engine import evaluate_command, PolicyDenied
from vault.models.policy import PolicyORM
import json


# ── Encryption ───────────────────────────────────────────────────────────────

class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "my-super-secret-private-key"
        ciphertext = encrypt(plaintext)
        assert ciphertext != plaintext
        assert decrypt(ciphertext) == plaintext

    def test_encrypt_produces_different_output_each_time(self):
        plaintext = "same-secret"
        assert encrypt(plaintext) != encrypt(plaintext)  # Fernet uses random IV

    def test_empty_string(self):
        assert decrypt(encrypt("")) == ""


# ── Token Service ─────────────────────────────────────────────────────────────

class TestTokenService:
    def test_issue_and_verify(self):
        token, expires_at = issue_token("agent-001", "prod-ec2-001", "policy-1")
        payload = verify_token(token)
        assert payload["sub"] == "agent-001"
        assert payload["credential_id"] == "prod-ec2-001"
        assert payload["type"] == "checkout"

    def test_tampered_token_raises(self):
        token, _ = issue_token("agent-001", "cred-001", "policy-1")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(ValueError, match="Invalid or expired token"):
            verify_token(tampered)

    def test_token_contains_expected_fields(self):
        token, expires_at = issue_token("agent-42", "cred-99", "pol-1", expire_minutes=5)
        payload = verify_token(token)
        assert "exp" in payload
        assert "iat" in payload
        assert payload["credential_id"] == "cred-99"


# ── Policy Engine ─────────────────────────────────────────────────────────────

def make_policy(allowed: list, denied: list = []) -> PolicyORM:
    p = PolicyORM()
    p.id = "test-policy"
    p.allowed_commands = json.dumps(allowed)
    p.denied_commands = json.dumps(denied)
    return p


class TestPolicyEngine:
    def test_allowed_command_passes(self):
        policy = make_policy(allowed=["df", "du", "ls"])
        evaluate_command(policy, "df -h")  # should not raise

    def test_denied_command_raises(self):
        policy = make_policy(allowed=["df", "ls"], denied=["rm"])
        with pytest.raises(PolicyDenied, match="explicitly denied"):
            evaluate_command(policy, "rm -rf /tmp/test")

    def test_command_not_in_allowed_raises(self):
        policy = make_policy(allowed=["df", "ls"])
        with pytest.raises(PolicyDenied, match="not in the allowed list"):
            evaluate_command(policy, "curl http://evil.com")

    def test_empty_allowed_list_permits_all(self):
        policy = make_policy(allowed=[])
        evaluate_command(policy, "anything goes")  # should not raise

    def test_case_insensitive_matching(self):
        policy = make_policy(allowed=["DF", "LS"])
        evaluate_command(policy, "df -h")   # lowercase should match uppercase allowed
        evaluate_command(policy, "LS /tmp")
