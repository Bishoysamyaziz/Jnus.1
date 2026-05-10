#!/bin/bash

# ═══════════════════════════════════════════════════════════════

# OneAgent Brain Extractor v2.0

# ═══════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

OK="${GREEN}✅${NC}"
SKIP="${YELLOW}⚠️${NC}"
FAIL="${RED}❌${NC}"

TOTAL=0
SUCCESS=0
FAILED=0

sparse_clone() {
local NAME=$1
local URL=$2
shift 2
local PATHS=("$@")

TOTAL=$((TOTAL + 1))
echo -e "\n${CYAN}${BOLD}[$TOTAL] $NAME${NC}"

if [ -d "$NAME/.git" ]; then
echo -e "    ${SKIP} موجود بالفعل — skip"
SUCCESS=$((SUCCESS + 1))
return
fi

if git clone --depth 1 --filter=blob:none --sparse "$URL" "$NAME"; then
cd "$NAME"
git sparse-checkout set "${PATHS[@]}"
cd ..
SIZE=$(du -sh "$NAME" | cut -f1)
echo -e "    ${OK} نجح — الحجم: ${BOLD}$SIZE${NC}"
SUCCESS=$((SUCCESS + 1))
else
echo -e "    ${FAIL} فشل"
FAILED=$((FAILED + 1))
fi
}

echo "🚀 OneAgent Brain Collector"

mkdir -p ~/oneagent-brains
cd ~/oneagent-brains

# Tier 1

sparse_clone "metagpt" "https://github.com/geekan/MetaGPT.git" \
"metagpt/provider" "metagpt/roles" "metagpt/actions"

sparse_clone "autogen" "https://github.com/microsoft/autogen.git" \
"python/packages/autogen-core/src"

sparse_clone "letta" "https://github.com/letta-ai/letta.git" \
"letta/memory" "letta/agent.py"

sparse_clone "openhands" "https://github.com/All-Hands-AI/OpenHands.git" \
"openhands/core" "skills"

# Tier 2

sparse_clone "langchain" "https://github.com/langchain-ai/langchain.git" \
"libs/langchain/langchain/agents"

sparse_clone "crewai" "https://github.com/crewAIInc/crewAI.git" \
"src/crewai"

# Tier 3

sparse_clone "aider" "https://github.com/paul-gauthier/aider.git" \
"aider/coders"

sparse_clone "taskweaver" "https://github.com/microsoft/TaskWeaver.git" \
"taskweaver/memory"

# Tier 4

sparse_clone "mem0" "https://github.com/mem0ai/mem0.git" \
"mem0/memory"

# Tier 5

sparse_clone "langgraph" "https://github.com/langchain-ai/langgraph.git" \
"langgraph/"

sparse_clone "llama-index" "https://github.com/run-llama/llama_index.git" \
"llama-index/core"

sparse_clone "haystack" "https://github.com/deepset-ai/haystack.git" \
"haystack/"

sparse_clone "semantic-kernel" "https://github.com/microsoft/semantic-kernel.git" \
"python/semantic_kernel/"

sparse_clone "botpress" "https://github.com/botpress/botpress.git" \
"packages/bp/src/core"

# Tier 6

sparse_clone "rasa" "https://github.com/RasaHQ/rasa.git" \
"rasa/core"

sparse_clone "opendialog" "https://github.com/opendialogai/opendialog.git" \
"opendialog/"

sparse_clone "agentverse" "https://github.com/OpenBMB/AgentVerse.git" \
"agentverse/"

sparse_clone "camel" "https://github.com/camel-ai/camel.git" \
"camel/"

sparse_clone "smolagents" "https://github.com/huggingface/smolagents.git" \
"src/smolagents/"

sparse_clone "autogpt" "https://github.com/Significant-Gravitas/AutoGPT.git" \
"autogpt/"

# Tier 7 (Super Agents)

sparse_clone "babyagi" "https://github.com/yoheinakajima/babyagi.git" \
"babyagi/"

sparse_clone "agentgpt" "https://github.com/reworkd/AgentGPT.git" \
"src/"

sparse_clone "superagi" "https://github.com/TransformerOptimus/SuperAGI.git" \
"superagi/"

sparse_clone "swarm" "https://github.com/openai/swarm.git" \
"swarm/"

sparse_clone "huggingface-agents" "https://github.com/huggingface/transformers.git" \
"src/transformers/agents"

# ZIP

zip -r brains-core.zip */ 2>/dev/null

echo ""
echo "✅ تم:"
echo "~/oneagent-brains/brains-core.zip"