"""
PraisonAI Secured API Server

Starts a FastAPI server that activates agents on incoming HTTP requests.
Agents are idle until a request arrives — no background polling.

Endpoints:
    POST /chat          — Send a message, get agent response
    POST /chat/stream   — Send a message, get SSE streaming response
    GET  /health        — Health check
    GET  /docs          — Swagger UI
"""

import os
import time
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from praisonaiagents import Agent

# ── Configuration ────────────────────────────────────────────────────────────

PORT = int(os.environ.get("PORT", 8765))
HOST = os.environ.get("HOST", "127.0.0.1")
MODEL = os.environ.get("MODEL", "openai/gpt-4o-mini")

# ── Agent setup (created once, reused per request) ───────────────────────────

assistant = Agent(
    name="assistant",
    role="AI Assistant",
    goal="Help users with their requests accurately and efficiently",
    instructions=(
        "You are a helpful AI assistant. Respond clearly and accurately. "
        "If you don't know something, say so."
    ),
    llm=MODEL,
)

# ── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="PraisonAI Secured Server",
    description="Security-hardened PraisonAI agent server",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("CORS_ORIGINS", "http://localhost:*")],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    model: str
    elapsed_seconds: float


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to the agent and get a response."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    start = time.time()

    # Override model per-request if provided
    if req.model:
        assistant.llm = req.model

    result = assistant.start(req.message)
    elapsed = time.time() - start

    return ChatResponse(
        response=str(result),
        model=assistant.llm or MODEL,
        elapsed_seconds=round(elapsed, 2),
    )


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Send a message and get a streaming SSE response."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async def generate():
        result = assistant.start(req.message)
        # PraisonAI returns full response; yield it as a single SSE event
        yield {"event": "message", "data": str(result)}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(generate())


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\nPraisonAI Secured Server starting on http://{HOST}:{PORT}")
    print(f"Model: {MODEL}\n")
    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )
