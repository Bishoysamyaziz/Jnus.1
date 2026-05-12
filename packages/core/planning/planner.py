"""OneAgent OS — Planner Engine
Creates execution plans from task graphs.
Handles dependency ordering, parallelization, and agent assignment.
"""
from __future__ import annotations

from typing import Any

from ..models import ExecutionPlan, Task, TaskGraph


class PlannerEngine:
    """يرتب المهام حسب:
    1. dependencies (A قبل B)
    2. priority (critical path أولاً)
    3. available agents (مين قادر ينفذ إيه)
    4. cost estimation (رخيص قبل غالي)
    """

    def plan(self, task_graph: TaskGraph, available_agents: list[str]) -> ExecutionPlan:
        """Create an execution plan from a task graph

        Args:
            task_graph: The DAG of tasks to execute
            available_agents: List of available agent names

        Returns:
            ExecutionPlan with ordered parallel groups
        """
        # Topological sort
        sorted_tasks = task_graph.topological_sort()

        # Build parallel groups
        parallel_groups = self._build_parallel_groups(sorted_tasks)

        # Assign agents to tasks
        agent_assignments = self._assign_agents(sorted_tasks, available_agents)

        return ExecutionPlan(
            tasks=sorted_tasks,
            agent_assignments=agent_assignments,
            parallel_groups=parallel_groups,
        )

    def _build_parallel_groups(self, tasks: list[Task]) -> list[list[str]]:
        """Group tasks that can run in parallel

        Uses a simple algorithm:
        - Tasks with no dependencies go in group 0
        - Tasks whose dependencies are all in groups < N go in group N
        """
        task_ids = {t.id for t in tasks}
        deps_map = {t.id: set(t.dependencies) & task_ids for t in tasks}
        groups: list[list[str]] = []
        assigned: set[str] = set()

        while len(assigned) < len(tasks):
            current_group = []
            for t in tasks:
                if t.id in assigned:
                    continue
                # Check if all dependencies are assigned
                if deps_map[t.id].issubset(assigned):
                    current_group.append(t.id)

            if not current_group:
                # Break circular dependencies — add remaining tasks
                remaining = [t.id for t in tasks if t.id not in assigned]
                if remaining:
                    current_group = remaining
                else:
                    break

            groups.append(current_group)
            assigned.update(current_group)

        return groups

    def _assign_agents(self, tasks: list[Task], available_agents: list[str]) -> dict[str, str]:
        """Assign agents to tasks based on priority and availability

        Simple round-robin for now — can be enhanced with ML-based assignment.
        """
        assignments = {}
        for i, task in enumerate(tasks):
            # Assign agent based on task priority and index
            agent_idx = min(i, len(available_agents) - 1)
            assignments[task.id] = available_agents[agent_idx]
        return assignments

    def estimate_duration(self, plan: ExecutionPlan) -> float:
        """Estimate total execution duration in seconds"""
        # Rough estimate: 2s per task + 1s per dependency
        task_map = {t.id: t for t in plan.tasks}
        total = 0
        for group in plan.parallel_groups:
            if not group:
                continue
            max_task_time = max(
                2 + len(task_map.get(tid, Task()).dependencies)
                for tid in group
            )
            total += max_task_time
        return total

    def estimate_cost(self, plan: ExecutionPlan) -> float:
        """Estimate total cost in USD"""
        # Rough estimate: $0.002 per task
        return len(plan.tasks) * 0.002
