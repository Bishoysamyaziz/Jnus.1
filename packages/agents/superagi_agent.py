"""OneAgent OS — SuperAGI Agent Wrapper
Autonomous tasks with 15+ tools (GitHub, Jira, Slack...)
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class SuperAGIAgent(BaseAgent):
    """
    متى يُستدعى: autonomous tasks مع 15 tool (GitHub, Jira, Slack...)
    مثال: "أنشئ Jira ticket وـassign للـ team وابعت Slack notification"
    """

    @property
    def framework_name(self) -> str:
        return "superagi"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from superagi import SuperAGI
        except ImportError:
            return AgentResult(
                content=f"[SuperAGI] Framework not installed.\nTask: {task.description}",
                framework="superagi",
                success=False,
                error="SuperAGI not installed",
            )
        agi = SuperAGI()
        result = await agi.run(task.description)
        return AgentResult(content=str(result), framework="superagi", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("automation", "Autonomous task automation with 15+ tools"),
            Capability("integration", "GitHub, Jira, Slack, Email integration"),
            Capability("tool_orchestration", "Multi-tool orchestration"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=3000, usd=0.015, time_seconds=60)
