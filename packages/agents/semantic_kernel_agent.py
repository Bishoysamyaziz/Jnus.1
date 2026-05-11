"""OneAgent OS — Semantic Kernel Agent Wrapper
Azure AI, Bedrock, Copilot integration
"""
from __future__ import annotations

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class SemanticKernelAgent(BaseAgent):
    """
    متى يُستدعى: Azure AI, Bedrock, CopilotStudio integration
    مثال: enterprise workflows مع Microsoft stack
    """

    @property
    def framework_name(self) -> str:
        return "semantic_kernel"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            from semantic_kernel import Kernel
            from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
        except ImportError:
            return AgentResult(
                content=f"[SemanticKernel] Framework not installed. Install with: pip install semantic-kernel\nTask: {task.description}",
                framework="semantic_kernel",
                success=False,
                error="SemanticKernel not installed",
            )

        cfg = self.get_llm_config()
        kernel = Kernel()
        kernel.add_service(OpenAIChatCompletion(ai_model_id=cfg["model"], api_key=cfg["api_key"], base_url=cfg["base_url"]))
        result = await kernel.invoke_prompt(task.description)
        return AgentResult(content=str(result), framework="semantic_kernel", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("enterprise", "Enterprise AI integration (Azure, Bedrock)"),
            Capability("microsoft_stack", "Microsoft Copilot and Azure integration"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=1500, usd=0.008, time_seconds=20)
