"""OneAgent OS — CAMEL Agent Wrapper
Deep specialization in one domain with role-playing
"""
from __future__ import annotations

from typing import Any

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class CAMELAgent(BaseAgent):
    """
    متى يُستدعى: مهام تحتاج تخصص عميق في مجال واحد
    مثال: "حلل هذا الـ dataset وأعطيني insights"
    """

    @property
    def framework_name(self) -> str:
        return "camel"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from camel.agent import ChatAgent
            from camel.message import SystemMessage
        except ImportError:
            return AgentResult(
                content=f"[CAMEL] Framework not installed. Install with: pip install camel-ai\nTask: {task.description}",
                framework="camel",
                success=False,
                error="CAMEL not installed",
            )

        system_msg = SystemMessage(content=f"You are a specialized agent for: {task.description}")
        agent = ChatAgent(system_msg)
        response = await agent.astep(task.description)
        return AgentResult(content=str(response.msg.content), framework="camel", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("specialization", "Deep domain specialization"),
            Capability("role_playing", "Role-playing conversation"),
            Capability("task_decomposition", "Task decomposition and execution"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=1500, usd=0.008, time_seconds=20)
