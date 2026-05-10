"""Tests for Orchestrator"""
from __future__ import annotations

import pytest

from packages.core.orchestrator import Orchestrator
from packages.core.models import Task, IntentType, MemoryContext


@pytest.fixture
def orchestrator():
    return Orchestrator()


@pytest.mark.asyncio
async def test_process_code_task(orchestrator):
    """Should process a CODE task successfully"""
    task = Task(description="write a Python function", intent_type=IntentType.CODE)
    memory = MemoryContext(user_id="test_user", session_id="test_session")
    result = await orchestrator.process(task, memory)
    assert result.success
    assert result.framework is not None
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_process_research_task(orchestrator):
    """Should process a RESEARCH task successfully"""
    task = Task(description="research AI trends", intent_type=IntentType.RESEARCH)
    memory = MemoryContext(user_id="test_user", session_id="test_session")
    result = await orchestrator.process(task, memory)
    assert result.success
    assert result.framework is not None


@pytest.mark.asyncio
async def test_process_with_empty_task(orchestrator):
    """Should handle empty task description"""
    task = Task(description="", intent_type=IntentType.CONVERSATION)
    memory = MemoryContext(user_id="test_user", session_id="test_session")
    result = await orchestrator.process(task, memory)
    assert result.success is False
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_process_with_none_task(orchestrator):
    """Should handle None task"""
    with pytest.raises(ValueError):
        await orchestrator.process(None, MemoryContext(user_id="test", session_id="test"))


@pytest.mark.asyncio
async def test_process_with_none_memory(orchestrator):
    """Should handle None memory"""
    task = Task(description="test", intent_type=IntentType.CONVERSATION)
    with pytest.raises(ValueError):
        await orchestrator.process(task, None)


@pytest.mark.asyncio
async def test_health_check(orchestrator):
    """Health check should return system status"""
    health = await orchestrator.health()
    assert "status" in health
    assert "agents" in health
    assert "memory" in health
    assert health["status"] in ["healthy", "degraded"]


@pytest.mark.asyncio
async def test_get_available_agents(orchestrator):
    """Should return list of available agents"""
    agents = orchestrator.get_available_agents()
    assert len(agents) > 0
    assert all("name" in a and "capabilities" in a for a in agents)


@pytest.mark.asyncio
async def test_get_agent_stats(orchestrator):
    """Should return agent usage statistics"""
    stats = orchestrator.get_agent_stats()
    assert isinstance(stats, dict)
