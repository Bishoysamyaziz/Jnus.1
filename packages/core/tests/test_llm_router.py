"""Tests for HybridLLMRouter (Phase 5)"""
from __future__ import annotations

import pytest

from packages.core.llm.router import HybridLLMRouter, LLM_TIERS


@pytest.fixture
def router():
    return HybridLLMRouter()


@pytest.mark.asyncio
async def test_route_simple_to_ollama(router):
    """Simple tasks should route to Ollama (free tier)"""
    tier = await router.route("CONVERSATION", complexity=0.2)
    assert tier["name"] == "ollama"
    assert tier["cost_per_1k"] == 0.0


@pytest.mark.asyncio
async def test_route_medium_to_windsurf(router):
    """Medium complexity tasks should route to WindsurfAPI"""
    tier = await router.route("CODE", complexity=0.6)
    assert tier["name"] == "windsurf"
    assert tier["cost_per_1k"] < 0.001


@pytest.mark.asyncio
async def test_route_complex_to_claude(router):
    """High complexity tasks should route to Claude"""
    tier = await router.route("RESEARCH", complexity=0.9)
    assert tier["name"] in ["claude_real", "openai_real"]


@pytest.mark.asyncio
async def test_route_max_complexity(router):
    """Maximum complexity should use the most capable tier"""
    tier = await router.route("PLANNING", complexity=1.0)
    assert tier["max_complexity"] == 1.0


@pytest.mark.asyncio
async def test_route_zero_complexity(router):
    """Zero complexity should use cheapest tier"""
    tier = await router.route("CONVERSATION", complexity=0.0)
    assert tier["cost_per_1k"] == 0.0


@pytest.mark.asyncio
async def test_estimate_cost_low(router):
    """Low complexity should have near-zero cost"""
    cost = await router.estimate_cost("CONVERSATION", complexity=0.1, tokens=1000)
    assert cost == 0.0


@pytest.mark.asyncio
async def test_estimate_cost_high(router):
    """High complexity should have higher cost"""
    cost = await router.estimate_cost("CODE", complexity=0.9, tokens=1000)
    assert cost > 0.0


@pytest.mark.asyncio
async def test_estimate_cost_scaling(router):
    """Cost should scale with token count"""
    cost_small = await router.estimate_cost("CODE", complexity=0.6, tokens=100)
    cost_large = await router.estimate_cost("CODE", complexity=0.6, tokens=10000)
    assert cost_large > cost_small


def test_list_tiers(router):
    """list_tiers should return all available tiers"""
    tiers = router.list_tiers()
    assert len(tiers) >= 4
    tier_names = [t["name"] for t in tiers]
    assert "ollama" in tier_names
    assert "windsurf" in tier_names
    assert "claude_real" in tier_names
    assert "openai_real" in tier_names


def test_tier_ordering(router):
    """Tiers should be ordered by cost (cheapest first)"""
    tiers = router.list_tiers()
    costs = [t["cost_per_1k"] for t in tiers]
    assert costs == sorted(costs)


def test_tier_complexity_coverage(router):
    """Tiers should cover the full complexity range"""
    tiers = router.list_tiers()
    max_complexities = [t["max_complexity"] for t in tiers]
    assert max(max_complexities) == 1.0
    assert min(max_complexities) >= 0.0


def test_ollama_is_free(router):
    """Ollama tier should always be free"""
    tiers = router.list_tiers()
    ollama = [t for t in tiers if t["name"] == "ollama"][0]
    assert ollama["cost_per_1k"] == 0.0


def test_windsurf_has_multiple_models(router):
    """WindsurfAPI should support multiple models"""
    tiers = router.list_tiers()
    windsurf = [t for t in tiers if t["name"] == "windsurf"][0]
    assert len(windsurf["models"]) >= 3


@pytest.mark.asyncio
async def test_route_different_intents_same_complexity(router):
    """Different intents at same complexity should route to same tier"""
    tier1 = await router.route("CODE", complexity=0.3)
    tier2 = await router.route("CONVERSATION", complexity=0.3)
    assert tier1["name"] == tier2["name"]


def test_llm_tiers_constant():
    """LLM_TIERS constant should be properly defined"""
    assert len(LLM_TIERS) >= 4
    for tier in LLM_TIERS:
        assert "name" in tier
        assert "models" in tier
        assert "cost_per_1k" in tier
        assert "max_complexity" in tier
        assert len(tier["models"]) > 0
