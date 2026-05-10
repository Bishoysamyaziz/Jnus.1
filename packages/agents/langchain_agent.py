"""OneAgent OS — LangChain Agent Wrapper
General chain of thought + tool use (fallback)
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class LangChainAgent(BaseAgent):
    """
    متى يُستدعى: chain of thought + tool use عام
    الأكثر flexibility — fallback للحالات غير المصنفة
    """

    @property
    def framework_name(self) -> str:
        return "langchain"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from langchain.agents import AgentExecutor, create_react_agent
            from langchain.tools import tool
            from langchain_openai import ChatOpenAI
            from langchain.prompts import PromptTemplate
        except ImportError:
            return AgentResult(
                content=f"[LangChain] Framework not installed. Install with: pip install langchain\nTask: {task.description}",
                framework="langchain",
                success=False,
                error="LangChain not installed",
            )
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        prompt = PromptTemplate.from_template("{input}")
        agent = create_react_agent(llm, [], prompt)
        executor = AgentExecutor(agent=agent, tools=[], verbose=False)
        result = await executor.ainvoke({"input": task.description})
        return AgentResult(content=str(result["output"]), framework="langchain", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("chain_of_thought", "Chain of thought reasoning"),
            Capability("tool_use", "General tool use and integration"),
            Capability("fallback", "Universal fallback for unclassified tasks"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=1500, usd=0.008, time_seconds=20)
