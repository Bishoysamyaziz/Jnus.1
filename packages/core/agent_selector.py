"""OneAgent OS — Agent Selection Logic
Routes intents to the best framework(s) for the job.
"""
from __future__ import annotations

from typing import Any

from .models import Intent, IntentType

# Routing table: intent type → ordered list of agent names to try
AGENT_ROUTING: dict[str, list[str]] = {
    "CODE":         ["aider", "openhands", "smolagents", "metagpt", "autogen"],
    "RESEARCH":     ["langchain", "haystack", "llamaindex", "crewai", "huggingface"],
    "CREATIVE":     ["crewai", "autogen", "langchain", "letta"],
    "DATA":         ["taskweaver", "camel", "langchain", "llamaindex"],
    "AUTOMATION":   ["superagi", "autogpt", "agentgpt", "swarm"],
    "CONVERSATION": ["letta", "mem0", "rasa", "botpress", "langchain"],
    "PLANNING":     ["babyagi", "metagpt", "crewai", "agentverse"],
    "EXECUTION":    ["swarm", "agentverse", "autogen", "openhands"],
}

# Agent capability descriptions for LLM-based selection
AGENT_CAPABILITIES: dict[str, dict[str, Any]] = {
    "crewai":      {"name": "CrewAI",      "desc": "Multi-role teams (researcher, writer, reviewer)", "strength": "collaboration"},
    "autogen":     {"name": "AutoGen",     "desc": "Multi-agent debate & critique", "strength": "discussion"},
    "metagpt":     {"name": "MetaGPT",     "desc": "Full software company simulation (13 roles)", "strength": "software_engineering"},
    "camel":       {"name": "CAMEL",       "desc": "Deep specialization in one domain", "strength": "specialization"},
    "agentverse":  {"name": "AgentVerse",  "desc": "Simulation scenarios & complex tasksolving", "strength": "simulation"},
    "taskweaver":  {"name": "TaskWeaver",  "desc": "Data analysis + Python execution in sandbox", "strength": "data_analysis"},
    "babyagi":     {"name": "BabyAGI",     "desc": "Long-term goal decomposition & prioritization", "strength": "planning"},
    "swarm":       {"name": "Swarm",       "desc": "Specialist routing via handoff", "strength": "routing"},
    "aider":       {"name": "Aider",       "desc": "Code editing on real git repos", "strength": "code_editing"},
    "openhands":   {"name": "OpenHands",   "desc": "Full dev environment control (terminal, debug)", "strength": "dev_ops"},
    "smolagents":  {"name": "smolagents",  "desc": "Fast tool calling agents", "strength": "tool_use"},
    "huggingface": {"name": "HuggingFace", "desc": "ML tasks, model inference, transformers", "strength": "ml_tasks"},
    "langchain":   {"name": "LangChain",   "desc": "General chain of thought + tool use (fallback)", "strength": "general"},
    "langgraph":   {"name": "LangGraph",   "desc": "Complex workflows with state management", "strength": "workflows"},
    "haystack":    {"name": "Haystack",    "desc": "RAG on documents + knowledge retrieval", "strength": "rag"},
    "llamaindex":  {"name": "LlamaIndex",  "desc": "Document QA + structured data query", "strength": "document_qa"},
    "semantic_kernel": {"name": "SemanticKernel", "desc": "Azure AI, Bedrock, Copilot integration", "strength": "enterprise"},
    "letta":       {"name": "Letta",       "desc": "Long-term memory across sessions (MemGPT)", "strength": "memory"},
    "mem0":        {"name": "Mem0",        "desc": "Cross-session personality & preferences", "strength": "personality"},
    "autogpt":     {"name": "AutoGPT",     "desc": "Self-directed tasks with high autonomy", "strength": "autonomy"},
    "agentgpt":    {"name": "AgentGPT",    "desc": "Goal decomposition + web research", "strength": "goal_decomp"},
    "rasa":        {"name": "Rasa",        "desc": "Structured conversations & form filling", "strength": "dialogue"},
    "botpress":    {"name": "Botpress",    "desc": "Visual flow conversations + NLU", "strength": "chatbots"},
    "superagi":    {"name": "SuperAGI",    "desc": "Autonomous tasks with 15+ tools", "strength": "automation"},
}


async def select_agent(intent: Intent, skill_memory=None) -> list[str]:
    """Select the best agent(s) for a given intent.

    1. Try from skill memory first (learned best strategies)
    2. Fallback to routing table
    """
    # Try skill memory if available
    if skill_memory:
        try:
            best = await skill_memory.get_best(intent.type.value)
            if best and best.get("performance_score", 0) > 0.8:
                return [best.get("strategy", {}).get("agent", AGENT_ROUTING.get(intent.type.value, ["langchain"])[0])]
        except Exception:
            pass

    # Fallback to routing table
    return AGENT_ROUTING.get(intent.type.value, ["langchain"])


def get_agent_capability(agent_name: str) -> dict[str, Any]:
    """Get capability description for an agent"""
    return AGENT_CAPABILITIES.get(agent_name, {"name": agent_name, "desc": "Unknown agent", "strength": "unknown"})
