"""OneAgent OS — BabyAGI Agent Wrapper
Long-term goal decomposition and prioritization loop
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class BabyAGIAgent(BaseAgent):
    """
    متى يُستدعى: أهداف طويلة المدى تحتاج prioritization مستمر
    مثال: "خطط لـ 3 أشهر لتعلم machine learning"
    """

    @property
    def framework_name(self) -> str:
        return "babyagi"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from babyagi import BabyAGI
        except ImportError:
            return AgentResult(
                content=f"[BabyAGI] Framework not installed.\nTask: {task.description}",
                framework="babyagi",
                success=False,
                error="BabyAGI not installed",
            )
        agi = BabyAGI()
        result = await agi.run(task.description)
        return AgentResult(content=str(result), framework="babyagi", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("goal_decomposition", "Long-term goal decomposition"),
            Capability("prioritization", "Continuous task prioritization"),
            Capability("autonomous_planning", "Autonomous planning and execution"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=3000, usd=0.015, time_seconds=60)
