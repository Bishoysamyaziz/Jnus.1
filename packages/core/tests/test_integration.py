"""Integration Tests — Full Pipeline
Tests the complete flow: Intent → Selector → Orchestrator → Agent → Memory
"""
from __future__ import annotations

import pytest
import asyncio

from packages.core.orchestrator import Orchestrator
from packages.core.intent.classifier import IntentClassifier
from packages.core.agent_selector import select_agent
from packages.core.models import IntentType


@pytest.fixture
def orchestrator():
    return Orchestrator()


@pytest.fixture
def classifier():
    return IntentClassifier()


@pytest.mark.asyncio
async def test_full_pipeline_code(orchestrator):
    """Full pipeline: CODE message → classify → select → execute"""
    chunks = []
    async for chunk in orchestrator.process(
        message="write a Python function to calculate factorial",
        session_id="int_session_1",
        user_id="integration_test",
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert any(c.type == "intent" for c in chunks)
    assert any(c.type == "done" for c in chunks)


@pytest.mark.asyncio
async def test_full_pipeline_research(orchestrator):
    """Full pipeline: RESEARCH message"""
    chunks = []
    async for chunk in orchestrator.process(
        message="explain the theory of relativity",
        session_id="int_session_2",
        user_id="integration_test",
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert any(c.type == "done" for c in chunks)


@pytest.mark.asyncio
async def test_full_pipeline_data(orchestrator):
    """Full pipeline: DATA message"""
    chunks = []
    async for chunk in orchestrator.process(
        message="analyze this CSV data for trends",
        session_id="int_session_3",
        user_id="integration_test",
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert any(c.type == "done" for c in chunks)


@pytest.mark.asyncio
async def test_full_pipeline_planning(orchestrator):
    """Full pipeline: PLANNING message"""
    chunks = []
    async for chunk in orchestrator.process(
        message="plan a 6-month learning path for data science",
        session_id="int_session_4",
        user_id="integration_test",
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert any(c.type == "done" for c in chunks)


@pytest.mark.asyncio
async def test_full_pipeline_conversation(orchestrator):
    """Full pipeline: CONVERSATION message"""
    chunks = []
    async for chunk in orchestrator.process(
        message="hello, how are you?",
        session_id="int_session_5",
        user_id="integration_test",
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert any(c.type == "done" for c in chunks)


@pytest.mark.asyncio
async def test_full_pipeline_creative(orchestrator):
    """Full pipeline: CREATIVE message"""
    chunks = []
    async for chunk in orchestrator.process(
        message="write a haiku about AI",
        session_id="int_session_6",
        user_id="integration_test",
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert any(c.type == "done" for c in chunks)


@pytest.mark.asyncio
async def test_full_pipeline_automation(orchestrator):
    """Full pipeline: AUTOMATION message"""
    chunks = []
    async for chunk in orchestrator.process(
        message="automate daily email reports",
        session_id="int_session_7",
        user_id="integration_test",
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert any(c.type == "done" for c in chunks)


@pytest.mark.asyncio
async def test_classify_then_select(classifier):
    """Test classify → select chain"""
    text = "write a REST API in Python"
    intent = await classifier.classify(text)
    assert intent.type == IntentType.CODE
    agents = await select_agent(intent)
    assert len(agents) > 0
    assert agents[0] in ["aider", "openhands", "smolagents", "metagpt", "autogen"]


@pytest.mark.asyncio
async def test_classify_then_select_research(classifier):
    """Test classify → select for research"""
    text = "research the latest AI trends"
    intent = await classifier.classify(text)
    assert intent.type == IntentType.RESEARCH
    agents = await select_agent(intent)
    assert len(agents) > 0
    assert agents[0] in ["langchain", "haystack", "llamaindex", "crewai", "huggingface"]


@pytest.mark.asyncio
async def test_concurrent_messages(orchestrator):
    """Test concurrent message processing"""
    async def process_message(session_id: str, message: str):
        chunks = []
        async for chunk in orchestrator.process(
            message=message,
            session_id=session_id,
            user_id="concurrent_test",
        ):
            chunks.append(chunk)
        return chunks

    results = await asyncio.gather(*[
        process_message(f"con_session_{i}", f"task {i}") for i in range(5)
    ])
    assert len(results) == 5
    for chunks in results:
        assert any(c.type == "done" for c in chunks)


@pytest.mark.asyncio
async def test_session_persistence(orchestrator):
    """Test session persists across messages"""
    session_id = "persistence_test_session"

    # First message
    async for _ in orchestrator.process(
        message="first message",
        session_id=session_id,
        user_id="persistence_test",
    ):
        pass

    # Second message in same session
    async for _ in orchestrator.process(
        message="second message in same session",
        session_id=session_id,
        user_id="persistence_test",
    ):
        pass

    # Session should exist
    session = orchestrator.get_session(session_id)
    assert session is not None
    assert len(session["messages"]) > 0


@pytest.mark.asyncio
async def test_error_recovery(orchestrator):
    """Test system recovers from errors gracefully"""
    # Send empty message
    async for _ in orchestrator.process(
        message="",
        session_id="error_session",
        user_id="error_test",
    ):
        pass

    # Next message should still work
    chunks = []
    async for chunk in orchestrator.process(
        message="recovery task",
        session_id="error_session",
        user_id="error_test",
    ):
        chunks.append(chunk)
    assert any(c.type == "done" for c in chunks)


@pytest.mark.asyncio
async def test_health_check_all_services(orchestrator):
    """Test health check reports all services"""
    health = await orchestrator.health_check()
    assert health["status"] == "ok"
    assert "classifier" in health
    assert "agents_registered" in health
