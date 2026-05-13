"""OneAgent OS — FastAPI Backend (Production MVP)
/api endpoints: health, chat, run, usage
"""
from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from .database import init_db, UsageTracker
from .agent_service import AgentService

# ── App State ──────────────────────────────────────────────────────

class AppState:
    agent: AgentService | None = None
    usage: UsageTracker | None = None
    start_time: float = time.time()

state = AppState()

# ── Simple Auth ──────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"

import jwt as pyjwt

def get_current_user(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = pyjwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return str(payload.get("sub", "anonymous"))
        except Exception:
            pass
    return "anonymous"

def require_user(request: Request) -> str:
    user_id = get_current_user(request)
    if user_id == "anonymous":
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id

# ── Lifespan ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("OneAgent OS API starting...")
    try:
        init_db()
        print("Database initialized")
    except Exception as e:
        print(f"Database init failed: {e}")
    state.agent = AgentService(timeout=600)
    state.usage = UsageTracker()
    yield
    state.agent = None
    state.usage = None
    print("OneAgent OS API shutting down")

app = FastAPI(
    title="OneAgent OS API",
    description="AI Developer Agent - Build, Fix, Explain",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────
cors_origins_str = os.getenv("ALLOWED_ORIGINS", "")
if cors_origins_str:
    cors_origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]
else:
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://jnus.pages.dev",
        "https://oneagent-os.pages.dev",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)

# ── Request ID Middleware ────────────────────────────────────────────

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    user_id = get_current_user(request)
    print(f"[{request_id}] {request.method} {request.url.path} | user={user_id} | {duration:.3f}s | {response.status_code}")
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    return response

# ── Models ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    user_id: Optional[str] = Field(None, description="User ID")
    mode: str = Field(default="build", description="Mode: build | fix | explain")
    repo_path: Optional[str] = Field(None, description="Repo path for fix mode")

class RunResponse(BaseModel):
    task_id: str
    status: str
    output: str
    files: list[str]
    logs: list[str]
    duration: float
    error: Optional[str] = None

class UsageResponse(BaseModel):
    daily_used: int
    daily_limit: int
    daily_remaining: int
    total_tasks: int
    last_task: Optional[dict] = None

# ── Endpoints ────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    uptime = time.time() - state.start_time
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": round(uptime, 2),
        "services": {
            "agent": "ready" if state.agent else "unavailable",
            "database": "ready" if state.usage else "unavailable",
        },
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    if not state.agent:
        raise HTTPException(status_code=503, detail="Service not initialized")
    user_id = request.user_id or get_current_user(request) or "anonymous"

    async def event_generator():
        try:
            yield "data: " + json.dumps({"type": "status", "content": "Thinking..."}) + "\n\n"
            result = await state.agent.run_task(
                prompt=request.message,
                mode=request.mode,
                repo_path=request.repo_path,
            )
            if result["success"]:
                for line in result["output"].split("\n"):
                    if line.strip():
                        yield "data: " + json.dumps({"type": "token", "content": line + "\n"}) + "\n\n"
                if result["files"]:
                    yield "data: " + json.dumps({"type": "files", "content": result["files"]}) + "\n\n"
                yield "data: " + json.dumps({"type": "done", "content": "Task completed!"}) + "\n\n"
            else:
                err_msg = str(result.get("error", "Unknown error"))
                yield "data: " + json.dumps({"type": "error", "content": "Error: " + err_msg}) + "\n\n"
        except Exception as e:
            yield "data: " + json.dumps({"type": "error", "content": "System error: " + str(e)}) + "\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@app.post("/run", response_model=RunResponse)
async def run_task(request: ChatRequest, user_id: str = Depends(require_user)):
    if not state.agent or not state.usage:
        raise HTTPException(status_code=503, detail="Service not initialized")
    allowed, remaining = state.usage.check_limit(user_id)
    if not allowed:
        raise HTTPException(status_code=429, detail="Daily usage limit reached. Remaining: " + str(remaining) + " runs")
    start = time.time()
    result = await state.agent.run_task(
        prompt=request.message,
        mode=request.mode,
        repo_path=request.repo_path,
    )
    duration = time.time() - start
    state.usage.log_usage(
        user_id=user_id, action="run_task",
        prompt=request.message, mode=request.mode,
        result_summary=result["output"][:200] if result["output"] else "",
        duration=duration, status="completed" if result["success"] else "failed",
        error=result["error"],
    )
    task_id = state.usage.save_task(
        user_id=user_id, prompt=request.message, mode=request.mode,
        status="completed" if result["success"] else "failed",
        files=result["files"], logs=result["logs"],
        duration=duration, error=result["error"],
    )
    return RunResponse(
        task_id=task_id, status="completed" if result["success"] else "failed",
        output=result["output"], files=result["files"],
        logs=result["logs"], duration=round(duration, 2),
        error=result["error"],
    )

@app.get("/usage", response_model=UsageResponse)
async def get_usage(user_id: str = Depends(get_current_user)):
    if not state.usage:
        raise HTTPException(status_code=503, detail="Service not initialized")
    stats = state.usage.get_usage_stats(user_id)
    return UsageResponse(**stats)

@app.get("/tasks")
async def get_tasks(limit: int = 10, user_id: str = Depends(get_current_user)):
    if not state.usage:
        raise HTTPException(status_code=503, detail="Service not initialized")
    tasks = state.usage.get_tasks(user_id, limit=limit)
    return {"tasks": tasks, "total": len(tasks)}

@app.post("/auth/login")
async def login(email: str, password: str):
    user_id = str(uuid.uuid4())
    if state.usage:
        state.usage.create_user(user_id, email)
    token = pyjwt.encode(
        {"sub": user_id, "email": email, "iat": int(time.time()), "exp": int(time.time()) + 86400 * 7},
        SECRET_KEY, algorithm=JWT_ALGORITHM,
    )
    return {"access_token": token, "token_type": "bearer", "user_id": user_id, "email": email}

@app.post("/auth/register")
async def register(email: str, password: str):
    user_id = str(uuid.uuid4())
    if state.usage:
        state.usage.create_user(user_id, email)
    token = pyjwt.encode(
        {"sub": user_id, "email": email, "iat": int(time.time()), "exp": int(time.time()) + 86400 * 7},
        SECRET_KEY, algorithm=JWT_ALGORITHM,
    )
    return {"access_token": token, "token_type": "bearer", "user_id": user_id, "email": email}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "status_code": exc.status_code})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    uvicorn.run("packages.api.main:app", host=host, port=port,
                reload=os.getenv("API_RELOAD", "false").lower() in {"1", "true", "yes"},
                log_level="info")
