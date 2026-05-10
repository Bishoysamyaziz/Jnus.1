"""Tests for TaskGraphBuilder and TaskGraph model"""
from __future__ import annotations

import pytest

from packages.core.planning.task_graph import TaskGraphBuilder
from packages.core.models import Intent, IntentType, TaskGraph, Task


@pytest.fixture
def builder():
    return TaskGraphBuilder()


@pytest.mark.asyncio
async def test_build_code_graph(builder):
    """Should build a task graph for CODE intent"""
    intent = Intent(type=IntentType.CODE, confidence=0.95, sub_tasks=["write_code"])
    graph = await builder.build("build a web app", intent)
    assert isinstance(graph, TaskGraph)
    assert len(graph.tasks) > 0
    # CODE template has 4 tasks
    assert len(graph.tasks) == 4


@pytest.mark.asyncio
async def test_build_research_graph(builder):
    """Should build a task graph for RESEARCH intent"""
    intent = Intent(type=IntentType.RESEARCH, confidence=0.9, sub_tasks=["research"])
    graph = await builder.build("research AI trends", intent)
    assert len(graph.tasks) == 4


@pytest.mark.asyncio
async def test_build_data_graph(builder):
    """Should build a task graph for DATA intent"""
    intent = Intent(type=IntentType.DATA, confidence=0.85, sub_tasks=["analyze"])
    graph = await builder.build("analyze sales data", intent)
    assert len(graph.tasks) == 4


@pytest.mark.asyncio
async def test_build_planning_graph(builder):
    """Should build a task graph for PLANNING intent"""
    intent = Intent(type=IntentType.PLANNING, confidence=0.9, sub_tasks=["plan"])
    graph = await builder.build("plan a project", intent)
    assert len(graph.tasks) == 4


@pytest.mark.asyncio
async def test_build_conversation_graph(builder):
    """Should build a task graph for CONVERSATION intent"""
    intent = Intent(type=IntentType.CONVERSATION, confidence=0.95, sub_tasks=[])
    graph = await builder.build("hello", intent)
    assert len(graph.tasks) == 2  # CONVERSATION has 2 tasks


@pytest.mark.asyncio
async def test_build_creative_graph(builder):
    """Should build a task graph for CREATIVE intent"""
    intent = Intent(type=IntentType.CREATIVE, confidence=0.85, sub_tasks=["create"])
    graph = await builder.build("write a poem", intent)
    assert len(graph.tasks) == 4


@pytest.mark.asyncio
async def test_build_automation_graph(builder):
    """Should build a task graph for AUTOMATION intent"""
    intent = Intent(type=IntentType.AUTOMATION, confidence=0.9, sub_tasks=["automate"])
    graph = await builder.build("automate deployment", intent)
    assert len(graph.tasks) == 4


@pytest.mark.asyncio
async def test_build_execution_graph(builder):
    """Should build a task graph for EXECUTION intent"""
    intent = Intent(type=IntentType.EXECUTION, confidence=0.85, sub_tasks=["execute"])
    graph = await builder.build("run the script", intent)
    assert len(graph.tasks) == 3  # EXECUTION has 3 tasks


@pytest.mark.asyncio
async def test_task_dependencies(builder):
    """Tasks should have proper dependencies"""
    intent = Intent(type=IntentType.CODE, confidence=0.95, sub_tasks=["write_code"])
    graph = await builder.build("build API", intent)
    # First task should have no dependencies
    assert graph.tasks[0].dependencies == []
    # Later tasks should depend on earlier ones
    assert len(graph.tasks[1].dependencies) > 0 or len(graph.tasks[2].dependencies) > 0


def test_task_graph_topological_sort():
    """TaskGraph.topological_sort should return tasks in dependency order"""
    tasks = [
        Task(id="1", description="task1", dependencies=[], priority=1),
        Task(id="2", description="task2", dependencies=["1"], priority=2),
        Task(id="3", description="task3", dependencies=["2"], priority=3),
    ]
    graph = TaskGraph(tasks=tasks)
    sorted_tasks = graph.topological_sort()
    assert [t.id for t in sorted_tasks] == ["1", "2", "3"]


def test_task_graph_independent_tasks():
    """get_independent_tasks should return tasks with no unresolved deps"""
    tasks = [
        Task(id="1", description="task1", dependencies=[], priority=1),
        Task(id="2", description="task2", dependencies=["1"], priority=2),
    ]
    graph = TaskGraph(tasks=tasks)
    # Before any execution, only task 1 is independent
    independent = graph.get_independent_tasks()
    assert len(independent) == 1
    assert independent[0].id == "1"


def test_task_graph_empty():
    """Empty task graph should work"""
    graph = TaskGraph(tasks=[])
    assert graph.topological_sort() == []
    assert graph.get_independent_tasks() == []


def test_task_graph_single_task():
    """Single task graph should work"""
    tasks = [Task(id="1", description="single", dependencies=[], priority=1)]
    graph = TaskGraph(tasks=tasks)
    assert len(graph.topological_sort()) == 1
    assert len(graph.get_independent_tasks()) == 1
