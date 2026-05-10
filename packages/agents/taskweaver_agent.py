"""OneAgent OS — TaskWeaver Agent Wrapper
Data analysis with Python execution in sandbox
"""
from __future__ import annotations

from typing import Any

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class TaskWeaverAgent(BaseAgent):
    """
    متى يُستدعى: تحليل بيانات + Python execution
    مثال: "حلل هذا الـ CSV وارسم الـ trends"
    """

    @property
    def framework_name(self) -> str:
        return "taskweaver"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from taskweaver import TaskWeaver
        except ImportError:
            return AgentResult(
                content=f"[TaskWeaver] Framework not installed. Install with: pip install taskweaver\nTask: {task.description}",
                framework="taskweaver",
                success=False,
                error="TaskWeaver not installed",
            )

        tw = TaskWeaver()
        result = await tw.run(task.description)
        return AgentResult(content=str(result), framework="taskweaver", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("data_analysis", "Data analysis with Python execution"),
            Capability("visualization", "Data visualization and charting"),
            Capability("code_execution", "Sandboxed Python code execution"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=2000, usd=0.01, time_seconds=30)
