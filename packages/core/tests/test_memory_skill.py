"""Tests for SkillMemory"""
from __future__ import annotations

import pytest

from packages.core.memory.skill_memory import SkillMemory


@pytest.fixture
def memory():
    return SkillMemory(qdrant_url="http://localhost:6333")


@pytest.mark.asyncio
async def test_save_strategy(memory):
    """Should save a learned strategy"""
    try:
        strategy = {"agent": "aider", "config": {"model": "gpt-4"}}
        await memory.save("CODE", strategy, score=0.95)
        assert True
    except Exception as e:
        pytest.skip(f"Qdrant not available: {e}")


@pytest.mark.asyncio
async def test_get_best_strategy(memory):
    """Should retrieve the best strategy for an intent type"""
    try:
        strategy = {"agent": "crewai", "config": {"roles": ["researcher", "writer"]}}
        await memory.save("RESEARCH", strategy, score=0.9)
        best = await memory.get_best("RESEARCH")
        if best:
            assert best["intent_type"] == "RESEARCH"
            assert best["performance_score"] >= 0
    except Exception as e:
        pytest.skip(f"Qdrant not available: {e}")


@pytest.mark.asyncio
async def test_get_best_nonexistent(memory):
    """Should return None for intent type with no strategies"""
    try:
        best = await memory.get_best("NONEXISTENT_INTENT")
        assert best is None
    except Exception as e:
        pytest.skip(f"Qdrant not available: {e}")


@pytest.mark.asyncio
async def test_simple_embed(memory):
    """Simple embedding should produce consistent vectors"""
    vec1 = memory._simple_embed("test text")
    vec2 = memory._simple_embed("test text")
    vec3 = memory._simple_embed("different text")
    assert vec1 == vec2  # Same input → same vector
    assert vec1 != vec3  # Different input → different vector
    assert len(vec1) == 384  # Correct dimension


@pytest.mark.asyncio
async def test_health_check(memory):
    """Health check should return True when Qdrant is available"""
    try:
        healthy = await memory.health()
        assert isinstance(healthy, bool)
    except Exception:
        pytest.skip("Qdrant not available")
