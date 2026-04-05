"""
Fernet symmetric encryption for secrets at rest.
Key is loaded from env (VAULT_ENCRYPTION_KEY).
If not set, a new key is generated and printed — store it in .env immediately.
"""
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

def _load_or_generate_key() -> bytes:
    key = os.getenv("VAULT_ENCRYPTION_KEY")
    if not key:
        new_key = Fernet.generate_key()
        print(
            f"\n[VAULT] No VAULT_ENCRYPTION_KEY found. Generated a new one:\n"
            f"  VAULT_ENCRYPTION_KEY={new_key.decode()}\n"
            f"  Add this to your .env file NOW or secrets will be unrecoverable after restart.\n"
        )
        return new_key
    return key.encode()


_fernet = Fernet(_load_or_generate_key())


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string. Returns base64-encoded ciphertext."""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a ciphertext string. Returns plaintext."""
    return _fernet.decrypt(ciphertext.encode()).decode()
