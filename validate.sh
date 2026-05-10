#!/bin/bash
# ============================================================
# OneAgent OS — Validation Script
# يتحقق من اكتمال كل phase قبل البدء في التالية
# Usage: bash scripts/validate.sh [phase_number]
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0

pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASS++)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; ((FAIL++)); }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

check_file() {
    if [ -f "$1" ]; then pass "File exists: $1"; else fail "Missing file: $1"; fi
}

check_dir() {
    if [ -d "$1" ]; then pass "Directory exists: $1"; else fail "Missing directory: $1"; fi
}

check_python_import() {
    if python3 -c "import $1" 2>/dev/null; then pass "Python import: $1"; else fail "Python import failed: $1"; fi
}

check_docker_service() {
    local service=$1
    if docker compose ps "$service" 2>/dev/null | grep -q "Up"; then
        pass "Docker service running: $service"
    elif docker compose ps "$service" 2>/dev/null | grep -q "running"; then
        pass "Docker service running: $service"
    else
        warn "Docker service not running: $service (may need 'docker compose up -d')"
    fi
}

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  OneAgent OS — Validation Script${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# === Phase 1: Foundation ===
validate_phase1() {
    echo -e "${YELLOW}--- Phase 1: Foundation ---${NC}"
    check_file "docker-compose.yml"
    check_file "Dockerfile.api"
    check_file "Dockerfile.frontend"
    check_file ".env.example"
    check_file "requirements.txt"
    check_file "pyproject.toml"
    check_file ".gitignore"
    check_dir "packages/core"
    check_dir "packages/api"
    check_dir "packages/agents"
    check_dir "packages/frontend"
    check_dir "packages/workers"
    check_python_import "packages.core"
    check_python_import "packages.api"
    check_python_import "packages.agents"
    echo ""
}

# === Phase 2: Brain Engine ===
validate_phase2() {
    echo -e "${YELLOW}--- Phase 2: Brain Engine ---${NC}"
    check_file "packages/core/intent/classifier.py"
    check_file "packages/core/planning/task_graph.py"
    check_file "packages/core/planning/planner.py"
    check_file "packages/core/orchestrator.py"
    check_file "packages/core/agent_selector.py"
    check_file "packages/core/base_agent.py"
    check_file "packages/core/models.py"
    check_python_import "packages.core.intent.classifier"
    check_python_import "packages.core.planning.task_graph"
    check_python_import "packages.core.planning.planner"
    check_python_import "packages.core.orchestrator"
    check_python_import "packages.core.agent_selector"
    echo ""
}

# === Phase 3: 24 Frameworks ===
validate_phase3() {
    echo -e "${YELLOW}--- Phase 3: 24 Frameworks ---${NC}"
    local count=0
    for f in packages/agents/*_agent.py; do
        if [ -f "$f" ]; then
            pass "Agent file: $(basename $f)"
            ((count++))
        fi
    done
    if [ "$count" -eq 24 ]; then
        pass "All 24 agent files present"
    else
        fail "Expected 24 agent files, found $count"
    fi
    echo ""
}

# === Phase 4: Memory ===
validate_phase4() {
    echo -e "${YELLOW}--- Phase 4: Memory ---${NC}"
    check_file "packages/core/memory/short_term.py"
    check_file "packages/core/memory/long_term.py"
    check_file "packages/core/memory/skill_memory.py"
    check_python_import "packages.core.memory.short_term"
    check_python_import "packages.core.memory.long_term"
    check_python_import "packages.core.memory.skill_memory"
    echo ""
}

# === Phase 5: LLM Router ===
validate_phase5() {
    echo -e "${YELLOW}--- Phase 5: LLM Router ---${NC}"
    check_file "packages/core/llm/router.py"
    check_python_import "packages.core.llm.router"
    echo ""
}

# === Phase 6: Tools ===
validate_phase6() {
    echo -e "${YELLOW}--- Phase 6: Tools ---${NC}"
    check_dir "packages/core/tools"
    check_file "packages/core/tools/__init__.py"
    check_file "packages/core/tools/code_executor.py"
    check_file "packages/core/tools/web_search.py"
    check_file "packages/core/tools/browser.py"
    echo ""
}

# === Phase 7: API + Frontend ===
validate_phase7() {
    echo -e "${YELLOW}--- Phase 7: API + Frontend ---${NC}"
    check_file "packages/api/main.py"
    check_file "packages/api/__init__.py"
    check_python_import "packages.api.main"
    echo ""
}

# === Phase 8: Production ===
validate_phase8() {
    echo -e "${YELLOW}--- Phase 8: Production ---${NC}"
    check_dir "k8s"
    check_dir "helm"
    check_file "k8s/deployment.yaml"
    check_file "k8s/service.yaml"
    check_file "helm/Chart.yaml"
    echo ""
}

# === Tests ===
validate_tests() {
    echo -e "${YELLOW}--- Tests ---${NC}"
    local test_count=0
    for f in packages/core/tests/test_*.py packages/api/tests/test_*.py; do
        if [ -f "$f" ]; then
            pass "Test file: $(basename $f)"
            ((test_count++))
        fi
    done
    info "Total test files: $test_count"
    echo ""
}

# === Docker Services ===
validate_docker() {
    echo -e "${YELLOW}--- Docker Services ---${NC}"
    check_docker_service "api"
    check_docker_service "redis"
    check_docker_service "postgres"
    check_docker_service "qdrant"
    echo ""
}

# === Main ===
if [ $# -eq 0 ]; then
    # Validate all phases
    validate_phase1
    validate_phase2
    validate_phase3
    validate_phase4
    validate_phase5
    validate_phase6
    validate_phase7
    validate_phase8
    validate_tests
    validate_docker
else
    # Validate specific phase
    case $1 in
        1) validate_phase1 ;;
        2) validate_phase2 ;;
        3) validate_phase3 ;;
        4) validate_phase4 ;;
        5) validate_phase5 ;;
        6) validate_phase6 ;;
        7) validate_phase7 ;;
        8) validate_phase8 ;;
        tests) validate_tests ;;
        docker) validate_docker ;;
        *) echo "Invalid phase: $1 (use 1-8, tests, or docker)" ;;
    esac
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}PASSED: $PASS${NC} | ${RED}FAILED: $FAIL${NC}"
echo -e "${BLUE}============================================${NC}"

# Exit with error if any failures
[ "$FAIL" -eq 0 ] || exit 1
