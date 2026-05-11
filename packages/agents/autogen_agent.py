"""OneAgent OS — AutoGen Agent Wrapper
Multi-agent debate, critique, and verification
"""
from __future__ import annotations

from typing import Any

from packages.core.base_agent import BaseAgent
from packages.core.models import AgentResult, Capability, CostEstimate, MemoryContext, Task


class AutoGenAgent(BaseAgent):
    """
    متى يُستدعى: مهام تحتاج نقاش بين agents (debate, critique, verification)
    مثال: "راجع هذا الكود وتأكد إنه secure"
    """

    @property
    def framework_name(self) -> str:
        return "autogen"

    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        try:
            import autogen
        except ImportError:
            return AgentResult(
                content=f"[AutoGen] Framework not installed. Install with: pip install pyautogen\nTask: {task.description}",
                framework="autogen",
                success=False,
                error="AutoGen not installed",
            )

        cfg = self.get_llm_config()
        config_list = [{"model": cfg["model"], "api_key": cfg["api_key"], "base_url": cfg["base_url"]}]
        llm_config  = {"config_list": config_list, "timeout": 60}

        coder      = autogen.AssistantAgent(name="Coder",  llm_config=llm_config)
        critic     = autogen.AssistantAgent(name="Critic", llm_config=llm_config)
        user_proxy = autogen.UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            code_execution_config=False,
            max_consecutive_auto_reply=3,
        )
        result = await user_proxy.a_initiate_chat(coder, message=task.description, max_turns=3)
        return AgentResult(content=str(result.summary), framework="autogen", success=True)

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability("debate", "Multi-agent debate and critique"),
            Capability("code_review", "Code review and security analysis"),
            Capability("verification", "Multi-perspective verification"),
        ]

    def estimate_cost(self, task: Task) -> CostEstimate:
        return CostEstimate(tokens=3000, usd=0.015, time_seconds=45)
