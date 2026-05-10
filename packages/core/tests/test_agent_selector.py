"""Tests for AgentSelector"""
from __future__ import annotations

import pytest

from packages.core.agent_selector import AgentSelector
from packages.core.models import IntentType


@pytest.fixture
def selector():
    return AgentSelector()


def test_select_agent_for_code(selector):
    """CODE intent should select aider or langchain"""
    agent = selector.select(IntentType.CODE)
    assert agent is not None
    assert agent in ["aider", "langchain", "autogen", "openhands"]


def test_select_agent_for_research(selector):
    """RESEARCH intent should select crewai or langchain"""
    agent = selector.select(IntentType.RESEARCH)
    assert agent is not None
    assert agent in ["crewai", "langchain", "autogpt", "agentgpt"]


def test_select_agent_for_data(selector):
    """DATA intent should select taskweaver or llamaindex"""
    agent = selector.select(IntentType.DATA)
    assert agent is not None
    assert agent in ["taskweaver", "llamaindex", "haystack"]


def test_select_agent_for_planning(selector):
    """PLANNING intent should select babyagi or metagpt"""
    agent = selector.select(IntentType.PLANNING)
    assert agent is not None
    assert agent in ["babyagi", "metagpt", "agentgpt"]


def test_select_agent_for_conversation(selector):
    """CONVERSATION intent should select rasa or botpress"""
    agent = selector.select(IntentType.CONVERSATION)
    assert agent is not None
    assert agent in ["rasa", "botpress", "langchain"]


def test_select_agent_for_creative(selector):
    """CREATIVE intent should select camel or langchain"""
    agent = selector.select(IntentType.CREATIVE)
    assert agent is not None
    assert agent in ["camel", "langchain", "huggingface"]


def test_select_agent_for_automation(selector):
    """AUTOMATION intent should select superagi or langgraph"""
    agent = selector.select(IntentType.AUTOMATION)
    assert agent is not None
    assert agent in ["superagi", "langgraph", "swarm"]


def test_select_agent_with_context(selector):
    """Selection should consider context"""
    context = {"preferred_framework": "crewai"}
    agent = selector.select(IntentType.RESEARCH, context)
    assert agent == "crewai"


def test_select_agent_with_unknown_intent(selector):
    """Unknown intent should fallback to langchain"""
    agent = selector.select("UNKNOWN_INTENT")
    assert agent == "langchain"


def test_get_all_agents(selector):
    """Should return all registered agents"""
    agents = selector.get_all_agents()
    assert len(agents) == 24
    assert "crewai" in agents
    assert "langchain" in agents
    assert "autogen" in agents


def test_get_agents_by_capability(selector):
    """Should filter agents by capability"""
    agents = selector.get_agents_by_capability("code_editing")
    assert "aider" in agents


def test_register_agent(selector):
    """Should register a new agent"""
    selector.register_agent("test_agent", IntentType.CODE)
    agents = selector.get_all_agents()
    assert "test_agent" in agents


def test_remove_agent(selector):
    """Should remove an agent"""
    selector.register_agent("temp_agent", IntentType.CODE)
    selector.remove_agent("temp_agent")
    agents = selector.get_all_agents()
    assert "temp_agent" not in agents


def test_get_agent_priority(selector):
    """Should return agent priority"""
    priority = selector.get_agent_priority("crewai")
    assert isinstance(priority, int)
    assert 0 <= priority <= 10
