#!/bin/bash
# سكريبت لـ push الخطة لـ GitHub
# Usage: ./push-to-git.sh <your-github-username> <repo-name>
# Example: ./push-to-git.sh selina oneagent-plan

USERNAME=${1:-"your-username"}
REPO=${2:-"oneagent-plan"}

echo "🚀 Pushing OneAgent Plan to GitHub..."
echo "Repo: https://github.com/$USERNAME/$REPO"
echo ""

# Initialize git in the plan directory
cd /home/claude/oneagent-plan

git init
git add .
git commit -m "feat: OneAgent OS — complete 16-week production plan

24 frameworks, 8 phases, 16 weeks.
Fully documented with code examples, architecture, and acceptance criteria.

Phases:
- Phase 1: Foundation Core (Week 1-2)
- Phase 2: Brain & Intent Engine (Week 3-4)
- Phase 3: 24 Framework Integration (Week 5-8)
- Phase 4: Memory System (Week 9-10)
- Phase 5: Hybrid LLM Router (Week 11)
- Phase 6: Tool Execution Layer (Week 12-13)
- Phase 7: API + Frontend (Week 14-15)
- Phase 8: Production Hardening (Week 16)"

git branch -M main
git remote add origin "https://github.com/$USERNAME/$REPO.git"
git push -u origin main

echo ""
echo "✅ Done! Check: https://github.com/$USERNAME/$REPO"
