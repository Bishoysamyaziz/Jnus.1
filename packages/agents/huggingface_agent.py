"""OneAgent OS — HuggingFace Agent Wrapper
ML tasks, model inference, transformers
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class HuggingFaceAgent(BaseAgent):
    """
    متى يُستدعى: ML tasks, model inference, transformers
    مثال: "صنف الصور دي", "ترجم هذا النص"
    """

    @property
    def framework_name(self) -> str:
        return "huggingface"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from transformers import pipeline
        except ImportError:
            return AgentResult(
                content=f"[HuggingFace] Framework not installed. Install with: pip install transformers\nTask: {task.description}",
                framework="huggingface",
                success=False,
                error="transformers not installed",
            )
        pipe = pipeline("text-generation", model="gpt2")
        result = pipe(task.description, max_length=200)
        return AgentResult(content=str(result[0]["generated_text"]), framework="huggingface", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("ml_tasks", "ML model inference and transformers"),
            Capability("text_generation", "Text generation and completion"),
            Capability("classification", "Text and image classification"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=500, usd=0.002, time_seconds=10)
