#!/bin/bash
# OneAgent OS — Phase Validation Script
# Usage: ./scripts/validate.sh [phase_number]
# Example: ./scripts/validate.sh 1

PHASE=${1:-"all"}
PASS=0
FAIL=0

check() {
    local name=$1
    local cmd=$2
    
    if eval "$cmd" > /dev/null 2>&1; then
        echo "  ✅ $name"
        ((PASS++))
    else
        echo "  ❌ $name"
        ((FAIL++))
    fi
}

echo "═══════════════════════════════════════"
echo "  OneAgent OS — Phase Validation"
echo "═══════════════════════════════════════"

if [ "$PHASE" == "1" ] || [ "$PHASE" == "all" ]; then
    echo ""
    echo "📦 Phase 1: Foundation Core"
    check "Docker running" "docker ps"
    check "Redis connected" "docker exec oneagent-redis redis-cli ping | grep PONG"
    check "Postgres connected" "docker exec oneagent-postgres pg_isready"
    check "Qdrant connected" "curl -sf http://localhost:6333/health"
    check "API health endpoint" "curl -sf http://localhost:8000/health"
    check ".env exists" "[ -f .env ]"
    check "GitHub Actions CI exists" "[ -f .github/workflows/ci.yml ]"
    check "WindsurfAPI Dockerfile exists" "[ -f packages/windsurf-api/Dockerfile ]"
    check "WindsurfAPI in docker-compose" "grep -q 'windsurf-api' docker-compose.yml"
fi

if [ "$PHASE" == "2" ] || [ "$PHASE" == "all" ]; then
    echo ""
    echo "🧠 Phase 2: Brain & Intent Engine"
    check "IntentClassifier module exists" "[ -f packages/core/intent/classifier.py ]"
    check "TaskGraphBuilder module exists" "[ -f packages/core/planning/task_graph.py ]"
    check "Orchestrator module exists" "[ -f packages/core/orchestrator.py ]"
    check "Intent classification test" "python3 -m pytest packages/core/tests/test_intent.py -q"
fi

if [ "$PHASE" == "3" ] || [ "$PHASE" == "all" ]; then
    echo ""
    echo "🤖 Phase 3: Framework Integration"
    
    AGENTS=("crewai" "autogen" "metagpt" "camel" "agentverse" "langchain" 
            "langgraph" "haystack" "babyagi" "letta" "llamaindex" "aider"
            "openhands" "agentgpt" "autogpt" "huggingface" "rasa" "botpress"
            "mem0" "taskweaver" "swarm" "semantic_kernel" "smolagents" "superagi")
    
    for agent in "${AGENTS[@]}"; do
        check "Agent $agent file exists" "[ -f packages/agents/${agent}_agent.py ]"
    done
    check "Agent registry has 24 agents" "python3 -c \"from packages.agents import AGENT_REGISTRY; assert len(AGENT_REGISTRY) == 24, f'Got {len(AGENT_REGISTRY)}'\""
fi

if [ "$PHASE" == "4" ] || [ "$PHASE" == "all" ]; then
    echo ""
    echo "💾 Phase 4: Memory System"
    check "ShortTermMemory module exists" "[ -f packages/core/memory/short_term.py ]"
    check "LongTermMemory module exists" "[ -f packages/core/memory/long_term.py ]"
    check "SkillMemory module exists" "[ -f packages/core/memory/skill_memory.py ]"
fi

if [ "$PHASE" == "5" ] || [ "$PHASE" == "all" ]; then
    echo ""
    echo "🔀 Phase 5: Hybrid LLM Router"
    check "LLM Router module exists" "[ -f packages/core/llm/router.py ]"
    check "LLM Router has tiers" "python3 -c \"from packages.core.llm.router import LLM_TIERS; assert len(LLM_TIERS) >= 3, f'Got {len(LLM_TIERS)}'\""
    check "WindsurfAPI .env exists" "[ -f packages/windsurf-api/.env ]"
    check "WindsurfAPI health endpoint" "curl -sf http://localhost:3003/health"
fi

if [ "$PHASE" == "8" ] || [ "$PHASE" == "all" ]; then
    echo ""
    echo "🚀 Phase 8: Production"
    check "Helm chart exists" "[ -f helm/Chart.yaml ]"
    check "K8s namespace exists" "[ -f k8s/namespace.yaml ]"
    check "Prometheus config exists" "[ -f k8s/prometheus-config.yaml ]"
    check "Grafana dashboard exists" "[ -f k8s/grafana-dashboard.json ]"
fi

echo ""
echo "═══════════════════════════════════════"
echo "  Results: ✅ $PASS passed  ❌ $FAIL failed"
echo "═══════════════════════════════════════"

[ $FAIL -eq 0 ] && exit 0 || exit 1
