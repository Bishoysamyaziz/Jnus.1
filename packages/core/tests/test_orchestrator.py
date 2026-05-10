"""Tests for Orchestrator"""
from __future__ import annotations

import pytest

from packages.core.orchestrator import Orchestrator
from packages.core.models import IntentType


@pytest.fixture
def orchestrator():
    return Orchestrator()


@pytest.mark.asyncio
async def test_process_code_message(orchestrator):
    """Should process a CODE message successfully"""
    chunks = []
    async for chunk in orchestrator.process(
        message="write a Python function to calculate factorial",
        session_id="test_session",
        user_id="test_user",
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    # Should have at least: status, intent, agent, status, status, execute chunks, done
    assert any(c.type == "intent" for c in chunks)
    assert any(c.type == "done" for c in chunks)
    assert not any(c.type == "error" for c in chunks)


@pytest.mark.asyncio
async def test_process_research_message(orchestrator):
    """Should process a RESEARCH message successfully"""
    chunks = []
    async for chunk in orchestrator.process(
        message="research the latest AI trends",
        session_id="test_session_2",
        user_id="test_user",
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert any(c.type == "intent" for c in chunks)
    assert any(c.type == "done" for c in chunks)


@pytest.mark.asyncio
async def test_process_empty_message(orchestrator):
    """Should handle empty message gracefully"""
    chunks = []
    async for chunk in orchestrator.process(
        message="",
        session_id="test_session_3",
        user_id="test_user",
    ):
        chunks.append(chunk)
    # Should still produce some output (may be error or done)
    assert len(chunks) > 0


@pytest.mark.asyncio
async def test_process_with_context(orchestrator):
    """Should process with additional context"""
    chunks = []
    async for chunk in orchestrator.process(
        message="analyze this dataset",
        session_id="test_session_4",
        user_id="test_user",
        context={"preferred_language": "python"},
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert any(c.type == "done" for c in chunks)


@pytest.mark.asyncio
async def test_health_check(orchestrator):
    """Health check should return system status"""
    health = await orchestrator.health_check()
    assert health["status"] == "ok"
    assert "classifier" in health
    assert "agents_registered" in health


@pytest.mark.asyncio
async def test_get_session(orchestrator):
    """Should return session data"""
    # Process a message first to create a session
    async for _ in orchestrator.process(
        message="hello",
        session_id="session_for_get",
        user_id="test_user",
    ):
        pass
    session = orchestrator.get_session("session_for_get")
    assert session is not None
    assert "messages" in session


@pytest.mark.asyncio
async def test_get_active_sessions(orchestrator):
    """Should return active sessions"""
    sessions = orchestrator.get_active_sessions()
    assert isinstance(sessions, list)


@pytest.mark.asyncio
async def test_stream(orchestrator):
    """Stream should yield SSE-formatted strings"""
    count = 0
    async for event in orchestrator.stream(
        message="write a simple API",
        session_id="test_stream",
        user_id="test_user",
    ):
        assert event.startswith("data: ")
        count += 1
    assert count > 0


@pytest.mark.asyncio
async def test_concurrent_sessions(orchestrator):
    """Should handle multiple sessions independently"""
    import asyncio

    async def process_session(session_id: str, message: str):
        chunks = []
        async for chunk in orchestrator.process(
            message=message,
            session_id=session_id,
            user_id="test_user",
        ):
            chunks.append(chunk)
        return chunks

    results = await asyncio.gather(
        process_session("concurrent_1", "write code"),
        process_session("concurrent_2", "research topic"),
    )
    assert len(results) == 2
    for chunks in results:
        assert any(c.type == "done" for c in chunks)
