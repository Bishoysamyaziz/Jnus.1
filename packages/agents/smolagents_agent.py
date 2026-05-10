"""OneAgent OS — smolagents Agent Wrapper
Fast tool calling agents from HuggingFace
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class SmolAgentsAgent(BaseAgent):
    """
    متى يُستدعى: مهام تحتاج tool calling سريع
    يدعم: CodeAgent, ToolCallingAgent, MultiStepAgent
    """

    @property
    def framework_name(self) -> str:
        return "smolagents"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from smolagents import CodeAgent, HfApiModel
        except ImportError:
            return AgentResult(
                content=f"[smolagents] Framework not installed. Install with: pip install smolagents\nTask: {task.description}",
                framework="smolagents",
                success=False,
                error="smolagents not installed",
            )
        model = HfApiModel()
        agent = CodeAgent(tools=[], model=model)
        result = agent.run(task.description)
        return AgentResult(content=str(result), framework="smolagents", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("tool_calling", "Fast tool calling and execution"),
            Capability("code_generation", "Code generation and execution"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=1000, usd=0.005, time_seconds=15)
