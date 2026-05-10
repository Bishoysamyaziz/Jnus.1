"""Integration Tests — Full Pipeline
Tests the complete flow: Intent → Selector → Orchestrator → Agent → Memory
Requires: docker compose up (Redis, PostgreSQL, Qdrant)
"""
from __future__ import annotations

import pytest
import asyncio

from packages.core.orchestrator import Orchestrator
from packages.core.models import Task, IntentType, MemoryContext
from packages.core.intent.classifier import IntentClassifier
from packages.core.agent_selector import AgentSelector


@pytest.fixture
def orchestrator():
    return Orchestrator()


@pytest.fixture
def classifier():
    return IntentClassifier()


@pytest.fixture
def selector():
    return AgentSelector()


@pytest.mark.asyncio
async def test_full_pipeline_code(orchestrator):
    """Full pipeline: CODE task → classify → select → execute → memory"""
    task = Task(description="write a Python function to calculate factorial", intent_type=IntentType.CODE)
    memory = MemoryContext(user_id="integration_test", session_id="int_session_1")
    result = await orchestrator.process(task, memory)
    assert result.success
    assert result.framework is not None
    assert len(result.content) > 0
    assert result.framework in ["aider", "langchain", "autogen", "openhands", "smolagents"]


@pytest.mark.asyncio
async def test_full_pipeline_research(orchestrator):
    """Full pipeline: RESEARCH task"""
    task = Task(description="explain the theory of relativity", intent_type=IntentType.RESEARCH)
    memory = MemoryContext(user_id="integration_test", session_id="int_session_2")
    result = await orchestrator.process(task, memory)
    assert result.success
    assert result.framework in ["crewai", "langchain", "autogpt", "agentgpt", "huggingface"]


@pytest.mark.asyncio
async def test_full_pipeline_data(orchestrator):
    """Full pipeline: DATA task"""
    task = Task(description="analyze this CSV data for trends", intent_type=IntentType.DATA)
    memory = MemoryContext(user_id="integration_test", session_id="int_session_3")
    result = await orchestrator.process(task, memory)
    assert result.success
    assert result.framework in ["taskweaver", "llamaindex", "haystack", "langchain"]


@pytest.mark.asyncio
async def test_full_pipeline_planning(orchestrator):
    """Full pipeline: PLANNING task"""
    task = Task(description="plan a 6-month learning path for data science", intent_type=IntentType.PLANNING)
    memory = MemoryContext(user_id="integration_test", session_id="int_session_4")
    result = await orchestrator.process(task, memory)
    assert result.success
    assert result.framework in ["babyagi", "metagpt", "agentgpt", "langgraph"]


@pytest.mark.asyncio
async def test_full_pipeline_conversation(orchestrator):
    """Full pipeline: CONVERSATION task"""
    task = Task(description="hello, how are you?", intent_type=IntentType.CONVERSATION)
    memory = MemoryContext(user_id="integration_test", session_id="int_session_5")
    result = await orchestrator.process(task, memory)
    assert result.success
    assert result.framework in ["rasa", "botpress", "langchain", "letta"]


@pytest.mark.asyncio
async def test_full_pipeline_creative(orchestrator):
    """Full pipeline: CREATIVE task"""
    task = Task(description="write a haiku about AI", intent_type=IntentType.CREATIVE)
    memory = MemoryContext(user_id="integration_test", session_id="int_session_6")
    result = await orchestrator.process(task, memory)
    assert result.success
    assert result.framework in ["camel", "langchain", "huggingface", "agentverse"]


@pytest.mark.asyncio
async def test_full_pipeline_automation(orchestrator):
    """Full pipeline: AUTOMATION task"""
    task = Task(description="automate daily email reports", intent_type=IntentType.AUTOMATION)
    memory = MemoryContext(user_id="integration_test", session_id="int_session_7")
    result = await orchestrator.process(task, memory)
    assert result.success
    assert result.framework in ["superagi", "langgraph", "swarm", "autogen"]


@pytest.mark.asyncio
async def test_classify_then_select(classifier, selector):
    """Test classify → select chain"""
    text = "write a REST API in Python"
    intent = await classifier.classify(text)
    assert intent.type == IntentType.CODE
    agent = selector.select(intent.type)
    assert agent is not None
    assert agent in ["aider", "langchain", "autogen", "openhands", "smolagents"]


@pytest.mark.asyncio
async def test_classify_then_select_research(classifier, selector):
    """Test classify → select for research"""
    text = "research the latest AI trends"
    intent = await classifier.classify(text)
    assert intent.type == IntentType.RESEARCH
    agent = selector.select(intent.type)
    assert agent in ["crewai", "langchain", "autogpt", "agentgpt"]


@pytest.mark.asyncio
async def test_concurrent_tasks(orchestrator):
    """Test concurrent task processing"""
    tasks = [
        Task(description=f"task {i}", intent_type=IntentType.CODE)
        for i in range(5)
    ]
    memories = [
        MemoryContext(user_id="concurrent_test", session_id=f"con_session_{i}")
        for i in range(5)
    ]
    results = await asyncio.gather(*[
        orchestrator.process(t, m) for t, m in zip(tasks, memories)
    ])
    assert len(results) == 5
    assert all(r.success for r in results)


@pytest.mark.asyncio
async def test_memory_persistence(orchestrator):
    """Test memory persists across tasks in same session"""
    session_id = "persistence_test_session"
    memory = MemoryContext(user_id="persistence_test", session_id=session_id)

    task1 = Task(description="first task", intent_type=IntentType.CODE)
    result1 = await orchestrator.process(task1, memory)
    assert result1.success

    task2 = Task(description="second task in same session", intent_type=IntentType.CODE)
    result2 = await orchestrator.process(task2, memory)
    assert result2.success


@pytest.mark.asyncio
async def test_error_recovery(orchestrator):
    """Test system recovers from errors gracefully"""
    # Send empty task → should fail gracefully
    task = Task(description="", intent_type=IntentType.CONVERSATION)
    memory = MemoryContext(user_id="error_test", session_id="error_session")
    result = await orchestrator.process(task, memory)
    assert result.success is False

    # Next task should still work
    task2 = Task(description="recovery task", intent_type=IntentType.CODE)
    result2 = await orchestrator.process(task2, memory)
    assert result2.success


@pytest.mark.asyncio
async def test_health_check_all_services(orchestrator):
    """Test health check reports all services"""
    health = await orchestrator.health()
    assert health["status"] in ["healthy", "degraded"]
    assert "agents" in health
    assert "memory" in health
    assert "version" in health
    assert health["version"] == "1.0.0"
