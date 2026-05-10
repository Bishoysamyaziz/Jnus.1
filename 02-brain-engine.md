# Phase 2 — Brain & Intent Engine (Week 3–4)
> المخ + محرك النوايا. ده اللي يحول الكلام لخطة قابلة للتنفيذ.

---

## الهدف

النظام يفهم قصد المستخدم ويبني خطة تنفيذ تلقائية بدون أي إعداد يدوي.

---

## المكونات

### 2.1 IntentClassifier

```python
# packages/core/intent/classifier.py

class IntentClassifier:
    """
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
    
    async def classify(self, user_input: str, context: dict) -> Intent:
        prompt = f"""
        Classify this user request into one of: 
        CODE, RESEARCH, CREATIVE, DATA, AUTOMATION, CONVERSATION, PLANNING, EXECUTION
        
        User: {user_input}
        Context: {context}
        
        Return JSON: {{"intent": "...", "confidence": 0.0-1.0, "sub_tasks": [...]}}
        """
        return await self.llm.classify(prompt)
```

### 2.2 TaskGraphBuilder

```python
# packages/core/planning/task_graph.py

class TaskGraphBuilder:
    """
    يحول الهدف لـ DAG (Directed Acyclic Graph).
    
    مثال:
    هدف: "ابني موقع بيع للكتب"
    
    DAG:
    [Research market] → [Design DB schema] → [Build backend API]
                                          ↗
    [Setup Next.js]  →                   → [Connect frontend]  → [Deploy]
                                          ↘
    [Write tests]    → [Setup CI/CD]      ↗
    """
    
    async def build(self, goal: str, intent: Intent) -> TaskGraph:
        # يستخدم LLM لتحديد المهام والـ dependencies
        # يرجع DAG قابل للتنفيذ
        pass
```

### 2.3 PlannerEngine

```python
# packages/core/planning/planner.py

class PlannerEngine:
    """
    يرتب المهام حسب:
    1. dependencies (A قبل B)
    2. priority (critical path أولاً)
    3. available agents (مين قادر ينفذ إيه)
    4. cost estimation (رخيص قبل غالي)
    """
    
    def plan(self, task_graph: TaskGraph, available_agents: list) -> ExecutionPlan:
        # Topological sort للـ DAG
        # Assign agent لكل task
        # Return ordered execution plan
        pass
```

### 2.4 Orchestrator

```python
# packages/core/orchestrator.py

class Orchestrator:
    """
    المدير العام. ينفذ الخطة ويتابع النتائج.
    """
    
    async def execute(self, plan: ExecutionPlan) -> AsyncIterator[Result]:
        # تنفيذ parallel للمهام المستقلة
        independent_tasks = plan.get_independent_tasks()
        results = await asyncio.gather(
            *[self.execute_task(task) for task in independent_tasks],
            return_exceptions=True
        )
        
        # error recovery تلقائي
        for task, result in zip(independent_tasks, results):
            if isinstance(result, Exception):
                yield await self.handle_failure(task, result)
            else:
                yield result
```

### 2.5 SelfOptimizer

```python
# packages/core/optimizer.py

class SelfOptimizer:
    """
    يتعلم من كل execution.
    يحفظ best_strategy لكل نوع مهمة.
    """
    
    async def learn(self, task: Task, result: Result, duration: float, cost: float):
        if result.success and cost < self.threshold:
            await self.skill_memory.save(
                intent_type=task.intent,
                strategy=task.agent_config,
                performance_score=self.score(result, duration, cost)
            )
    
    async def suggest_strategy(self, intent: Intent) -> AgentConfig:
        return await self.skill_memory.get_best(intent.type)
```

### 2.6 RetryLogic

```python
# packages/core/retry.py

class RetryWithFallback:
    """
    exponential backoff + fallback agent chain
    """
    
    FALLBACK_CHAIN = [
        "primary_agent",
        "secondary_agent", 
        "simple_llm_call",
        "human_in_the_loop"
    ]
    
    async def execute_with_retry(self, task: Task) -> Result:
        for attempt, agent_type in enumerate(self.FALLBACK_CHAIN):
            try:
                wait = 2 ** attempt  # 1s, 2s, 4s, 8s
                await asyncio.sleep(wait if attempt > 0 else 0)
                return await self.run_agent(agent_type, task)
            except Exception as e:
                if attempt == len(self.FALLBACK_CHAIN) - 1:
                    raise
                log.warning(f"Attempt {attempt} failed, trying fallback", error=str(e))
```

---

## Flow الكامل

```
User Input
    ↓
IntentClassifier  →  Intent(type=CODE, confidence=0.95)
    ↓
SelfOptimizer     →  best_strategy من الذاكرة (لو موجودة)
    ↓
TaskGraphBuilder  →  DAG: [write_code] → [test_code] → [explain_code]
    ↓
PlannerEngine     →  [Aider: write] parallel [TaskWeaver: test] → [Claude: explain]
    ↓
Orchestrator      →  تنفيذ parallel + stream النتائج
    ↓
SelfOptimizer     →  save performance metrics
    ↓
Stream Response   →  المستخدم يشوف النتيجة real-time
```

---

## Acceptance Criteria

- [ ] `classify("اكتب API للـ user authentication")` يرجع `intent=CODE` بـ confidence > 0.9
- [ ] Task graph ينقسم لـ parallel tasks صح
- [ ] فشل agent واحد مش بيوقف الـ orchestrator
- [ ] SelfOptimizer يحسن نتيجة نفس النوع من المهام بعد 5 executions
