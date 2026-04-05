"""
agent/api.py — Thin FastAPI wrapper around pam_agent.py
Exposes the agent over HTTP with Server-Sent Events (SSE) for live streaming.
The React UI calls this on port 8001.
"""
import json
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor

from agent.pam_agent import run_agent
from audit.logger import get_recent_events, get_events_for_session

app = FastAPI(
    title="agent-pam Agent API",
    description="HTTP interface for the Claude PAM agent with SSE streaming",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=4)


class RunTaskRequest(BaseModel):
    task: str
    credential_id: str = "prod-ec2-001"


@app.post("/agent/run")
async def run_task_stream(payload: RunTaskRequest):
    """
    Run the agent and stream output back via SSE.
    Each SSE event is a JSON object: { type, content }

    Event types:
      - "stream"   — agent text / tool call output chunk
      - "done"     — task complete, content = final response
      - "error"    — something went wrong
    """
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def stream_callback(text: str):
        """Called from agent thread — puts SSE events onto the async queue."""
        asyncio.run_coroutine_threadsafe(
            queue.put({"type": "stream", "content": text}),
            loop,
        )

    def run_in_thread():
        try:
            result = run_agent(
                task=payload.task,
                credential_id=payload.credential_id,
                stream_callback=stream_callback,
            )
            asyncio.run_coroutine_threadsafe(
                queue.put({"type": "done", "content": result}),
                loop,
            )
        except Exception as e:
            asyncio.run_coroutine_threadsafe(
                queue.put({"type": "error", "content": str(e)}),
                loop,
            )
        finally:
            asyncio.run_coroutine_threadsafe(
                queue.put(None),  # sentinel
                loop,
            )

    async def event_generator():
        # Start agent in thread pool
        loop.run_in_executor(executor, run_in_thread)

        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/agent/sessions")
def list_sessions():
    """Return recent audit events for the session list view."""
    events = get_recent_events(limit=200)
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "agent_id": e.agent_id,
            "token": e.token,
            "severity": e.severity,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "detail": json.loads(e.detail) if e.detail else {},
        }
        for e in events
    ]


@app.get("/agent/sessions/{token}")
def get_session_events(token: str):
    """Return all audit events for a specific session token (for replay)."""
    events = get_events_for_session(token)
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "agent_id": e.agent_id,
            "token": e.token,
            "severity": e.severity,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "detail": json.loads(e.detail) if e.detail else {},
        }
        for e in events
    ]


@app.get("/health")
def health():
    return {"status": "ok", "service": "agent-pam-agent-api"}
