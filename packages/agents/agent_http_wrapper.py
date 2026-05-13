"""HTTP wrapper — runs inside each agent's Docker container.
Exposes /health and /execute endpoints for the Orchestrator to call.
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Optional

from fastapi import FastAPI
from pydantic import BaseModel

sys.path.insert(0, "/app")

app = FastAPI(title="Agent HTTP Wrapper")

AGENT_CLASS = os.getenv("AGENT_CLASS", "")
AGENT_MODULE = os.getenv("AGENT_MODULE", "")


def get_agent():
    """Dynamically import and instantiate the agent class."""
    if not AGENT_CLASS or not AGENT_MODULE:
        raise ValueError("AGENT_CLASS and AGENT_MODULE env vars required")
    mod = importlib.import_module(AGENT_MODULE)
    cls = getattr(mod, AGENT_CLASS)
    return cls()


class TaskRequest(BaseModel):
    message: str
    session_id: str = ""
    context: dict = {}


class TaskResponse(BaseModel):
    success: bool
    content: str
    agent: str
    error: Optional[str] = None
    duration_ms: float = 0


@app.get("/health")
async def health():
    return {"status": "ok", "agent": AGENT_CLASS, "module": AGENT_MODULE}


@app.post("/execute", response_model=TaskResponse)
async def execute(req: TaskRequest):
    import time
    from core.models import Task, MemoryContext, Intent, IntentType

    start = time.time()
    try:
        agent = get_agent()
        task = Task(
            id="t1",
            description=req.message,
            intent=Intent(type=IntentType.CODE, confidence=0.9, sub_tasks=[]),
            assigned_agent=AGENT_CLASS,
        )
        memory = MemoryContext(
            session_id=req.session_id,
            messages=[],
            user_preferences={},
        )
        result = await agent.execute(task, memory)
        duration = (time.time() - start) * 1000
        return TaskResponse(
            success=result.success,
            content=result.content,
            agent=AGENT_CLASS,
            error=result.error,
            duration_ms=duration,
        )
    except Exception as e:
        duration = (time.time() - start) * 1000
        return TaskResponse(
            success=False,
            content="",
            agent=AGENT_CLASS,
            error=str(e),
            duration_ms=duration,
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
