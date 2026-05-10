# القواعد — غير قابلة للتفاوض

> دي مش suggestions. أي deviation بيخلق technical debt يصعب إصلاحه.

---

## القانون 1: BaseAgent Interface — لا استثناءات

كل framework **يجب** أن يرث من `BaseAgent` وينفذ:
- `execute(task, memory) → AgentResult`
- `get_capabilities() → list[Capability]`
- `estimate_cost(task) → CostEstimate`

**لماذا:** الـ Orchestrator بيتكلم مع الـ interface فقط. لو framework واحد بيخرج عن الـ interface، الـ orchestrator هيتكسر.

---

## القانون 2: Isolation — كل framework في container منفصل

كل framework عنده:
- Docker container منفصل
- Dependencies منفصلة (لا conflicts)
- Network isolated (يتكلم مع الـ API فقط)
- Resource limits (RAM + CPU + timeout)

**لماذا:** بعض الـ frameworks عندهم conflicting dependencies. CrewAI و AutoGen مثلاً بيستخدموا versions مختلفة من نفس الـ package.

---

## القانون 3: Local-First LLM

**الترتيب الإجباري:**
1. Ollama (local) — للمهام البسيطة < complexity 4
2. DeepSeek (cheap) — للكود والتحليل
3. Claude Sonnet 4 — للمهام المعقدة
4. GPT-4o — فقط كـ last resort

**لماذا:** Cost control. مشروع بـ 24 framework بيعمل آلاف الـ LLM calls. بدون routing هتدفع آلاف الدولارات شهرياً.

---

## القانون 4: لا Agent يبقى يشتغل أكثر من 5 دقائق

كل agent execution عنده:
```python
timeout = 300  # 5 دقائق
max_iterations = 20  # max loop iterations
human_in_loop_threshold = 10  # بعد 10 iterations → اسأل المستخدم
```

**لماذا:** Infinite loops. BabyAGI وAutoGPT مشهورين بالـ infinite loops اللي بتكلف مئات الدولارات.

---

## القانون 5: كل شيء يتسجل مع Trace ID

```python
# كل request
request_id = uuid4()
log.info("request_started", 
    trace_id=request_id,
    user_id=user.id,
    intent=intent.type,
    agent_selected=agent.name
)

# كل LLM call
log.info("llm_call",
    trace_id=request_id,
    model=model_name,
    tokens_in=prompt_tokens,
    tokens_out=response_tokens,
    cost_usd=cost,
    duration_ms=duration
)
```

**لماذا:** بدون observability، لما حاجة تتكسر مش هتعرف ليه. مع trace IDs، تقدري تتبع أي request من البداية للنهاية.

---

## القانون 6: Security-First

- **Code Execution:** Docker sandbox، no network، resource limits
- **User Input:** sanitize دايماً، لا تثقي في أي input
- **API Keys:** environment variables فقط، لا hardcoding أبداً
- **Auth:** JWT على كل endpoint
- **Rate Limiting:** 60 req/min per user

**لماذا:** Code execution tool = arbitrary code execution risk. السكريبت اللي ممكن يمحو كل حاجة على السيرفر ممكن يتبعت كـ "task".

---

## Timeline Milestone Gates

كل phase لازم تكمل قبل ما تبدأ اللي بعدها:

```
Week 2  ▶ docker-compose up بدون errors + /health يرد
Week 4  ▶ intent classification > 90% accuracy على 50 test case
Week 8  ▶ كل الـ 24 agent بيرد على base execute()
Week 10 ▶ memory يتحفظ ويترجع صح
Week 11 ▶ LLM routing يختار local للبسيط وcloud للمعقد
Week 13 ▶ code executor يشتغل في sandbox آمن
Week 15 ▶ Frontend streaming يشتغل end-to-end
Week 16 ▶ 99.9% uptime في load test لمدة 24 ساعة
```
