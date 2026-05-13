"""OneAgent OS — Agent Selection Logic
Routes intents to the best framework(s) for the job.
Uses HTTP calls to Docker containers for real execution.
"""
from __future__ import annotations

import os
from typing import Any

from .models import Intent, IntentType

# ── Agent URLs (Docker containers) ────────────────────────────────
AGENT_URLS: dict[str, str] = {
    "crewai":           os.getenv("AGENT_URL_CREWAI",          "http://agent-crewai:8000"),
    "metagpt":          os.getenv("AGENT_URL_METAGPT",         "http://agent-metagpt:8000"),
    "autogen":          os.getenv("AGENT_URL_AUTOGEN",         "http://agent-autogen:8000"),
    "langchain":        os.getenv("AGENT_URL_LANGCHAIN",       "http://agent-langchain:8000"),
    "superagi":         os.getenv("AGENT_URL_SUPERAGI",        "http://agent-superagi:8000"),
    "babyagi":          os.getenv("AGENT_URL_BABYAGI",         "http://agent-babyagi:8000"),
    "aider":            os.getenv("AGENT_URL_AIDER",           "http://agent-aider:8000"),
    "openhands":        os.getenv("AGENT_URL_OPENHANDS",       "http://agent-openhands:8000"),
    "smolagents":       os.getenv("AGENT_URL_SMOLAGENTS",      "http://agent-smolagents:8000"),
    "haystack":         os.getenv("AGENT_URL_HAYSTACK",        "http://agent-haystack:8000"),
    "llamaindex":       os.getenv("AGENT_URL_LLAMAINDEX",      "http://agent-llamaindex:8000"),
    "langgraph":        os.getenv("AGENT_URL_LANGGRAPH",       "http://agent-langgraph:8000"),
    "camel":            os.getenv("AGENT_URL_CAMEL",           "http://agent-camel:8000"),
    "letta":            os.getenv("AGENT_URL_LETTA",           "http://agent-letta:8000"),
    "mem0":             os.getenv("AGENT_URL_MEM0",            "http://agent-mem0:8000"),
    "taskweaver":       os.getenv("AGENT_URL_TASKWEAVER",      "http://agent-taskweaver:8000"),
    "swarm":            os.getenv("AGENT_URL_SWARM",           "http://agent-swarm:8000"),
    "agentverse":       os.getenv("AGENT_URL_AGENTVERSE",      "http://agent-agentverse:8000"),
    "autogpt":          os.getenv("AGENT_URL_AUTOGPT",         "http://agent-autogpt:8000"),
    "agentgpt":         os.getenv("AGENT_URL_AGENTGPT",        "http://agent-agentgpt:8000"),
    "huggingface":      os.getenv("AGENT_URL_HUGGINGFACE",     "http://agent-huggingface:8000"),
    "rasa":             os.getenv("AGENT_URL_RASA",            "http://agent-rasa:8000"),
    "botpress":         os.getenv("AGENT_URL_BOTPRESS",        "http://agent-botpress:8000"),
    "semantic_kernel":  os.getenv("AGENT_URL_SEMANTIC_KERNEL", "http://agent-semantic-kernel:8000"),
}

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


async def call_agent(agent_name: str, task: dict) -> dict:
    """Call an agent via HTTP to its Docker container.
    Returns the agent's response or error.
    """
    import httpx
    url = AGENT_URLS.get(agent_name)
    if not url:
        return {"success": False, "error": f"Agent {agent_name} not found", "agent": agent_name}
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{url}/execute", json=task)
            return r.json()
    except httpx.ConnectError:
        return {"success": False, "error": f"Agent {agent_name} container not reachable at {url}", "agent": agent_name}
    except Exception as e:
        return {"success": False, "error": str(e), "agent": agent_name}


async def check_agent_health(agent_name: str) -> dict:
    """Check if an agent container is healthy."""
    import httpx
    url = AGENT_URLS.get(agent_name)
    if not url:
        return {"status": "unknown", "agent": agent_name}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{url}/health")
            return r.json()
    except Exception:
        return {"status": "unreachable", "agent": agent_name}


def get_agent_capability(agent_name: str) -> dict[str, Any]:
    """Get capability description for an agent"""
    return AGENT_CAPABILITIES.get(agent_name, {"name": agent_name, "desc": "Unknown agent", "strength": "unknown"})
