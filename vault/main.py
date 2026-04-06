from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from vault.db.database import init_db
from vault.routes import credentials, checkout, policies


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="agent-pam Vault",
    description="PAM Vault for AI agents",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(credentials.router)
app.include_router(checkout.router)
app.include_router(policies.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "agent-pam-vault"}