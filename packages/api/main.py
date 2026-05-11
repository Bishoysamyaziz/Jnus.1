"""OneAgent OS — FastAPI Backend
Main API server with SSE streaming for real-time agent responses.
Supports both native /v1/chat and OpenAI-compatible /v1/chat/completions.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Add parent to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.orchestrator import Orchestrator
from core.base_agent import AgentRegistry
from core.intent.classifier import IntentClassifier
from core.models import StreamChunk

# ── Auth ───────────────────────────────────────────────────────────
from fastapi_users import FastAPIUsers
from .auth import auth_backend, UserRead, UserCreate

fastapi_users = FastAPIUsers(
    get_user_manager=lambda: None,  # Will be replaced with real DB-backed manager
    auth_backends=[auth_backend],
)

# ── Rate Limiting (Redis-based) ────────────────────────────────────
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


# ── App State ──────────────────────────────────────────────────────

class AppState:
    orchestrator: Orchestrator | None = None
    start_time: float = time.time()


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    # Initialize orchestrator
    classifier = IntentClassifier()
    orchestrator = Orchestrator(classifier=classifier)
    state.orchestrator = orchestrator
    yield
    # Cleanup on shutdown
    state.orchestrator = None


app = FastAPI(
    title="OneAgent OS API",
    description="Unified API for 24 AI frameworks",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend from any origin in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate Limiting ──────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379"),
    default_limits=["200/hour"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Auth Routes ────────────────────────────────────────────────────
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)


# ── Models ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User ID")
    context: Optional[dict[str, Any]] = Field(None, description="Additional context")


class ChatResponse(BaseModel):
    session_id: str
    status: str = "ok"


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    services: dict[str, str]


# ── OpenAI-Compatible Models ───────────────────────────────────────

class OpenAIMessage(BaseModel):
    role: str = "user"
    content: str


class OpenAICompletionRequest(BaseModel):
    model: str = Field(default="claude-s4", description="Model name")
    messages: list[OpenAIMessage] = Field(..., description="Chat messages")
    stream: bool = Field(default=True, description="Whether to stream the response")
    session_id: Optional[str] = Field(None, description="Session ID")
    user_id: Optional[str] = Field(None, description="User ID")


# ── Endpoints ───────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    uptime = time.time() - state.start_time
    return HealthResponse(
        status="ok",
        version="1.0.0",
        uptime_seconds=uptime,
        services={
            "orchestrator": "ready",
            "classifier": "ready",
            "agents": f"{len(AgentRegistry._agents)} registered",
        },
    )


@app.post("/v1/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint with SSE streaming

    Sends Server-Sent Events:
    - type: "status" — progress updates
    - type: "intent" — detected intent
    - type: "agent" — selected agent
    - type: "token" — actual response content
    - type: "error" — error messages
    - type: "done" — completion signal
    """
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id or "anonymous"

    async def event_generator():
        try:
            async for chunk in state.orchestrator.process(
                message=request.message,
                session_id=session_id,
                user_id=user_id,
                context=request.context or {},
            ):
                yield chunk.to_sse()
        except Exception as e:
            error_chunk = StreamChunk(
                type="error",
                content=f"❌ خطأ في النظام: {str(e)}",
                metadata={"error": str(e)},
            )
            yield error_chunk.to_sse()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/v1/chat/completions")
async def chat_completions(request: OpenAICompletionRequest):
    """OpenAI-compatible chat completions endpoint.

    Accepts OpenAI-style request format and returns OpenAI-style SSE stream.
    This allows any OpenAI-compatible client (including the frontend) to connect.
    """
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    # Extract the last user message
    user_message = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_message = msg.content
            break

    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found")

    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id or "anonymous"

    async def openai_event_generator():
        """Convert native StreamChunks to OpenAI-compatible SSE format"""
        full_content = ""
        intent_detected = None
        agent_selected = None
        is_error = False

        try:
            async for chunk in state.orchestrator.process(
                message=user_message,
                session_id=session_id,
                user_id=user_id,
                context={},
            ):
                if chunk.type == "token":
                    full_content += chunk.content
                    # OpenAI format: data: {"choices":[{"delta":{"content":"..."},"index":0}]}
                    openai_chunk = {
                        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk.content},
                            "finish_reason": None,
                        }],
                    }
                    yield f"data: {json.dumps(openai_chunk)}\n\n"

                elif chunk.type == "intent":
                    intent_detected = chunk.metadata.get("intent", "")
                    # Send as a special delta with intent metadata
                    intent_chunk = {
                        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": f"\n🔍 **Intent:** {chunk.content}\n",
                            },
                            "finish_reason": None,
                        }],
                    }
                    yield f"data: {json.dumps(intent_chunk)}\n\n"

                elif chunk.type == "agent":
                    agent_selected = chunk.metadata.get("primary", "")
                    agent_chunk = {
                        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "content": f"\n🤖 **Agent:** {chunk.content}\n",
                            },
                            "finish_reason": None,
                        }],
                    }
                    yield f"data: {json.dumps(agent_chunk)}\n\n"

                elif chunk.type == "status":
                    # Send status updates as content
                    status_chunk = {
                        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "content": f"\n⏳ {chunk.content}\n",
                            },
                            "finish_reason": None,
                        }],
                    }
                    yield f"data: {json.dumps(status_chunk)}\n\n"

                elif chunk.type == "error":
                    is_error = True
                    error_chunk = {
                        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "content": f"\n⚠️ {chunk.content}\n",
                            },
                            "finish_reason": None,
                        }],
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"

        except Exception as e:
            error_chunk = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": f"\n❌ **Error:** {str(e)}\n"},
                    "finish_reason": None,
                }],
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

        # Send the final [DONE] signal
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        openai_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/v1/agents")
async def list_agents():
    """List all available agents and their capabilities"""
    agents = AgentRegistry.list_agents()
    return {
        "agents": agents,
        "total": len(agents),
    }


@app.get("/v1/history")
async def get_history(session_id: str | None = None, user_id: str | None = None):
    """Get conversation history"""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    if session_id:
        session = state.orchestrator.get_session(session_id)
        if session:
            return {"session_id": session_id, "messages": session["messages"]}
        return {"session_id": session_id, "messages": []}

    sessions = state.orchestrator.get_active_sessions()
    return {"sessions": sessions}


@app.delete("/v1/history/{session_id}")
async def delete_history(session_id: str):
    """Delete a conversation session"""
    # Sessions are auto-managed; this is a no-op for now
    return {"status": "deleted", "session_id": session_id}


@app.get("/metrics")
async def metrics():
    """Basic Prometheus-style metrics"""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    sessions = state.orchestrator.get_active_sessions()
    return {
        "active_sessions": len(sessions),
        "uptime_seconds": time.time() - state.start_time,
        "agents_registered": len(AgentRegistry._agents),
    }


# ── Run ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    uvicorn.run("packages.api.main:app", host=host, port=port, reload=True)
