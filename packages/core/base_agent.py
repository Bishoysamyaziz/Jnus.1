"""OneAgent OS — Base Agent Interface
All 24 frameworks implement this interface.
The Orchestrator talks ONLY to BaseAgent — never directly to frameworks.
"""
from __future__ import annotations

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
            await agent.validate()
        cls._initialized = True
