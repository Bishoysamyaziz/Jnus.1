"""OneAgent OS — Botpress Agent Wrapper
Visual flow conversations + NLU
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class BotpressAgent(BaseAgent):
    """
    متى يُستدعى: visual flow conversations + NLU
    مثال: customer support بـ decision trees
    """

    @property
    def framework_name(self) -> str:
        return "botpress"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from botpress import BotpressClient
        except ImportError:
            return AgentResult(
                content=f"[Botpress] Framework not installed.\nTask: {task.description}",
                framework="botpress",
                success=False,
                error="Botpress not installed",
            )
        client = BotpressClient(bot_id="oneagent")
        result = await client.send_message(task.description)
        return AgentResult(content=str(result), framework="botpress", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("chatbots", "Visual flow chatbot conversations"),
            Capability("nlu", "NLU and intent recognition"),
            Capability("decision_trees", "Decision tree conversations"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=1000, usd=0.005, time_seconds=15)
