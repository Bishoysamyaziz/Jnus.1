"""Tests for PlannerEngine"""
from __future__ import annotations

import pytest

from packages.core.planning.planner import PlannerEngine
from packages.core.models import Task, IntentType, TaskGraph


@pytest.fixture
def planner():
    return PlannerEngine()


def test_create_plan(planner):
    """Should create a plan from a task graph"""
    tasks = [
        Task(description="build a web app", intent=IntentType.CODE, priority=1),
    ]
    graph = TaskGraph(tasks=tasks)
    plan = planner.plan(graph, ["aider", "langchain"])
    assert plan is not None
    assert len(plan.tasks) > 0
    assert len(plan.parallel_groups) > 0


def test_create_plan_with_dependencies(planner):
    """Should handle task dependencies"""
    tasks = [
        Task(id="1", description="setup", intent=IntentType.CODE, dependencies=[], priority=1),
        Task(id="2", description="build", intent=IntentType.CODE, dependencies=["1"], priority=2),
        Task(id="3", description="test", intent=IntentType.CODE, dependencies=["2"], priority=3),
    ]
    graph = TaskGraph(tasks=tasks)
    plan = planner.plan(graph, ["aider"])
    assert len(plan.tasks) == 3
    # First group should have task 1 only
    assert "1" in plan.parallel_groups[0]


def test_parallel_groups(planner):
    """Should identify parallel execution groups"""
    tasks = [
        Task(id="1", description="task1", intent=IntentType.CODE, dependencies=[], priority=1),
        Task(id="2", description="task2", intent=IntentType.CODE, dependencies=[], priority=1),
        Task(id="3", description="task3", intent=IntentType.CODE, dependencies=["1", "2"], priority=2),
    ]
    graph = TaskGraph(tasks=tasks)
    plan = planner.plan(graph, ["aider", "langchain"])
    # Group 0: tasks 1,2 (parallel)
    # Group 1: task 3 (after 1,2 done)
    assert len(plan.parallel_groups) >= 2
    assert "1" in plan.parallel_groups[0]
    assert "2" in plan.parallel_groups[0]


def test_agent_assignment(planner):
    """Should assign agents to tasks"""
    tasks = [
        Task(id="1", description="task1", intent=IntentType.CODE, dependencies=[], priority=1),
        Task(id="2", description="task2", intent=IntentType.CODE, dependencies=[], priority=2),
    ]
    graph = TaskGraph(tasks=tasks)
    plan = planner.plan(graph, ["aider", "langchain"])
    assert "1" in plan.agent_assignments
    assert "2" in plan.agent_assignments


def test_estimate_duration(planner):
    """Should estimate execution duration"""
    tasks = [
        Task(id="1", description="task1", intent=IntentType.CODE, dependencies=[], priority=1),
        Task(id="2", description="task2", intent=IntentType.CODE, dependencies=["1"], priority=2),
    ]
    graph = TaskGraph(tasks=tasks)
    plan = planner.plan(graph, ["aider"])
    duration = planner.estimate_duration(plan)
    assert duration > 0


def test_estimate_cost(planner):
    """Should estimate execution cost"""
    tasks = [
        Task(id="1", description="task1", intent=IntentType.CODE, dependencies=[], priority=1),
    ]
    graph = TaskGraph(tasks=tasks)
    plan = planner.plan(graph, ["aider"])
    cost = planner.estimate_cost(plan)
    assert cost >= 0


def test_empty_graph(planner):
    """Should handle empty task graph"""
    graph = TaskGraph(tasks=[])
    plan = planner.plan(graph, ["aider"])
    assert len(plan.tasks) == 0
    assert len(plan.parallel_groups) == 0


def test_single_task(planner):
    """Should handle single task"""
    tasks = [
        Task(id="1", description="single task", intent=IntentType.CODE, dependencies=[], priority=1),
    ]
    graph = TaskGraph(tasks=tasks)
    plan = planner.plan(graph, ["aider"])
    assert len(plan.tasks) == 1
    assert len(plan.parallel_groups) == 1


def test_circular_dependency_handling(planner):
    """Should handle circular dependencies gracefully"""
    tasks = [
        Task(id="1", description="task1", intent=IntentType.CODE, dependencies=["2"], priority=1),
        Task(id="2", description="task2", intent=IntentType.CODE, dependencies=["1"], priority=2),
    ]
    graph = TaskGraph(tasks=tasks)
    plan = planner.plan(graph, ["aider"])
    # Should still produce a plan (all tasks in one group)
    assert len(plan.tasks) == 2
