"""OneAgent OS — Mem0 Agent Wrapper
Cross-session personality and preferences
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class Mem0Agent(BaseAgent):
    """
    متى يُستدعى: cross-session personality + preferences
    يُضاف لكل agent آخر كـ memory layer
    """

    @property
    def framework_name(self) -> str:
        return "mem0"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from mem0 import Memory
        except ImportError:
            return AgentResult(
                content=f"[Mem0] Framework not installed. Install with: pip install mem0\nTask: {task.description}",
                framework="mem0",
                success=False,
                error="Mem0 not installed",
            )
        m = Memory()
        result = m.add(f"User: {memory.user_id}, Task: {task.description}")
        return AgentResult(content=f"[Mem0] Memory stored: {result}", framework="mem0", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("personality", "Cross-session personality and preferences"),
            Capability("memory_layer", "Memory layer for other agents"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=500, usd=0.002, time_seconds=5)
