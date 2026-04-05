from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Vault
    vault_secret_key: str = "dev-secret-change-in-production"
    vault_db_url: str = "sqlite:///./vault.db"
    vault_token_expire_minutes: int = 15
    vault_encryption_key: Optional[str] = None

    # Agent identity header
    agent_id_header: str = "X-Agent-ID"

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()