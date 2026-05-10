#!/bin/bash
# OneAgent OS — Push to GitHub
# Usage: ./push-to-git.sh <your-github-username> <repo-name>
# Example: ./push-to-git.sh Bishoysamyaziz Jnus.1

set -e

USERNAME=${1:-"Bishoysamyaziz"}
REPO=${2:-"Jnus.1"}
BRANCH=${3:-"main"}

echo "═══════════════════════════════════════"
echo "  🚀 Pushing OneAgent OS to GitHub"
echo "═══════════════════════════════════════"
echo "  Repo: https://github.com/$USERNAME/$REPO"
echo "  Branch: $BRANCH"
echo ""

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if git is initialized
if [ ! -d .git ]; then
    echo "▶ Initializing git repository..."
    git init
    git branch -M "$BRANCH"
fi

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "▶ Adding remote origin..."
    git remote add origin "https://github.com/$USERNAME/$REPO.git"
fi

# Add all files
echo "▶ Staging all files..."
git add -A

# Create commit
echo "▶ Creating commit..."
git commit -m "feat: OneAgent OS — Complete Multi-Agent Operating System

24 AI frameworks integrated under one unified OS.
8 phases, monorepo architecture, Docker + K8s ready.

Includes:
- Core engine: IntentClassifier, TaskGraph, Orchestrator
- 24 agent wrappers (CrewAI, AutoGen, LangChain, etc.)
- Three-tier memory: Redis, PostgreSQL, Qdrant
- Hybrid LLM Router: Ollama → WindsurfAPI → Claude/OpenAI
- FastAPI backend with SSE streaming
- Next.js frontend with real-time chat
- CI/CD pipeline with GitHub Actions
- Helm charts + K8s manifests for production
- Full documentation with architecture diagrams" || echo "ℹ️  Nothing new to commit"

# Push
echo "▶ Pushing to GitHub..."
git push -u origin "$BRANCH" 2>&1 || {
    echo ""
    echo "⚠️  Push failed. Possible reasons:"
    echo "  1. No GitHub authentication configured"
    echo "  2. Repository doesn't exist"
    echo "  3. Branch protection rules"
    echo ""
    echo "  To fix:"
    echo "  gh auth login"
    echo "  gh repo create $USERNAME/$REPO --public --push --source ."
    exit 1
}

echo ""
echo "═══════════════════════════════════════"
echo "  ✅ Done! Check your repo:"
echo "  https://github.com/$USERNAME/$REPO"
echo "═══════════════════════════════════════"
