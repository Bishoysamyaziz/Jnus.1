"""OneAgent OS — Core Data Models"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Optional


class IntentType(str, Enum):
    CODE = "CODE"
    RESEARCH = "RESEARCH"
    CREATIVE = "CREATIVE"
    DATA = "DATA"
    AUTOMATION = "AUTOMATION"
    CONVERSATION = "CONVERSATION"
    PLANNING = "PLANNING"
    EXECUTION = "EXECUTION"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    FALLBACK = "fallback"


@dataclass
class Intent:
    type: IntentType
    confidence: float
    sub_tasks: list[str] = field(default_factory=list)
    raw_input: str = ""
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class Capability:
    name: str
    description: str
    score: float = 1.0


@dataclass
class CostEstimate:
    tokens: int = 0
    usd: float = 0.0
    time_seconds: float = 0.0


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    intent: IntentType = IntentType.CODE
    dependencies: list[str] = field(default_factory=list)
    priority: int = 5
    agent_config: dict[str, Any] = field(default_factory=dict)
    complexity: int = 5
    privacy: str = "normal"
    requires_reasoning: bool = False


@dataclass
class TaskGraph:
    tasks: list[Task] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)  # (from_id, to_id)
    _executed: set[str] = field(default_factory=set)

    def get_independent_tasks(self) -> list[Task]:
        """Tasks with no unresolved dependencies"""
        executed_ids = {t.id for t in self.tasks if t.id in self._executed}
        return [t for t in self.tasks if all(d in executed_ids for d in t.dependencies)]

    def topological_sort(self) -> list[Task]:
        """Return tasks in dependency order"""
        visited: set[str] = set()
        result: list[Task] = []
        task_map = {t.id: t for t in self.tasks}

        def dfs(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)
            task = task_map[task_id]
            for dep_id in task.dependencies:
                if dep_id in task_map:
                    dfs(dep_id)
            result.append(task)

        for t in self.tasks:
            dfs(t.id)
        return result


@dataclass
class AgentResult:
    content: str = ""
    framework: str = ""
    success: bool = True
    error: Optional[str] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    tasks: list[Task] = field(default_factory=list)
    agent_assignments: dict[str, str] = field(default_factory=dict)  # task_id -> agent_name
    parallel_groups: list[list[str]] = field(default_factory=list)  # groups of parallel task_ids


@dataclass
class MemoryContext:
    session_id: str = ""
    user_id: str = ""
    messages: list[dict] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    short_term: dict[str, Any] = field(default_factory=dict)
    long_term: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChunk:
    type: str  # "token", "intent", "agent", "error", "done", "status"
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_sse(self) -> str:
        import json
        return f"data: {json.dumps({'type': self.type, 'content': self.content, 'metadata': self.metadata})}\n\n"
