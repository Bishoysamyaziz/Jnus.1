"""OneAgent OS — Hybrid LLM Router (Phase 5)
Routes requests to the optimal LLM tier based on intent complexity and cost.
Tiers: DeepSeek (primary) → Ollama (free) → WindsurfAPI (near-free) → Claude/OpenAI (paid fallback)
"""
from __future__ import annotations

import os
from typing import Any

# ── LLM Tiers (Lazy-loaded — تُقرأ من os.environ عند الاستخدام فقط) ──
# Each tier has: name, base_url, api_key, models, cost_per_1k, max_complexity
# Complexity is 0.0 (simple) → 1.0 (very complex)
# ✅ Race Condition Fix: تُقرأ الـ env vars عند كل استدعاء route() وليس عند import

def _get_tiers() -> list[dict]:
    """Build LLM tiers lazily — reads os.environ at call time, not import time.
    هذا يمنع Race Condition حيث أن .env قد لا يكون محمّلاً بعد عند import.
    """
    return [
        {
            "name": "deepseek",
            "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "models": [os.getenv("DEEPSEEK_MODEL", "deepseek-chat"), "deepseek-coder"],
            "cost_per_1k": 0.00014,
            "max_complexity": 0.9,
        },
        {
            "name": "ollama",
            "base_url": os.getenv("OLLAMA_URL", "http://ollama:11434/v1"),
            "api_key": "",
            "models": [os.getenv("OLLAMA_MODEL", "llama3.2"), "mistral"],
            "cost_per_1k": 0.0,
            "max_complexity": 0.4,
        },
        {
            "name": "windsurf",
            "base_url": os.getenv("WINDSURF_API_URL", "http://windsurf-api:3003/v1"),
            "api_key": os.getenv("WINDSURF_API_KEY", ""),
            "models": ["claude-sonnet-4-6", "deepseek-v3", "gemini-2.5-pro"],
            "cost_per_1k": 0.0005,
            "max_complexity": 0.85,
        },
        {
            "name": "claude_real",
            "base_url": "https://api.anthropic.com",
            "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "models": ["claude-opus-4-6", "claude-sonnet-4-6"],
            "cost_per_1k": 0.015,
            "max_complexity": 1.0,
        },
        {
            "name": "openai_real",
            "base_url": "https://api.openai.com/v1",
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "models": ["gpt-4o", "gpt-4o-mini"],
            "cost_per_1k": 0.01,
            "max_complexity": 1.0,
        },
    ]


# ✅ Backward compatibility: LLM_TIERS is now a callable function
LLM_TIERS = _get_tiers()


class HybridLLMRouter:
    """Routes LLM requests to the optimal tier based on complexity analysis."""

    def __init__(self, tiers: list[dict] | None = None):
        self.tiers = tiers or LLM_TIERS

    async def route(self, intent: str, complexity: float) -> dict:
        """Select the best LLM tier for the given intent and complexity."""
        for tier in self.tiers:
            if complexity <= tier["max_complexity"]:
                return tier
        return self.tiers[-1]

    async def estimate_cost(self, intent: str, complexity: float, tokens: int = 1000) -> float:
        """Estimate cost for a request based on tier and token count."""
        tier = await self.route(intent, complexity)
        return tier["cost_per_1k"] * (tokens / 1000)

    def list_tiers(self) -> list[dict]:
        """List all available LLM tiers."""
        return [
            {
                "name": t["name"],
                "models": t["models"],
                "cost_per_1k": t["cost_per_1k"],
                "max_complexity": t["max_complexity"],
            }
            for t in self.tiers
        ]


router = HybridLLMRouter()
route = router.route

__all__ = ["LLM_TIERS", "HybridLLMRouter", "router", "route"]
