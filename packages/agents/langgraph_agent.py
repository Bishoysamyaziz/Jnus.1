"""OneAgent OS — LangGraph Agent Wrapper
Complex workflows with state management
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class LangGraphAgent(BaseAgent):
    """
    متى يُستدعى: workflows معقدة مع state management
    مثال: approval flows, conditional branching
    """

    @property
    def framework_name(self) -> str:
        return "langgraph"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from langgraph.graph import StateGraph
        except ImportError:
            return AgentResult(
                content=f"[LangGraph] Framework not installed. Install with: pip install langgraph\nTask: {task.description}",
                framework="langgraph",
                success=False,
                error="LangGraph not installed",
            )
        workflow = StateGraph(dict)
        workflow.add_node("process", lambda x: {"result": f"Processed: {x.get('input', '')}"})
        workflow.set_entry_point("process")
        workflow.set_finish_point("process")
        app = workflow.compile()
        result = await app.ainvoke({"input": task.description})
        return AgentResult(content=str(result.get("result", "")), framework="langgraph", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("workflows", "Complex workflow management"),
            Capability("state_management", "State management and transitions"),
            Capability("conditional_branching", "Conditional branching and approval flows"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=2000, usd=0.01, time_seconds=25)
