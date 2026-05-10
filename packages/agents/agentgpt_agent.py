"""OneAgent OS — AgentGPT Agent Wrapper
Goal decomposition + web-based research
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class AgentGPTAgent(BaseAgent):
    """
    متى يُستدعى: goal decomposition + web-based research
    """

    @property
    def framework_name(self) -> str:
        return "agentgpt"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from agentgpt import AgentGPT
        except ImportError:
            return AgentResult(
                content=f"[AgentGPT] Framework not installed.\nTask: {task.description}",
                framework="agentgpt",
                success=False,
                error="AgentGPT not installed",
            )
        agent = AgentGPT()
        result = await agent.run(task.description)
        return AgentResult(content=str(result), framework="agentgpt", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("goal_decomposition", "Goal decomposition into sub-tasks"),
            Capability("web_research", "Web-based research and analysis"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=3000, usd=0.015, time_seconds=60)
