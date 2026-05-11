"""OneAgent OS — CrewAI Agent Wrapper
Multi-role orchestration: researcher, writer, reviewer
"""
from __future__ import annotations

from typing import Any

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class CrewAIAgent(BaseAgent):
    """
    متى يُستدعى: مهام تحتاج أدوار متعددة (researcher + writer + reviewer)
    مثال: "اكتب تقرير بحثي شامل عن X"
    """

    @property
    def framework_name(self) -> str:
        return "crewai"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from crewai import Crew, Process, Agent as CrewAgent, Task as CrewTask
            from langchain_openai import ChatOpenAI
        except ImportError:
            return AgentResult(
                content=f"[CrewAI] Framework not installed. Install with: pip install crewai\nTask: {task.description}",
                framework="crewai",
                success=False,
                error="CrewAI not installed",
            )

        cfg = self.get_llm_config()
        llm = ChatOpenAI(model=cfg["model"], base_url=cfg["base_url"], api_key=cfg["api_key"])

        researcher = CrewAgent(role="Researcher", goal="Gather information",  backstory="Expert researcher", llm=llm)
        writer     = CrewAgent(role="Writer",     goal="Write clear content", backstory="Expert writer",     llm=llm)
        reviewer   = CrewAgent(role="Reviewer",   goal="Review and improve",  backstory="Expert reviewer",   llm=llm)

        crew_tasks = [
            CrewTask(description=f"Research: {task.description}", agent=researcher),
            CrewTask(description=f"Write: {task.description}", agent=writer),
            CrewTask(description=f"Review: {task.description}", agent=reviewer),
        ]

        crew = Crew(agents=[researcher, writer, reviewer], tasks=crew_tasks, process=Process.sequential, verbose=False)
        result = await crew.kickoff_async(inputs={"task": task.description})
        return AgentResult(content=str(result), framework="crewai", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("multi_role", "Multi-role orchestration with researcher, writer, reviewer"),
            Capability("research", "Deep research and information gathering"),
            Capability("content_creation", "Content writing and review"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=2000, usd=0.01, time_seconds=30)
