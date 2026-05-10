"""Tests for Planner"""
from __future__ import annotations

import pytest

from packages.core.planning.planner import Planner
from packages.core.models import Task, IntentType


@pytest.fixture
def planner():
    return Planner()


@pytest.mark.asyncio
async def test_create_plan(planner):
    """Should create a plan from a task"""
    task = Task(description="build a web app", intent_type=IntentType.CODE)
    plan = await planner.create_plan(task)
    assert plan is not None
    assert len(plan.steps) > 0
    assert all(hasattr(s, "description") for s in plan.steps)
    assert all(hasattr(s, "order") for s in plan.steps)


@pytest.mark.asyncio
async def test_create_plan_for_research(planner):
    """Should create a research plan"""
    task = Task(description="research quantum computing", intent_type=IntentType.RESEARCH)
    plan = await planner.create_plan(task)
    assert plan is not None
    assert len(plan.steps) > 0


@pytest.mark.asyncio
async def test_create_plan_for_data(planner):
    """Should create a data analysis plan"""
    task = Task(description="analyze sales data", intent_type=IntentType.DATA)
    plan = await planner.create_plan(task)
    assert plan is not None
    assert len(plan.steps) > 0


@pytest.mark.asyncio
async def test_create_plan_for_planning(planner):
    """Should create a meta-planning plan"""
    task = Task(description="plan a project", intent_type=IntentType.PLANNING)
    plan = await planner.create_plan(task)
    assert plan is not None
    assert len(plan.steps) > 0


@pytest.mark.asyncio
async def test_create_plan_for_conversation(planner):
    """Should create a simple conversation plan"""
    task = Task(description="hello", intent_type=IntentType.CONVERSATION)
    plan = await planner.create_plan(task)
    assert plan is not None
    assert len(plan.steps) >= 1


@pytest.mark.asyncio
async def test_create_plan_for_creative(planner):
    """Should create a creative plan"""
    task = Task(description="write a poem", intent_type=IntentType.CREATIVE)
    plan = await planner.create_plan(task)
    assert plan is not None
    assert len(plan.steps) > 0


@pytest.mark.asyncio
async def test_create_plan_for_automation(planner):
    """Should create an automation plan"""
    task = Task(description="automate deployment", intent_type=IntentType.AUTOMATION)
    plan = await planner.create_plan(task)
    assert plan is not None
    assert len(plan.steps) > 0


@pytest.mark.asyncio
async def test_create_plan_with_empty_task(planner):
    """Should handle empty task"""
    task = Task(description="", intent_type=IntentType.CONVERSATION)
    plan = await planner.create_plan(task)
    assert plan is not None
    assert len(plan.steps) == 1  # Default single step


@pytest.mark.asyncio
async def test_plan_steps_have_order(planner):
    """Plan steps should have sequential order"""
    task = Task(description="complex task", intent_type=IntentType.CODE)
    plan = await planner.create_plan(task)
    for i, step in enumerate(plan.steps):
        assert step.order == i + 1


@pytest.mark.asyncio
async def test_plan_has_estimated_duration(planner):
    """Plan should have estimated duration"""
    task = Task(description="test task", intent_type=IntentType.CODE)
    plan = await planner.create_plan(task)
    assert plan.estimated_duration > 0


@pytest.mark.asyncio
async def test_plan_has_estimated_cost(planner):
    """Plan should have estimated cost"""
    task = Task(description="test task", intent_type=IntentType.CODE)
    plan = await planner.create_plan(task)
    assert plan.estimated_cost >= 0
