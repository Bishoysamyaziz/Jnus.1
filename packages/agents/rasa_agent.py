"""OneAgent OS — Rasa Agent Wrapper
Structured conversations and form filling
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class RasaAgent(BaseAgent):
    """
    متى يُستدعى: structured conversations + form filling
    مثال: "اجمع معلومات المستخدم خطوة بخطوة"
    """

    @property
    def framework_name(self) -> str:
        return "rasa"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from rasa.core.agent import Agent
        except ImportError:
            return AgentResult(
                content=f"[Rasa] Framework not installed. Install with: pip install rasa\nTask: {task.description}",
                framework="rasa",
                success=False,
                error="Rasa not installed",
            )
        agent = Agent.load("models/dialogue")
        result = await agent.handle_text(task.description)
        return AgentResult(content=str(result), framework="rasa", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("dialogue", "Structured dialogue management"),
            Capability("form_filling", "Form filling and data collection"),
            Capability("nlu", "Natural language understanding"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=1000, usd=0.005, time_seconds=15)
