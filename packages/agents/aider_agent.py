"""OneAgent OS — Aider Agent Wrapper
Code editing on real git repositories
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class AiderAgent(BaseAgent):
    """
    متى يُستدعى: تعديل كود موجود (refactor, bugfix, feature add)
    مثال: "أضف unit tests لهذا الـ module"
    """

    @property
    def framework_name(self) -> str:
        return "aider"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from aider.coders import Coder
            from aider.models import Model
        except ImportError:
            return AgentResult(
                content=f"[Aider] Framework not installed. Install with: pip install aider-chat\nTask: {task.description}",
                framework="aider",
                success=False,
                error="Aider not installed",
            )
        model = Model("gpt-4")
        coder = Coder.create(main_model=model, auto_commits=False)
        result = coder.run(task.description)
        return AgentResult(content=str(result), framework="aider", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("code_editing", "Code editing on real git repos"),
            Capability("refactoring", "Code refactoring and optimization"),
            Capability("bugfixing", "Bug fixing and debugging"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=2000, usd=0.01, time_seconds=30)
