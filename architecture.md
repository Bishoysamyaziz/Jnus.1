# Architecture — OneAgent OS

## الصورة الكاملة

```
╔══════════════════════════════════════════════════════════════════╗
║                         USER INPUT                               ║
╚═══════════════════════════════╦══════════════════════════════════╝
                                ║
                    ┌───────────▼───────────┐
                    │    Intent Classifier   │
                    │  (LLM-based, 8 types) │
                    └───────────┬───────────┘
                                │
              ┌─────────────────▼──────────────────┐
              │         Self Optimizer              │
              │  (checks SkillMemory for best       │
              │   strategy from past executions)    │
              └─────────────────┬──────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Task Graph Builder   │
                    │  (Goal → DAG of tasks) │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │    Planner Engine      │
                    │  (Sort by deps/priority│
                    │   assign agents)       │
                    └───────────┬───────────┘
                                │
          ┌─────────────────────▼───────────────────────┐
          │              Memory Lookup                    │
          │  Short-term (Redis) + Long-term (Postgres)   │
          └─────────────────────┬───────────────────────┘
                                │
          ┌─────────────────────▼───────────────────────┐
          │             Agent Dispatcher                  │
          │  Selects from 24 frameworks based on intent  │
          └──┬──────────────────┬───────────────────┬───┘
             │                  │                   │
    ┌────────▼──────┐  ┌────────▼──────┐  ┌────────▼──────┐
    │  Agent Pool 1 │  │  Agent Pool 2 │  │  Agent Pool 3 │
    │  (CrewAI,     │  │  (Aider,      │  │  (LangChain,  │
    │   MetaGPT,    │  │   OpenHands,  │  │   Haystack,   │
    │   AutoGen)    │  │   smolagents) │  │   LlamaIndex) │
    └────────┬──────┘  └────────┬──────┘  └────────┬──────┘
             │                  │                   │
          ┌──▼──────────────────▼───────────────────▼──┐
          │              Tool Execution Layer            │
          │  Code | Browser | Git | API | File | Search │
          └──────────────────────┬──────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │             Hybrid LLM Router                │
          │  Ollama (local) ← → Claude ← → DeepSeek     │
          └──────────────────────┬──────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │              Result Merger                    │
          │  Combines parallel results coherently         │
          └──────────────────────┬──────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │              Memory Save                      │
          │  Save to Short/Long/Skill memory              │
          └──────────────────────┬──────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │           Stream Response (SSE)               │
          │  Real-time streaming to user                  │
          └─────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **API** | FastAPI + Python 3.12 | Async, fast, type-safe |
| **Frontend** | Next.js 15 + TypeScript | SSR, streaming support |
| **Task Queue** | Celery + Redis | Async agent execution |
| **Short Memory** | Redis 7 | Sub-ms latency |
| **Long Memory** | PostgreSQL 16 | ACID, reliable |
| **Vector Memory** | Qdrant | Fast semantic search |
| **Local LLMs** | Ollama | Privacy + cost = $0 |
| **Cloud LLM** | Claude Sonnet 4 | Best reasoning |
| **Deep Analysis** | DeepSeek via Cloudflare | Best code + cost |
| **Monitoring** | Grafana + Prometheus | Full observability |
| **Tracing** | OpenTelemetry | Distributed tracing |
| **Error Tracking** | Sentry | Instant error alerts |
| **Container** | Docker + Compose | Reproducible env |
| **CI/CD** | GitHub Actions | Auto deploy |
| **Reverse Proxy** | Caddy | Auto HTTPS |

## Execution Flow Example

```
User: "ابني REST API للـ user authentication بالكامل"

1. IntentClassifier → CODE (confidence: 0.97)
2. SelfOptimizer → "آخر مرة اتعمل code task نجح مع Aider + MetaGPT"
3. TaskGraphBuilder →
   [Design DB schema] → [Write FastAPI endpoints] → [Add JWT auth]
                                                   ↗
   [Write unit tests]                            →   [Docker setup] → [README]
4. PlannerEngine → Aider: code | TaskWeaver: tests | Claude: README
5. MemoryLookup → "المستخدم بيفضل PostgreSQL و async patterns"
6. AgentDispatch → Aider (code) + TaskWeaver (tests) in PARALLEL
7. ToolExecution → Aider يكتب في git repo حقيقي
8. LLMRouter → DeepSeek للكود، Claude للـ README
9. ResultMerger → دمج كود + tests + docs
10. MemorySave → "code task نجح مع Aider، save strategy"
11. StreamResponse → المستخدم يشوف الكود بيتكتب real-time
```
