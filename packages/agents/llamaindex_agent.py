"""OneAgent OS — LlamaIndex Agent Wrapper
Document QA + structured data query
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class LlamaIndexAgent(BaseAgent):
    """
    متى يُستدعى: document QA + structured data query
    مثال: "اسأل على هذا الـ PDF"
    """

    @property
    def framework_name(self) -> str:
        return "llamaindex"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from llama_index.core import VectorStoreIndex, Document
        except ImportError:
            return AgentResult(
                content=f"[LlamaIndex] Framework not installed. Install with: pip install llama-index\nTask: {task.description}",
                framework="llamaindex",
                success=False,
                error="LlamaIndex not installed",
            )
        documents = [Document(text=task.description)]
        index = VectorStoreIndex.from_documents(documents)
        query_engine = index.as_query_engine()
        result = query_engine.query(task.description)
        return AgentResult(content=str(result), framework="llamaindex", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("document_qa", "Document question answering"),
            Capability("indexing", "Document indexing and retrieval"),
            Capability("structured_query", "Structured data query"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=1500, usd=0.008, time_seconds=20)
