"""OneAgent OS — Swarm Agent Wrapper
Specialist routing via handoff mechanism
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class SwarmAgent(BaseAgent):
    """
    متى يُستدعى: routing بين specialists بناءً على context
    """

    @property
    def framework_name(self) -> str:
        return "swarm"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from swarm import Swarm, Agent
        except ImportError:
            return AgentResult(
                content=f"[Swarm] Framework not installed. Install with: pip install openai-swarm\nTask: {task.description}",
                framework="swarm",
                success=False,
                error="Swarm not installed",
            )

        cfg = self.get_llm_config()
        client = Swarm(base_url=cfg["base_url"], api_key=cfg["api_key"])
        agent = Agent(name="Generalist", instructions="Handle any task efficiently", model=cfg["model"])
        response = client.run(agent=agent, messages=[{"role": "user", "content": task.description}])
        return AgentResult(content=str(response.messages[-1]["content"]), framework="swarm", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("routing", "Specialist routing via handoff"),
            Capability("general_purpose", "General purpose task handling"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=1000, usd=0.005, time_seconds=15)
