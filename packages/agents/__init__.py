"""OneAgent OS — 24 Agent Framework Wrappers
All agents inherit from BaseAgent and are auto-registered in AgentSelector.
"""
from __future__ import annotations

from packages.agents.crewai_agent import CrewAIAgent
from packages.agents.autogen_agent import AutoGenAgent
from packages.agents.metagpt_agent import MetaGPTAgent
from packages.agents.camel_agent import CAMELAgent
from packages.agents.agentverse_agent import AgentVerseAgent
from packages.agents.taskweaver_agent import TaskWeaverAgent
from packages.agents.babyagi_agent import BabyAGIAgent
from packages.agents.swarm_agent import SwarmAgent
from packages.agents.aider_agent import AiderAgent
from packages.agents.openhands_agent import OpenHandsAgent
from packages.agents.smolagents_agent import SmolAgentsAgent
from packages.agents.huggingface_agent import HuggingFaceAgent
from packages.agents.langchain_agent import LangChainAgent
from packages.agents.langgraph_agent import LangGraphAgent
from packages.agents.haystack_agent import HaystackAgent
from packages.agents.llamaindex_agent import LlamaIndexAgent
from packages.agents.semantic_kernel_agent import SemanticKernelAgent
from packages.agents.letta_agent import LettaAgent
from packages.agents.mem0_agent import Mem0Agent
from packages.agents.autogpt_agent import AutoGPTAgent
from packages.agents.agentgpt_agent import AgentGPTAgent
from packages.agents.rasa_agent import RasaAgent
from packages.agents.botpress_agent import BotpressAgent
from packages.agents.superagi_agent import SuperAGIAgent

__all__ = [
    "CrewAIAgent",
    "AutoGenAgent",
    "MetaGPTAgent",
    "CAMELAgent",
    "AgentVerseAgent",
    "TaskWeaverAgent",
    "BabyAGIAgent",
    "SwarmAgent",
    "AiderAgent",
    "OpenHandsAgent",
    "SmolAgentsAgent",
    "HuggingFaceAgent",
    "LangChainAgent",
    "LangGraphAgent",
    "HaystackAgent",
    "LlamaIndexAgent",
    "SemanticKernelAgent",
    "LettaAgent",
    "Mem0Agent",
    "AutoGPTAgent",
    "AgentGPTAgent",
    "RasaAgent",
    "BotpressAgent",
    "SuperAGIAgent",
]

# Agent registry: maps framework_name → class
AGENT_REGISTRY = {
    "crewai": CrewAIAgent,
    "autogen": AutoGenAgent,
    "metagpt": MetaGPTAgent,
    "camel": CAMELAgent,
    "agentverse": AgentVerseAgent,
    "taskweaver": TaskWeaverAgent,
    "babyagi": BabyAGIAgent,
    "swarm": SwarmAgent,
    "aider": AiderAgent,
    "openhands": OpenHandsAgent,
    "smolagents": SmolAgentsAgent,
    "huggingface": HuggingFaceAgent,
    "langchain": LangChainAgent,
    "langgraph": LangGraphAgent,
    "haystack": HaystackAgent,
    "llamaindex": LlamaIndexAgent,
    "semantic_kernel": SemanticKernelAgent,
    "letta": LettaAgent,
    "mem0": Mem0Agent,
    "autogpt": AutoGPTAgent,
    "agentgpt": AgentGPTAgent,
    "rasa": RasaAgent,
    "botpress": BotpressAgent,
    "superagi": SuperAGIAgent,
}

# Intent → Primary Agent mapping
INTENT_AGENT_MAP = {
    "CODE": ["aider", "langchain", "autogen", "openhands", "smolagents"],
    "RESEARCH": ["crewai", "langchain", "autogpt", "agentgpt", "huggingface"],
    "DATA": ["taskweaver", "llamaindex", "haystack", "langchain"],
    "PLANNING": ["babyagi", "metagpt", "agentgpt", "langgraph"],
    "CONVERSATION": ["rasa", "botpress", "langchain", "letta"],
    "CREATIVE": ["camel", "langchain", "huggingface", "agentverse"],
    "AUTOMATION": ["superagi", "langgraph", "swarm", "autogen"],
}


def get_agent_class(framework_name: str):
    """Get agent class by framework name."""
    return AGENT_REGISTRY.get(framework_name)


def get_agents_for_intent(intent_type: str) -> list[str]:
    """Get recommended agents for an intent type."""
    return INTENT_AGENT_MAP.get(intent_type, ["langchain"])


def list_all_agents() -> list[dict]:
    """List all registered agents with their framework names."""
    return [
        {"name": name, "class": cls.__name__}
        for name, cls in AGENT_REGISTRY.items()
    ]
