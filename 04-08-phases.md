# Phase 4 — Memory System (Week 9–10)
> نظام الذاكرة الثلاثي. النظام يتذكر كل شيء إلى الأبد.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Memory Manager                     │
├──────────────┬──────────────┬───────────────────────┤
│ ShortTerm    │  LongTerm    │    SkillMemory         │
│ (Redis TTL)  │ (PostgreSQL) │    (Qdrant Vector)     │
│              │              │                        │
│ Context      │ History      │ Best strategies        │
│ Window       │ للمستخدمين   │ learned per intent     │
│ الحالي       │              │                        │
└──────┬───────┴──────┬───────┴──────────┬─────────────┘
       │              │                  │
       ▼              ▼                  ▼
   EpisodicMemory   Mem0 Integration   Compression
   (تسلسل زمني)    (cross-session)    (auto-summarize)
```

---

## الكود

### ShortTermMemory
```python
class ShortTermMemory:
    """Redis TTL=1h — context window الحالي"""
    
    async def save(self, session_id: str, messages: list):
        key = f"session:{session_id}:messages"
        await self.redis.setex(key, 3600, json.dumps(messages))
    
    async def get(self, session_id: str) -> list:
        data = await self.redis.get(f"session:{session_id}:messages")
        return json.loads(data) if data else []
```

### LongTermMemory
```python
class LongTermMemory:
    """PostgreSQL — history كامل + user profiles"""
    
    # Tables:
    # - conversations (id, user_id, session_id, created_at)
    # - messages (id, conversation_id, role, content, tokens, cost)
    # - user_profiles (user_id, preferences, personality, goals)
    # - task_history (id, user_id, intent, task, result, duration, cost)
```

### SkillMemory
```python
class SkillMemory:
    """Qdrant Vector DB — learned strategies"""
    
    async def save(self, intent_type: str, strategy: dict, score: float):
        embedding = await self.embedder.embed(str(strategy))
        await self.qdrant.upsert(
            collection="skills",
            points=[{
                "id": uuid4(),
                "vector": embedding,
                "payload": {
                    "intent_type": intent_type,
                    "strategy": strategy,
                    "performance_score": score,
                    "used_count": 1
                }
            }]
        )
    
    async def get_best(self, intent_type: str) -> Strategy | None:
        results = await self.qdrant.search(
            collection="skills",
            query_filter={"intent_type": intent_type},
            limit=1,
            with_payload=True
        )
        return results[0] if results else None
