"""OneAgent OS — Haystack Agent Wrapper
RAG on documents + knowledge retrieval
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class HaystackAgent(BaseAgent):
    """
    متى يُستدعى: RAG على documents + knowledge retrieval
    مثال: "ابحث في هذه الوثائق وأجب على السؤال"
    """

    @property
    def framework_name(self) -> str:
        return "haystack"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from haystack import Pipeline
            from haystack.components.builders import PromptBuilder
        except ImportError:
                return AgentResult(
                    content=f"[Haystack] Framework not installed. Install with: pip install haystack-ai\nTask: {task.description}",
                    framework="haystack",
                    success=False,
                    error="Haystack not installed",
                )
        pipe = Pipeline()
        pipe.add_component("prompt", PromptBuilder(template="{input}"))
        result = pipe.run({"prompt": {"input": task.description}})
        return AgentResult(content=str(result), framework="haystack", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("rag", "RAG on documents and knowledge retrieval"),
            Capability("document_qa", "Document question answering"),
            Capability("pipeline", "Pipeline-based processing"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=1500, usd=0.008, time_seconds=20)
