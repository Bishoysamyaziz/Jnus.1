"""OneAgent OS — LLM-based Intent Classifier
Classifies user input into one of 8 intent types using an LLM.
No keyword matching — real semantic understanding.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from ..models import Intent, IntentType


class IntentClassifier:
    """LLM-based intent detection.

    يصنف النية باستخدام LLM — مش keyword matching.

    8 أنواع نوايا:
    - CODE        → كتابة/مراجعة/تنفيذ كود
    - RESEARCH    → بحث وتحليل معلومات
    - CREATIVE    → كتابة إبداعية، تصميم
    - DATA        → تحليل بيانات، visualization
    - AUTOMATION  → أتمتة مهمة متكررة
    - CONVERSATION → محادثة عادية
    - PLANNING    → تخطيط مشروع أو هدف
    - EXECUTION   → تنفيذ عمل محدد مباشر
    """

    def __init__(self, llm_client: Optional[Any] = None):
        self.llm = llm_client or self._create_default_llm()
        self._cache: dict[str, Intent] = {}

    def _create_default_llm(self):
        import os

        ollama_url   = os.getenv("OLLAMA_URL",        "http://ollama:11434")
        ollama_model = os.getenv("OLLAMA_MODEL",       "llama3.2")
        windsurf_url = os.getenv("WINDSURF_API_URL",   "http://windsurf-api:3003")
        windsurf_key = os.getenv("WINDSURF_API_KEY",   "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

        class SmartLLMClient:
            """
            3-tier fallback للـ intent classification:
            1. Ollama  (مجاني محلي — أسرع)
            2. WindsurfAPI (مجاني cloud — fallback)
            3. Keyword matching (بدون LLM — آخر حل)
            """

            async def generate(self, prompt: str) -> str:
                import httpx

                # ── Tier 1: Ollama ──────────────────────────────────
                try:
                    async with httpx.AsyncClient(timeout=8) as client:
                        r = await client.post(
                            f"{ollama_url}/api/generate",
                            json={"model": ollama_model, "prompt": prompt,
                                  "stream": False, "options": {"temperature": 0.1, "num_predict": 256}},
                        )
                        if r.status_code == 200:
                            return r.json().get("response", "")
                except Exception:
                    pass

                # ── Tier 2: WindsurfAPI ─────────────────────────────
                try:
                    async with httpx.AsyncClient(timeout=20) as client:
                        r = await client.post(
                            f"{windsurf_url}/v1/chat/completions",
                            headers={"Authorization": f"Bearer {windsurf_key}",
                                     "Content-Type": "application/json"},
                            json={
                                "model": "claude-sonnet-4-6",
                                "messages": [{"role": "user", "content": prompt}],
                                "max_tokens": 256,
                                "temperature": 0.1,
                            },
                        )
                        if r.status_code == 200:
                            return r.json()["choices"][0]["message"]["content"]
                except Exception:
                    pass

                # ── Tier 3: keyword fallback (بدون LLM) ────────────
                return ""

        return SmartLLMClient()

    async def classify(self, user_input: str, context: dict | None = None) -> Intent:
        """Classify user input into an Intent.

        Args:
            user_input: The user's message
            context: Optional context (previous messages, user preferences, etc.)

        Returns:
            Intent with type, confidence, and sub_tasks
        """
        # Check cache for identical input
        cache_key = user_input.strip().lower()[:100]
        if cache_key in self._cache:
            return self._cache[cache_key]

        context_str = json.dumps(context or {}, ensure_ascii=False)

        prompt = f"""You are an intent classifier for an AI agent orchestration system.
Classify the following user request into EXACTLY ONE of these intent types:

- CODE: Writing, reviewing, or executing code. Building software, APIs, scripts.
- RESEARCH: Searching for information, analyzing topics, gathering knowledge.
- CREATIVE: Creative writing, design, content creation, brainstorming.
- DATA: Data analysis, visualization, statistics, working with datasets.
- AUTOMATION: Automating repetitive tasks, setting up workflows.
- CONVERSATION: Casual chat, greetings, general discussion.
- PLANNING: Project planning, goal setting, strategy, roadmaps.
- EXECUTION: Direct execution of a specific action.

User: {user_input}
Context: {context_str}

Respond with ONLY valid JSON:
{{"intent": "INTENT_TYPE", "confidence": 0.0-1.0, "sub_tasks": ["task1", "task2"], "reasoning": "brief explanation"}}"""

        try:
            response = await self.llm.generate(prompt)
            # Extract JSON from response
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            parsed = json.loads(response)
            intent_type = parsed.get("intent", "CODE").upper()

            # Validate intent type
            if intent_type not in IntentType.__members__:
                intent_type = "CODE"

            intent = Intent(
                type=IntentType[intent_type],
                confidence=float(parsed.get("confidence", 0.8)),
                sub_tasks=parsed.get("sub_tasks", []),
                raw_input=user_input,
                context=context or {},
            )

            # Cache the result
            self._cache[cache_key] = intent
            return intent

        except (json.JSONDecodeError, KeyError, ValueError, Exception) as e:
            # Fallback to keyword-based classification
            return self._fallback_classify(user_input, context)

    def _fallback_classify(self, user_input: str, context: dict | None = None) -> Intent:
        """Keyword-based fallback when LLM is unavailable"""
        text = user_input.lower()

        # Intent detection patterns
        patterns = [
            (IntentType.CODE, ["code", "كود", "api", "function", "برمجة", "برنامج",
                               "python", "javascript", "typescript", "script", "build",
                               "develop", "implement", "debug", "fix", "test"]),
            (IntentType.RESEARCH, ["research", "بحث", "search", "ابحث", "find",
                                   "what is", "tell me about", "explain", "تحقق"]),
            (IntentType.DATA, ["data", "بيانات", "تحليل", "csv", "dataset",
                               "analyze", "statistics", "chart", "graph"]),
            (IntentType.PLANNING, ["plan", "خطة", "خطط", "مشروع", "project",
                                   "roadmap", "strategy", "goal"]),
            (IntentType.AUTOMATION, ["automate", "اتمتة", "automatic", "تلقائي",
                                     "workflow", "pipeline", "schedule"]),
            (IntentType.CREATIVE, ["creative", "إبداع", "write", "اكتب", "design",
                                   "content", "story", "poem", "article"]),
            (IntentType.CONVERSATION, ["hello", "hi", "مرحبا", "اهلا", "كيف",
                                       "how are you", "what's up", "hey"]),
        ]

        for intent_type, keywords in patterns:
            if any(kw in text for kw in keywords):
                return Intent(
                    type=intent_type,
                    confidence=0.8,
                    sub_tasks=[f"process_{intent_type.value.lower()}"],
                    raw_input=user_input,
                    context=context or {},
                )

        # Default to CODE with lower confidence
        return Intent(
            type=IntentType.CODE,
            confidence=0.5,
            sub_tasks=["analyze_request"],
            raw_input=user_input,
            context=context or {},
        )

    async def classify_batch(self, inputs: list[str]) -> list[Intent]:
        """Classify multiple inputs"""
        return [await self.classify(inp) for inp in inputs]

    def clear_cache(self):
        """Clear the classification cache"""
        self._cache.clear()