```

### Memory Compression
```python
class MemoryCompressor:
    """تلخيص تلقائي لما يتجاوز الـ context window"""
    
    async def compress_if_needed(self, messages: list, max_tokens: int) -> list:
        total_tokens = sum(count_tokens(m) for m in messages)
        if total_tokens > max_tokens * 0.8:
            # لخص أقدم 50% من المحادثة
            old_messages = messages[:len(messages)//2]
            summary = await self.llm.summarize(old_messages)
            return [{"role": "system", "content": f"Previous context: {summary}"}] + messages[len(messages)//2:]
        return messages
```

---

## Acceptance Criteria

- [ ] Session يتذكر آخر 100 رسالة بـ Redis
- [ ] User history محفوظ في PostgreSQL إلى الأبد
- [ ] Semantic search على الذاكرة يرجع نتيجة < 100ms
- [ ] Compression يحافظ على المعنى مع تقليل الـ tokens بـ 70%
- [ ] Mem0 يحتفظ بـ personality across sessions

---
---

# Phase 5 — Hybrid LLM Router (Week 11)
> موجه النماذج الذكي. الـ model الصح للمهمة الصح.

---

## Logic

```python
class HybridLLMRouter:
    """
    Cost-aware, performance-aware LLM routing
    """
    
    ROUTING_RULES = [
        # Simple tasks → Local (FREE)
        Rule(
            condition=lambda t: t.complexity < 3 and t.privacy == "high",
            model="ollama/llama3.2",
            reason="simple + private → local"
        ),
        # Complex reasoning → Claude Sonnet 4
        Rule(
            condition=lambda t: t.complexity >= 7 or t.requires_reasoning,
            model="claude-sonnet-4-20250514",
            reason="complex → Claude"
        ),
        # Code tasks → DeepSeek (via Cloudflare)
        Rule(
            condition=lambda t: t.intent == "CODE" and t.complexity in (4, 5, 6),
            model="deepseek-coder",
            reason="code → DeepSeek"
        ),
        # Default → Sonnet 4
        Rule(
            condition=lambda t: True,
            model="claude-sonnet-4-20250514",
            reason="default"
        ),
    ]
    
    FALLBACK_CHAIN = [
        "claude-sonnet-4-20250514",
        "gpt-4o",
        "ollama/llama3.2",
    ]
```

## Caching Layer
```python
class LLMCache:
    """
    Cache لـ identical requests — يوفر 80% من التكلفة
    """
    
    async def get_or_call(self, prompt: str, model: str) -> str:
        cache_key = hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()
        
        cached = await self.redis.get(f"llm_cache:{cache_key}")
        if cached:
            return json.loads(cached)
        
        result = await self.call_llm(prompt, model)
        await self.redis.setex(f"llm_cache:{cache_key}", 3600, json.dumps(result))
        return result
```

---
---

# Phase 6 — Tool Execution Layer (Week 12–13)
> طبقة تنفيذ الأدوات. الـ agent يقدر يعمل أي حاجة.

---

## الأدوات

```python
TOOLS = {
    "code_executor": CodeExecutorTool,     # Python/JS في Docker sandbox
    "web_search":    WebSearchTool,        # Serper + Tavily + SearXNG
    "browser":       BrowserTool,          # Playwright headless
    "file":          FileTool,             # read/write/delete/list
    "git":           GitTool,              # clone/commit/PR
    "api":           APITool,              # generic HTTP + auth
    "database":      DatabaseTool,         # SQL query
    "email":         EmailTool,            # send/read
    "calendar":      CalendarTool,         # create/read events
    "slack":         SlackTool,            # send messages
    "github":        GitHubTool,           # issues/PRs/repos
    "image_gen":     ImageGenTool,         # DALL-E/SD
    "pdf":           PDFTool,              # read/create/merge PDFs
}
```

### CodeExecutor (مهم جداً — sandboxed)
```python
class CodeExecutorTool:
    """
    ينفذ Python/JS في Docker container معزول
    Resource limits: 512MB RAM, 1 CPU, 30s timeout
    No network access
    """
    
    async def execute(self, code: str, language: str = "python") -> ExecutionResult:
        container = await docker.containers.run(
            "python:3.12-slim",
            command=["python", "-c", code],
            mem_limit="512m",
            cpu_quota=50000,
            network_disabled=True,
            remove=True,
            timeout=30
        )
        return ExecutionResult(
            output=container.logs(),
            exit_code=container.wait()["StatusCode"]
        )
```

---
---

# Phase 7 — API + Frontend (Week 14–15)
> واجهة المستخدم والـ API. المنتج يبدو احترافي.

---

## Backend API

```python
# FastAPI endpoints

POST   /v1/chat           # الـ main chat endpoint (SSE streaming)
GET    /v1/history        # conversation history
DELETE /v1/history/{id}   # delete conversation
GET    /v1/agents         # list available agents + status
POST   /v1/agents/run     # run specific agent manually
GET    /health            # health check
GET    /metrics           # Prometheus metrics
WS     /v1/ws/{session}  # WebSocket للـ real-time
```

### Chat Endpoint
```python
@app.post("/v1/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    async def generate():
        async for chunk in orchestrator.stream(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id,
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Frontend — Next.js

```
app/
├── page.tsx              ← Landing page
├── chat/
│   ├── page.tsx          ← Main chat interface
│   └── [id]/page.tsx     ← Specific conversation
├── agents/
│   └── page.tsx          ← Agent status dashboard
├── settings/
│   └── page.tsx          ← User settings
└── api/                  ← Next.js API routes
```

### Design System (مستوحى من Claude)
```typescript
const theme = {
  colors: {
    bg: "#0D0D14",
    surface: "#13131F",
    purple: "#B57BFF",
    text: "#E8E0FF",
    textMuted: "#8B7FC7",
  },
  fonts: {
    body: "Inter",
    mono: "DM Mono",
  }
}
```

### مميزات الـ UI
- Streaming responses (يكتب وانت شايف)
- Agent activity panel (مين بيشتغل دلوقتي)
- Memory indicator (كام رسالة في الـ context)
- Cost tracker (كلفت قد إيه)
- Model indicator (بيستخدم أنهي model)
- Conversation history sidebar

---
---

# Phase 8 — Production Hardening (Week 16)
> التصليد للـ production. النظام يشتغل وانت نايم.

---

## Security

```python
# Rate Limiting
@limiter.limit("60/minute")
async def chat_endpoint():
    pass

# Input Sanitization
class InputSanitizer:
    def sanitize(self, text: str) -> str:
        # Remove prompt injection attempts
        # Limit length
        # Validate encoding
        pass

# Auth (JWT)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload
```

## Monitoring

```yaml
# Grafana Dashboards:
- Request rate + latency
- Agent success/failure rates
- Token usage + cost per user
- Memory usage (Redis, Postgres, Qdrant)
- LLM router decisions
- Active sessions

# Alerts:
- Error rate > 1% → PagerDuty
- Latency > 5s → Slack notification
- Cost > $10/hour → Email + auto-throttle
- Disk > 80% → immediate alert
```

## Auto-scaling

```yaml
# docker-compose production overrides
services:
  worker:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        max_attempts: 3
```

## Backup Strategy

```bash
# Daily automated backups
postgres:  pg_dump → S3 (retained 30 days)
qdrant:    snapshot API → S3 (retained 7 days)
redis:     RDB snapshot (retained 3 days)
```

---

## Final Acceptance Criteria (كل الـ 8 phases)

| Metric | Target |
|--------|--------|
| Response time (simple) | < 3 seconds |
| Response time (complex) | < 30 seconds |
| Uptime | 99.9% |
| Average cost per request | < $0.01 |
| Memory retrieval | < 100ms |
| Agent failure rate | < 0.1% |
| Test coverage | > 80% |
