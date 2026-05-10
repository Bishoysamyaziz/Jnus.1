"""OneAgent OS — AutoGPT Agent Wrapper
Self-directed tasks with high autonomy
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class AutoGPTAgent(BaseAgent):
    """
    متى يُستدعى: self-directed tasks تحتاج autonomy عالية
    مثال: "ابحث عن أفضل framework لـ X وقيّمه وأعطيني تقرير"
    """

    @property
    def framework_name(self) -> str:
        return "autogpt"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from autogpt import AutoGPT
        except ImportError:
            return AgentResult(
                content=f"[AutoGPT] Framework not installed.\nTask: {task.description}",
                framework="autogpt",
                success=False,
                error="AutoGPT not installed",
            )
        agent = AutoGPT()
        result = await agent.run(task.description)
        return AgentResult(content=str(result), framework="autogpt", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("autonomy", "High autonomy self-directed tasks"),
            Capability("research", "Autonomous research and analysis"),
            Capability("decision_making", "Independent decision making"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=4000, usd=0.02, time_seconds=90)
