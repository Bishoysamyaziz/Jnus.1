#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# OneAgent OS — Cloudflare Secure Deployment Script
# ═══════════════════════════════════════════════════════════════════
# This script deploys to Cloudflare Workers using secrets (encrypted)
# instead of plain-text environment variables.
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     OneAgent OS — Cloudflare Secure Deploy         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"

# ── Load .env (without exposing secrets in logs) ──────────────────
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo -e "${GREEN}✓ .env loaded${NC}"
else
    echo -e "${RED}✗ .env not found${NC}"
    exit 1
fi

# ── Verify Cloudflare is installed ────────────────────────────────
if ! command -v wrangler &> /dev/null; then
    echo -e "${YELLOW}⚠ wrangler not found. Installing...${NC}"
    npm install -g wrangler
fi

# ── Authenticate with Cloudflare using deploy token ───────────────
echo -e "${CYAN}━━━ Authenticating with Cloudflare ─━━${NC}"

# Try primary deploy token first, then fallback to secondary
if [ -n "${CLOUDFLARE_API_TOKEN_DEPLOY:-}" ]; then
    echo "$CLOUDFLARE_API_TOKEN_DEPLOY" | wrangler login --token-stdin
    echo -e "${GREEN}✓ Authenticated with primary deploy token${NC}"
elif [ -n "${CLOUDFLARE_API_TOKEN_DEPLOY2:-}" ]; then
    echo "$CLOUDFLARE_API_TOKEN_DEPLOY2" | wrangler login --token-stdin
    echo -e "${GREEN}✓ Authenticated with secondary deploy token${NC}"
elif [ -n "${CLOUDFLARE_API_TOKEN:-}" ]; then
    echo "$CLOUDFLARE_API_TOKEN" | wrangler login --token-stdin
    echo -e "${GREEN}✓ Authenticated with API token${NC}"
else
    echo -e "${RED}✗ No Cloudflare token found in .env${NC}"
    exit 1
fi

# ── Deploy API Worker with secrets ────────────────────────────────
echo -e "${CYAN}━━━ Deploying API Worker ─━━${NC}"

cd packages/api

# Set secrets (encrypted — never visible in wrangler.toml)
echo -e "${YELLOW}→ Setting DEEPSEEK_API_KEY as secret...${NC}"
echo "$DEEPSEEK_API_KEY" | wrangler secret put DEEPSEEK_API_KEY --env production

echo -e "${YELLOW}→ Setting DEEPSEEK_BASE_URL as secret...${NC}"
echo "$DEEPSEEK_BASE_URL" | wrangler secret put DEEPSEEK_BASE_URL --env production

echo -e "${YELLOW}→ Setting DEEPSEEK_MODEL as secret...${NC}"
echo "$DEEPSEEK_MODEL" | wrangler secret put DEEPSEEK_MODEL --env production

echo -e "${YELLOW}→ Deploying API Worker...${NC}"
wrangler deploy --env production

cd ../..

# ── Deploy Frontend ───────────────────────────────────────────────
echo -e "${CYAN}━━━ Deploying Frontend ─━━${NC}"

cd packages/frontend

echo -e "${YELLOW}→ Setting API_URL as secret...${NC}"
echo "$API_URL" | wrangler secret put API_URL --env production

echo -e "${YELLOW}→ Deploying Frontend...${NC}"
wrangler pages deploy . --project-name oneagent-os-frontend

cd ../..

# ── Done ──────────────────────────────────────────────────────────
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ OneAgent OS deployed successfully!              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "API:     ${CYAN}https://oneagent-os-api.bishoysamyaziz.workers.dev${NC}"
echo -e "Frontend: ${CYAN}https://oneagent-os.pages.dev${NC}"
