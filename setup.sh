#!/bin/bash
# OneAgent OS — Initial Setup Script
# Run this first: chmod +x scripts/setup.sh && ./scripts/setup.sh

set -e

echo "═══════════════════════════════════════"
echo "  OneAgent OS — Setup"
echo "═══════════════════════════════════════"

# Check prerequisites
echo ""
echo "▶ Checking prerequisites..."

command -v docker >/dev/null 2>&1 || { echo "❌ Docker not installed"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 not installed"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js not installed"; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "❌ pnpm not installed. Run: npm i -g pnpm"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ git not installed"; exit 1; }

echo "✅ All prerequisites found"

# Create monorepo structure
echo ""
echo "▶ Creating monorepo structure..."

mkdir -p packages/{core,api,frontend,workers,agents}
mkdir -p packages/agents/{crewai,autogen,metagpt,camel,agentverse,semantic-kernel}
mkdir -p packages/agents/{smolagents,superagi,langchain,langgraph,taskweaver,swarm}
mkdir -p packages/agents/{haystack,babyagi,letta,llamaindex,aider,openhands}
mkdir -p packages/agents/{agentgpt,autogpt,huggingface,rasa,botpress,mem0}

echo "✅ Directory structure created"

# Copy .env.example
echo ""
echo "▶ Setting up environment..."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env created from .env.example"
    echo "⚠️  Edit .env and add your API keys before continuing"
else
    echo "✅ .env already exists"
fi

# Install Python dependencies
echo ""
echo "▶ Installing Python dependencies..."

pip install uv --quiet
uv pip install -r requirements.txt --quiet

echo "✅ Python dependencies installed"

# Install Node dependencies
echo ""
echo "▶ Installing Node dependencies..."
pnpm install --quiet

echo "✅ Node dependencies installed"

# Start Docker services
echo ""
echo "▶ Starting infrastructure services..."
docker compose up -d redis postgres qdrant

echo "⏳ Waiting for services to be ready..."
sleep 5

# Health check
echo ""
echo "▶ Running health check..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "⚠️  API not up yet — start it with: uvicorn packages.api.main:app --reload"

echo ""
echo "═══════════════════════════════════════"
echo "  ✅ Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: docker compose up"
echo "  3. Run: pnpm dev (frontend)"
echo "  4. Open: http://localhost:3000"
echo "═══════════════════════════════════════"
