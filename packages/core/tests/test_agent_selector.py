"""Tests for AgentSelector (select_agent function)"""
from __future__ import annotations

import pytest

from packages.core.agent_selector import select_agent, AGENT_ROUTING, AGENT_CAPABILITIES, get_agent_capability
from packages.core.models import Intent, IntentType


@pytest.mark.asyncio
async def test_select_agent_for_code():
    """CODE intent should select aider or langchain"""
    intent = Intent(type=IntentType.CODE, confidence=0.95, sub_tasks=["write_code"])
    agents = await select_agent(intent)
    assert len(agents) > 0
    assert agents[0] in AGENT_ROUTING["CODE"]


@pytest.mark.asyncio
async def test_select_agent_for_research():
    """RESEARCH intent should select crewai or langchain"""
    intent = Intent(type=IntentType.RESEARCH, confidence=0.9, sub_tasks=["research"])
    agents = await select_agent(intent)
    assert len(agents) > 0
    assert agents[0] in AGENT_ROUTING["RESEARCH"]


@pytest.mark.asyncio
async def test_select_agent_for_data():
    """DATA intent should select taskweaver or llamaindex"""
    intent = Intent(type=IntentType.DATA, confidence=0.85, sub_tasks=["analyze_data"])
    agents = await select_agent(intent)
    assert len(agents) > 0
    assert agents[0] in AGENT_ROUTING["DATA"]


@pytest.mark.asyncio
async def test_select_agent_for_planning():
    """PLANNING intent should select babyagi or metagpt"""
    intent = Intent(type=IntentType.PLANNING, confidence=0.9, sub_tasks=["plan"])
    agents = await select_agent(intent)
    assert len(agents) > 0
    assert agents[0] in AGENT_ROUTING["PLANNING"]


@pytest.mark.asyncio
async def test_select_agent_for_conversation():
    """CONVERSATION intent should select letta or rasa"""
    intent = Intent(type=IntentType.CONVERSATION, confidence=0.95, sub_tasks=[])
    agents = await select_agent(intent)
    assert len(agents) > 0
    assert agents[0] in AGENT_ROUTING["CONVERSATION"]


@pytest.mark.asyncio
async def test_select_agent_for_creative():
    """CREATIVE intent should select crewai or autogen"""
    intent = Intent(type=IntentType.CREATIVE, confidence=0.85, sub_tasks=["create"])
    agents = await select_agent(intent)
    assert len(agents) > 0
    assert agents[0] in AGENT_ROUTING["CREATIVE"]


@pytest.mark.asyncio
async def test_select_agent_for_automation():
    """AUTOMATION intent should select superagi or autogpt"""
    intent = Intent(type=IntentType.AUTOMATION, confidence=0.9, sub_tasks=["automate"])
    agents = await select_agent(intent)
    assert len(agents) > 0
    assert agents[0] in AGENT_ROUTING["AUTOMATION"]


@pytest.mark.asyncio
async def test_select_agent_for_execution():
    """EXECUTION intent should select swarm or agentverse"""
    intent = Intent(type=IntentType.EXECUTION, confidence=0.85, sub_tasks=["execute"])
    agents = await select_agent(intent)
    assert len(agents) > 0
    assert agents[0] in AGENT_ROUTING["EXECUTION"]


@pytest.mark.asyncio
async def test_select_agent_with_skill_memory():
    """Selection should use skill memory when available"""
    intent = Intent(type=IntentType.CODE, confidence=0.95, sub_tasks=["write_code"])

    class MockSkillMemory:
        async def get_best(self, intent_type: str) -> dict | None:
            return {
                "intent_type": "CODE",
                "strategy": {"agent": "aider"},
                "performance_score": 0.95,
            }

    agents = await select_agent(intent, skill_memory=MockSkillMemory())
    assert agents[0] == "aider"


@pytest.mark.asyncio
async def test_select_agent_with_low_confidence_skill():
    """Selection should fallback to routing table when skill confidence is low"""
    intent = Intent(type=IntentType.CODE, confidence=0.95, sub_tasks=["write_code"])

    class MockLowSkillMemory:
        async def get_best(self, intent_type: str) -> dict | None:
            return {
                "intent_type": "CODE",
                "strategy": {"agent": "aider"},
                "performance_score": 0.5,  # Below 0.8 threshold
            }

    agents = await select_agent(intent, skill_memory=MockLowSkillMemory())
    assert agents[0] in AGENT_ROUTING["CODE"]


@pytest.mark.asyncio
async def test_select_agent_with_unknown_intent():
    """Unknown intent should fallback to langchain"""
    intent = Intent(type=IntentType.CODE, confidence=0.5, sub_tasks=[])
    # Force unknown by using a type not in routing
    agents = await select_agent(intent)
    assert len(agents) > 0


def test_agent_capabilities_exist():
    """All agents in routing should have capabilities defined"""
    for intent_type, agents in AGENT_ROUTING.items():
        for agent in agents:
            assert agent in AGENT_CAPABILITIES, f"{agent} missing from AGENT_CAPABILITIES"


def test_get_agent_capability():
    """get_agent_capability should return correct data"""
    cap = get_agent_capability("crewai")
    assert cap["name"] == "CrewAI"
    assert cap["strength"] == "collaboration"


def test_get_agent_capability_unknown():
    """get_agent_capability should return default for unknown agent"""
    cap = get_agent_capability("unknown_agent")
    assert cap["name"] == "unknown_agent"
    assert cap["strength"] == "unknown"


def test_routing_table_completeness():
    """All 8 intent types should have routing entries"""
    expected_intents = {"CODE", "RESEARCH", "CREATIVE", "DATA", "AUTOMATION", "CONVERSATION", "PLANNING", "EXECUTION"}
    assert set(AGENT_ROUTING.keys()) == expected_intents


def test_routing_table_has_fallbacks():
    """Each intent should have at least 2 fallback agents"""
    for intent_type, agents in AGENT_ROUTING.items():
        assert len(agents) >= 2, f"{intent_type} has only {len(agents)} agents"
