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
        check "Agent $agent has execute()" "python3 -c \"from packages.agents.${agent}_agent import *; a = $(echo $agent | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++) printf toupper(substr($i,1,1)) substr($i,2); print ""}')Agent(); print('ok')\""
    done
fi

if [ "$PHASE" == "4" ] || [ "$PHASE" == "all" ]; then
    echo ""
    echo "💾 Phase 4: Memory System"
    check "ShortTermMemory save/get" "python3 -m pytest packages/core/tests/test_memory_short.py -q"
    check "LongTermMemory save/get" "python3 -m pytest packages/core/tests/test_memory_long.py -q"
    check "SkillMemory save/search" "python3 -m pytest packages/core/tests/test_memory_skill.py -q"
    check "Memory search < 100ms" "python3 scripts/benchmark_memory.py"
fi

if [ "$PHASE" == "8" ] || [ "$PHASE" == "all" ]; then
    echo ""
    echo "🚀 Phase 8: Production"
    check "Response time < 3s (simple task)" "python3 scripts/benchmark_response.py simple"
    check "Error rate < 0.1%" "python3 scripts/load_test.py --check-error-rate"
    check "Grafana accessible" "curl -sf http://localhost:3001/api/health"
fi

echo ""
echo "═══════════════════════════════════════"
echo "  Results: ✅ $PASS passed  ❌ $FAIL failed"
echo "═══════════════════════════════════════"

[ $FAIL -eq 0 ] && exit 0 || exit 1
