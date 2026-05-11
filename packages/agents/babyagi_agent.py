"""OneAgent OS — BabyAGI Agent Wrapper
Long-term goal decomposition and prioritization loop
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class BabyAGIAgent(BaseAgent):
    """
    متى يُستدعى: أهداف طويلة المدى تحتاج prioritization مستمر
    مثال: "خطط لـ 3 أشهر لتعلم machine learning"
    """

    @property
    def framework_name(self) -> str:
        return "babyagi"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            return AgentResult(
                content=f"[BabyAGI] LangChain not installed.\nTask: {task.description}",
                framework="babyagi",
                success=False,
                error="LangChain not installed",
            )

        cfg = self.get_llm_config()
        llm = ChatOpenAI(model=cfg["model"], base_url=cfg["base_url"], api_key=cfg["api_key"], temperature=0)

        # BabyAGI loop: task creation → prioritization → execution
        tasks    = [task.description]
        results  = []
        for _ in range(3):  # max 3 iterations
            if not tasks:
                break
            current = tasks.pop(0)
            response = await llm.ainvoke(current)
            results.append(str(response.content))
            # Generate next sub-task
            next_task_prompt = f"Based on result: {results[-1][:200]}\nWhat is the next task for: {task.description}?"
            next_resp = await llm.ainvoke(next_task_prompt)
            next_task = str(next_resp.content).strip()
            if next_task and "complete" not in next_task.lower():
                tasks.append(next_task)

        return AgentResult(content="\n---\n".join(results), framework="babyagi", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("goal_decomposition", "Long-term goal decomposition"),
            Capability("prioritization", "Continuous task prioritization"),
            Capability("autonomous_planning", "Autonomous planning and execution"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=3000, usd=0.015, time_seconds=60)
