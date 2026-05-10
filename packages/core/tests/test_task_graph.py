"""Tests for TaskGraph"""
from __future__ import annotations

import pytest

from packages.core.planning.task_graph import TaskGraph, TaskNode


@pytest.fixture
def graph():
    return TaskGraph()


def test_add_node(graph):
    """Should add a node to the graph"""
    node = graph.add_node("task1", "Do something")
    assert node.id == "task1"
    assert node.description == "Do something"
    assert node.id in graph.nodes


def test_add_edge(graph):
    """Should add an edge between nodes"""
    graph.add_node("task1", "First")
    graph.add_node("task2", "Second")
    graph.add_edge("task1", "task2")
    assert "task2" in graph.nodes["task1"].dependencies
    assert "task1" in graph.nodes["task2"].dependents


def test_get_execution_order(graph):
    """Should return topological execution order"""
    graph.add_node("task1", "First")
    graph.add_node("task2", "Second")
    graph.add_node("task3", "Third")
    graph.add_edge("task1", "task2")
    graph.add_edge("task1", "task3")
    order = graph.get_execution_order()
    assert order[0] == "task1"
    assert set(order[1:]) == {"task2", "task3"}


def test_get_execution_order_complex(graph):
    """Should handle complex dependency chains"""
    graph.add_node("a", "A")
    graph.add_node("b", "B")
    graph.add_node("c", "C")
    graph.add_node("d", "D")
    graph.add_edge("a", "b")
    graph.add_edge("a", "c")
    graph.add_edge("b", "d")
    graph.add_edge("c", "d")
    order = graph.get_execution_order()
    assert order.index("a") < order.index("b")
    assert order.index("a") < order.index("c")
    assert order.index("b") < order.index("d")
    assert order.index("c") < order.index("d")


def test_get_parallel_groups(graph):
    """Should identify parallel execution groups"""
    graph.add_node("a", "A")
    graph.add_node("b", "B")
    graph.add_node("c", "C")
    graph.add_edge("a", "b")
    graph.add_edge("a", "c")
    groups = graph.get_parallel_groups()
    assert len(groups) == 2
    assert groups[0] == ["a"]
    assert set(groups[1]) == {"b", "c"}


def test_get_critical_path(graph):
    """Should find the critical path"""
    graph.add_node("a", "A", duration=1)
    graph.add_node("b", "B", duration=3)
    graph.add_node("c", "C", duration=2)
    graph.add_edge("a", "b")
    graph.add_edge("a", "c")
    path = graph.get_critical_path()
    assert len(path) > 0


def test_has_cycle(graph):
    """Should detect cycles"""
    graph.add_node("a", "A")
    graph.add_node("b", "B")
    graph.add_node("c", "C")
    graph.add_edge("a", "b")
    graph.add_edge("b", "c")
    graph.add_edge("c", "a")
    assert graph.has_cycle()


def test_no_cycle(graph):
    """Should confirm no cycle in DAG"""
    graph.add_node("a", "A")
    graph.add_node("b", "B")
    graph.add_edge("a", "b")
    assert not graph.has_cycle()


def test_get_leaf_nodes(graph):
    """Should find leaf nodes (no dependents)"""
    graph.add_node("a", "A")
    graph.add_node("b", "B")
    graph.add_node("c", "C")
    graph.add_edge("a", "b")
    graph.add_edge("a", "c")
    leaves = graph.get_leaf_nodes()
    assert set(leaves) == {"b", "c"}


def test_get_root_nodes(graph):
    """Should find root nodes (no dependencies)"""
    graph.add_node("a", "A")
    graph.add_node("b", "B")
    graph.add_node("c", "C")
    graph.add_edge("a", "b")
    graph.add_edge("a", "c")
    roots = graph.get_root_nodes()
    assert roots == ["a"]


def test_clear_graph(graph):
    """Should clear all nodes"""
    graph.add_node("a", "A")
    graph.clear()
    assert len(graph.nodes) == 0


def test_node_count(graph):
    """Should return correct node count"""
    graph.add_node("a", "A")
    graph.add_node("b", "B")
    assert graph.node_count() == 2


def test_edge_count(graph):
    """Should return correct edge count"""
    graph.add_node("a", "A")
    graph.add_node("b", "B")
    graph.add_edge("a", "b")
    assert graph.edge_count() == 1
