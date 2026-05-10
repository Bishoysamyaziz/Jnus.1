"""OneAgent OS — MetaGPT Agent Wrapper
Full software company simulation with 13 roles
"""
from __future__ import annotations

from typing import Any

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class MetaGPTAgent(BaseAgent):
    """
    متى يُستدعى: مهام software engineering كاملة
    مثال: "ابني SaaS app للـ task management"
    """

    @property
    def framework_name(self) -> str:
        return "metagpt"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from metagpt.software_company import SoftwareCompany
            from metagpt.roles import ProductManager, Architect, ProjectManager, Engineer
        except ImportError:
            return AgentResult(
                content=f"[MetaGPT] Framework not installed. Install with: pip install metagpt\nTask: {task.description}",
                framework="metagpt",
                success=False,
                error="MetaGPT not installed",
            )

        company = SoftwareCompany()
        company.add_role(ProductManager())
        company.add_role(Architect())
        company.add_role(ProjectManager())
        company.add_role(Engineer())

        result = await company.run(task.description)
        return AgentResult(content=str(result), framework="metagpt", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("software_engineering", "Full software engineering lifecycle"),
            Capability("product_management", "Product requirements and planning"),
            Capability("architecture", "System architecture design"),
            Capability("implementation", "Code implementation"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=5000, usd=0.025, time_seconds=120)
