"""OneAgent OS — Base Agent Interface
All 24 frameworks implement this interface.
The Orchestrator talks ONLY to BaseAgent — never directly to frameworks.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

from .models import AgentResult, Capability, CostEstimate, Intent, MemoryContext, Task


class BaseAgent(ABC):
    """Interface موحد لكل الـ 24 framework.
    كل framework بيشتغل في isolation.
    الـ Orchestrator بيتكلم مع BaseAgent فقط — مش مع الـ framework مباشرة.

    Rules (non-negotiable):
    - Rule 4: No agent runs more than 5 minutes
    - Rule 4: Max 20 iterations per execution
    - Rule 4: Human-in-the-loop after 10 iterations
    """

    # Rule 4: Timeout and iteration limits
    timeout: int = 300  # 5 minutes max execution time
    max_iterations: int = 20  # max loop iterations
    human_in_loop_threshold: int = 10  # after 10 iterations → ask user

    def get_llm_config(self) -> dict:
        """
        Single source of truth للـ LLM config.
        ✅ B6 Fix: تُقرأ من llm_config المُمرر من Orchestrator أولاً،
        ثم os.environ كـ fallback.
        هذا يمنع مشكلة "Memory لا تُمرر" حيث أن الـ config
        كانت تُقرأ من os.environ فقط وتتجاهل llm_config المُمرر.
        """
        # ✅ استخدام llm_config المُمرر من Orchestrator (إن وُجد)
        if hasattr(self, '_llm_config') and self._llm_config:
            return self._llm_config
        # Fallback: os.environ
        return {
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "api_key":  os.getenv("OPENAI_API_KEY",  "sk-dummy"),
            "model":    os.getenv("DEFAULT_MODEL",   "claude-sonnet-4-6"),
        }

    def set_llm_config(self, config: dict):
        """✅ B6 Fix: تعيين llm_config من Orchestrator"""
        self._llm_config = config

    @abstractmethod
    async def execute(self, task: Task, memory: MemoryContext) -> AgentResult:
        """Execute a task using this framework"""
        pass

    @abstractmethod
    def get_capabilities(self) -> list[Capability]:
        """What is this agent good at?"""
        pass

    @abstractmethod
    def estimate_cost(self, task: Task) -> CostEstimate:
        """How much will this cost?"""
        pass

    @property
    @abstractmethod
    def framework_name(self) -> str:
        pass

    @property
    def version(self) -> str:
        return "1.0.0"

    async def validate(self) -> bool:
        """Check if this agent is properly configured"""
        return True


class AgentRegistry:
    """Registry of all 24 agents — singleton"""

    _agents: dict[str, BaseAgent] = {}
    _initialized = False

    @classmethod
    def register(cls, agent: BaseAgent):
        cls._agents[agent.framework_name] = agent

    @classmethod
    def get(cls, name: str) -> BaseAgent | None:
        return cls._agents.get(name)

    @classmethod
    def list_agents(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "capabilities": [c.name for c in agent.get_capabilities()],
                "status": "ready",
            }
            for name, agent in cls._agents.items()
        ]

    @classmethod
    def get_agents_for_intent(cls, intent_type: str) -> list[BaseAgent]:
        """Find agents that can handle this intent type"""
        from .agent_selector import AGENT_ROUTING
        agent_names = AGENT_ROUTING.get(intent_type, ["langchain"])
        return [cls._agents[name] for name in agent_names if name in cls._agents]

    @classmethod
    async def initialize_all(cls):
        """Initialize all registered agents"""
        if cls._initialized:
            return
        for name, agent in cls._agents.items():
            try:
                await agent.validate()
            except Exception as e:
                print(f"⚠️ Failed to initialize agent '{name}': {e}")
        cls._initialized = True
