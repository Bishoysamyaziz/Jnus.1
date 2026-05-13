#!/bin/bash
# Generate all 24 Dockerfiles for agent isolation
# Usage: bash scripts/generate-dockerfiles.sh

AGENTS=(
  "crewai:CrewAIAgent:crewai"
  "metagpt:MetaGPTAgent:metagpt"
  "autogen:AutoGenAgent:pyautogen"
  "langchain:LangChainAgent:langchain"
  "superagi:SuperAGIAgent:superagi"
  "babyagi:BabyAGIAgent:babyagi"
  "aider:AiderAgent:aider-chat"
  "openhands:OpenHandsAgent:openhands-ai"
  "smolagents:SmolAgentsAgent:smolagents"
  "haystack:HaystackAgent:haystack-ai"
  "llamaindex:LlamaIndexAgent:llama-index"
  "langgraph:LangGraphAgent:langgraph"
  "camel:CAMELAgent:camel-ai"
  "letta:LettaAgent:letta"
  "mem0:Mem0Agent:mem0ai"
  "taskweaver:TaskWeaverAgent:taskweaver"
  "swarm:SwarmAgent:openai-swarm"
  "agentverse:AgentVerseAgent:agentverse"
  "autogpt:AutoGPTAgent:autogpt"
  "agentgpt:AgentGPTAgent:agentgpt"
  "huggingface:HuggingFaceAgent:huggingface-hub"
  "rasa:RasaAgent:rasa"
  "botpress:BotpressAgent:botpress"
  "semantic-kernel:SemanticKernelAgent:semantic-kernel"
)

for entry in "${AGENTS[@]}"; do
  IFS=":" read -r name class pip_pkg <<< "$entry"
  cat > "dockerfiles/Dockerfile.$name" << DOCKERFILE
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir $pip_pkg fastapi uvicorn anthropic openai httpx
COPY packages/agents/agent_http_wrapper.py .
COPY packages/agents/${name}_agent.py .
COPY packages/core/ ./core/
ENV AGENT_CLASS=$class
ENV AGENT_MODULE=${name}_agent
CMD ["uvicorn", "agent_http_wrapper:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKERFILE
  echo "✅ dockerfiles/Dockerfile.$name"
done

echo ""
echo "🎉 All 24 Dockerfiles generated!"
ls -la dockerfiles/
