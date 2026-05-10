"""OneAgent OS — Task Graph Builder
Converts a goal into a DAG (Directed Acyclic Graph) of tasks.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from ..models import Intent, IntentType, Task, TaskGraph


class TaskGraphBuilder:
    """يحول الهدف لـ DAG (Directed Acyclic Graph).

    مثال:
    هدف: "ابني موقع بيع للكتب"

    DAG:
    [Research market] → [Design DB schema] → [Build backend API]
                                          ↗
    [Setup Next.js]  →                   → [Connect frontend]  → [Deploy]
                                          ↘
    [Write tests]    → [Setup CI/CD]      ↗
    """

    def __init__(self, llm_client: Optional[Any] = None):
        self.llm = llm_client

    async def build(self, goal: str, intent: Intent) -> TaskGraph:
        """Build a task graph from a goal and intent"""
        # Use intent-specific templates for common patterns
        template = self._get_template(intent.type)

        if template:
            return self._build_from_template(goal, intent, template)

        # For complex/unusual goals, use LLM
        return await self._build_with_llm(goal, intent)

    def _get_template(self, intent_type: IntentType) -> list[dict] | None:
        """Get a task template for common intent types"""
        templates = {
            IntentType.CODE: [
                {"desc": "تحليل المتطلبات وتصميم الحل", "deps": [], "priority": 1},
                {"desc": "كتابة الكود الأساسي", "deps": [0], "priority": 2},
                {"desc": "إضافة الاختبارات", "deps": [1], "priority": 3},
                {"desc": "مراجعة وتحسين الكود", "deps": [1, 2], "priority": 4},
            ],
            IntentType.RESEARCH: [
                {"desc": "تحديد مصادر البحث", "deps": [], "priority": 1},
                {"desc": "جمع المعلومات", "deps": [0], "priority": 2},
                {"desc": "تحليل وتلخيص النتائج", "deps": [1], "priority": 3},
                {"desc": "كتابة التقرير النهائي", "deps": [2], "priority": 4},
            ],
            IntentType.DATA: [
                {"desc": "تحميل وتنظيف البيانات", "deps": [], "priority": 1},
                {"desc": "تحليل إحصائي", "deps": [0], "priority": 2},
                {"desc": "إنشاء التصورات", "deps": [1], "priority": 3},
                {"desc": "تقرير النتائج", "deps": [2], "priority": 4},
            ],
            IntentType.PLANNING: [
                {"desc": "تحليل الهدف الرئيسي", "deps": [], "priority": 1},
                {"desc": "تقسيم الهدف لمهام فرعية", "deps": [0], "priority": 2},
                {"desc": "تحديد الموارد والجدول الزمني", "deps": [1], "priority": 3},
                {"desc": "كتابة خطة التنفيذ", "deps": [2], "priority": 4},
            ],
            IntentType.AUTOMATION: [
                {"desc": "تحليل سير العمل الحالي", "deps": [], "priority": 1},
                {"desc": "تصميم الأتمتة", "deps": [0], "priority": 2},
                {"desc": "تنفيذ الـ pipeline", "deps": [1], "priority": 3},
                {"desc": "اختبار وتوثيق", "deps": [2], "priority": 4},
            ],
            IntentType.CREATIVE: [
                {"desc": "العصف الذهني وجمع الأفكار", "deps": [], "priority": 1},
                {"desc": "تطوير المفهوم", "deps": [0], "priority": 2},
                {"desc": "الكتابة/التصميم", "deps": [1], "priority": 3},
                {"desc": "مراجعة وتحسين", "deps": [2], "priority": 4},
            ],
            IntentType.CONVERSATION: [
                {"desc": "فهم سياق المحادثة", "deps": [], "priority": 1},
                {"desc": "توليد الرد", "deps": [0], "priority": 2},
            ],
            IntentType.EXECUTION: [
                {"desc": "تحليل الأمر", "deps": [], "priority": 1},
                {"desc": "تنفيذ الإجراء", "deps": [0], "priority": 2},
                {"desc": "تأكيد النتيجة", "deps": [1], "priority": 3},
            ],
        }
        return templates.get(intent_type)

    def _build_from_template(self, goal: str, intent: Intent, template: list[dict]) -> TaskGraph:
        """Build a task graph from a template"""
        tasks = []
        for i, t in enumerate(template):
            task = Task(
                description=f"{t['desc']} — {goal[:50]}",
                intent=intent.type,
                dependencies=[str(tasks[d].id) for d in t["deps"]],
                priority=t["priority"],
                complexity=min(10, max(1, t["priority"] * 2)),
            )
            tasks.append(task)

        graph = TaskGraph(tasks=tasks)
        return graph

    async def _build_with_llm(self, goal: str, intent: Intent) -> TaskGraph:
        """Use LLM to build a custom task graph for complex goals"""
        # Fallback to template-based approach
        template = self._get_template(intent.type) or self._get_template(IntentType.CODE)
        return self._build_from_template(goal, intent, template)
