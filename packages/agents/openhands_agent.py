"""OneAgent OS — OpenHands Agent Wrapper
Full dev environment control (terminal, debug, install)
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class OpenHandsAgent(BaseAgent):
    """
    متى يُستدعى: مهام dev environment كاملة (install, run, debug)
    مثال: "خذ هذا المشروع وأصلح الـ failing tests"
    """

    @property
    def framework_name(self) -> str:
        return "openhands"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from openhands.core import OpenHands
        except ImportError:
            return AgentResult(
                content=f"[OpenHands] Framework not installed.\nTask: {task.description}",
                framework="openhands",
                success=False,
                error="OpenHands not installed",
            )
        oh = OpenHands()
        result = await oh.run(task.description)
        return AgentResult(content=str(result), framework="openhands", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("dev_environment", "Full dev environment control"),
            Capability("terminal", "Terminal command execution"),
            Capability("debugging", "Debugging and troubleshooting"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=2500, usd=0.012, time_seconds=45)
