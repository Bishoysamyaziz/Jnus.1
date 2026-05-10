# Phase 1 — Foundation Core (Week 1–2)
> النواة الأساسية. كل شيء يبنى فوق الـ foundation دي.

---

## الهدف

بيئة تطوير موحدة تشغّل كل الـ 24 framework في نفس الوقت بدون conflicts.

---

## المهام التفصيلية

### 1.1 إعداد Monorepo

```bash
# الهيكل المطلوب
oneagent/
├── packages/
│   ├── core/          ← الـ orchestrator الرئيسي
│   ├── api/           ← FastAPI backend
│   ├── frontend/      ← Next.js UI
│   ├── workers/       ← Celery async workers
│   └── agents/        ← wrapper لكل framework
├── docker-compose.yml
├── pnpm-workspace.yaml
└── pyproject.toml
```

**الأدوات:**
- `pnpm workspaces` للـ Node packages
- `uv` بديل pip للـ Python (أسرع 10x)
- `ruff` للـ linting
- `pre-commit` hooks

### 1.2 Docker Compose Stack

```yaml
# docker-compose.yml المطلوب
services:
  api:          # FastAPI — port 8000
  frontend:     # Next.js — port 3000
  worker:       # Celery — async tasks
  redis:        # port 6379 — short-term memory + task queue
  postgres:     # port 5432 — long-term storage
  qdrant:       # port 6333 — vector DB للـ embeddings
  ollama:       # port 11434 — local LLMs
  grafana:      # port 3001 — monitoring
  prometheus:   # port 9090 — metrics
```

### 1.3 Environment Variables

```bash
# .env.example — يجب أن يكون شامل 100%
# LLM APIs
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
DEEPSEEK_API_KEY=

# Infrastructure
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://user:pass@localhost:5432/oneagent
QDRANT_URL=http://localhost:6333

# Search Tools
SERPER_API_KEY=
TAVILY_API_KEY=

# Monitoring
SENTRY_DSN=
OPENTELEMETRY_ENDPOINT=

# App
SECRET_KEY=
ENVIRONMENT=development
MAX_TOKENS_PER_REQUEST=4096
TOKEN_BUDGET_USD=0.01
```

### 1.4 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  test:     # pytest + vitest
  lint:     # ruff + eslint
  build:    # docker build
  deploy:   # على merge لـ main
```

### 1.5 Logging & Monitoring

```python
# packages/core/logging.py
import structlog
import sentry_sdk
from opentelemetry import trace

# كل request له trace_id فريد
# كل error يروح Sentry تلقائياً
# كل operation لها span في OpenTelemetry
```

### 1.6 Health Check Endpoint

```python
# GET /health
{
  "status": "ok",
  "services": {
    "redis": "connected",
    "postgres": "connected",
    "qdrant": "connected",
    "ollama": "connected"
  },
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

---

## Acceptance Criteria

- [ ] `docker-compose up` يشغّل كل الـ services بدون errors
- [ ] `GET /health` يرجع 200 مع status كل الـ services
- [ ] CI pipeline يعدّي على كل push
- [ ] `.env.example` موثق بالكامل
- [ ] Logs تظهر في Grafana

---

## ملاحظات للتنفيذ

> **مهم:** لا تستخدمي `pip install` مباشرةً. استخدمي `uv pip install` لأن المشروع فيه 24 framework وبعضها conflicting dependencies. كل framework يشتغل في isolated virtualenv جوه الـ Docker container بتاعه.
