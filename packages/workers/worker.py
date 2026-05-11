"""OneAgent OS — Celery Workers for Long-Running Tasks"""
from __future__ import annotations

import asyncio
import os

from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

app = Celery(
    "oneagent",
    broker=os.getenv("REDIS_URL",  "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/1"),
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_time_limit=300,          # 5 min (= BaseAgent.timeout)
    task_soft_time_limit=240,     # warning بعد 4 min
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


@app.task(bind=True, max_retries=3, default_retry_delay=5)
def run_agent_task(
    self,
    message: str,
    session_id: str,
    user_id: str = "anonymous",
) -> dict:
    """Long-running agent task في الخلفية.
    بيُستدعى من الـ API لما complexity > 0.85.
    """
    try:
        from packages.core.orchestrator import Orchestrator
        from packages.core.intent.classifier import IntentClassifier

        orchestrator = Orchestrator(classifier=IntentClassifier())
        chunks = []

        async def collect():
            async for chunk in orchestrator.process(message, session_id, user_id):
                chunks.append(chunk.to_sse())

        asyncio.run(collect())
        logger.info(f"Task done: {session_id} — {len(chunks)} chunks")
        return {"session_id": session_id, "chunks": len(chunks), "status": "done"}

    except Exception as exc:
        logger.error(f"Task failed: {session_id} — {exc}")
        raise self.retry(exc=exc)
