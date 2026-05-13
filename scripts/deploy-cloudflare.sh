#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# OneAgent OS — Cloudflare Frontend Deployment Script
# ═══════════════════════════════════════════════════════════════════
# ✅ Production Fix: هذا السكريبت ينشر FRONTEND فقط على Cloudflare Pages
# الـ API يُنشر على VPS أو Render أو Cloudflare Tunnel — ليس على Workers
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  OneAgent OS — Cloudflare Frontend Deploy          ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"

# ── Load .env ──────────────────────────────────────────────────────
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo -e "${GREEN}✓ .env loaded${NC}"
else
    echo -e "${RED}✗ .env not found${NC}"
    exit 1
fi

# ── Verify wrangler ────────────────────────────────────────────────
if ! command -v wrangler &> /dev/null; then
    echo -e "${YELLOW}⚠ wrangler not found. Installing...${NC}"
    npm install -g wrangler
fi

# ── Build Frontend ─────────────────────────────────────────────────
echo -e "${CYAN}━━━ Building Frontend ─━━${NC}"
cd packages/frontend

echo -e "${YELLOW}→ Using API URL: ${NEXT_PUBLIC_API_URL:-http://localhost:8000}${NC}"
NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000} pnpm build

if [ ! -d "out" ]; then
    echo -e "${RED}✗ Build failed — 'out' directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Frontend built successfully${NC}"

# ── Deploy to Cloudflare Pages ─────────────────────────────────────
echo -e "${CYAN}━━━ Deploying to Cloudflare Pages ─━━${NC}"

# Deploy using wrangler pages
wrangler pages deploy out/ --project-name oneagent-os --branch production

echo -e "${GREEN}✓ Frontend deployed to Cloudflare Pages${NC}"

cd ../..

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ OneAgent OS Frontend deployed!                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Frontend: ${CYAN}https://oneagent-os.pages.dev${NC}"
echo -e "API:      ${CYAN}${NEXT_PUBLIC_API_URL:-http://localhost:8000}${NC}"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT:${NC}"
echo -e "  - API is NOT deployed by this script"
echo -e "  - Make sure your backend is running at: ${CYAN}${NEXT_PUBLIC_API_URL:-http://localhost:8000}${NC}"
echo -e "  - To deploy API, use: ${CYAN}bash scripts/deploy.sh${NC}"
