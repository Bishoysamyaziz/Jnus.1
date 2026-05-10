"""OneAgent OS — LLM Router Package
Routes requests to the optimal LLM tier based on complexity and cost.
"""

from packages.core.llm.router import LLM_TIERS, HybridLLMRouter, route

__all__ = ["LLM_TIERS", "HybridLLMRouter", "route"]
