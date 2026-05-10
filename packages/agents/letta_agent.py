"""OneAgent OS — Letta Agent Wrapper
Long-term memory across sessions (MemGPT)
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class LettaAgent(BaseAgent):
    """
    متى يُستدعى: conversations تحتاج long-term memory عبر sessions
    مثال: personal assistant يتذكر كل تفاصيلك
    """

    @property
    def framework_name(self) -> str:
        return "letta"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from letta import Letta
        except ImportError:
            return AgentResult(
                content=f"[Letta] Framework not installed. Install with: pip install letta\nTask: {task.description}",
                framework="letta",
                success=False,
                error="Letta not installed",
            )
        client = Letta()
        result = await client.run(task.description)
        return AgentResult(content=str(result), framework="letta", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("long_term_memory", "Long-term memory across sessions"),
            Capability("personal_assistant", "Personal assistant with memory"),
            Capability("memgpt", "MemGPT memory management"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=2000, usd=0.01, time_seconds=30)
