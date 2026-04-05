from fastapi import FastAPI
from contextlib import asynccontextmanager
from vault.db.database import init_db
from vault.routes import credentials, checkout, policies


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="agent-pam Vault",
    description="PAM Vault — credential storage, JIT checkout, and policy enforcement for AI agents",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(credentials.router)
app.include_router(checkout.router)
app.include_router(policies.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "agent-pam-vault"}
