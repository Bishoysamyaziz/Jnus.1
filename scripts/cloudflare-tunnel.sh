#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# OneAgent OS — Cloudflare Tunnel Quick Start
# ═══════════════════════════════════════════════════════════════════
# يُشغّل Cloudflare Tunnel لتعريض الـ API المحلي للإنترنت
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  OneAgent OS — Cloudflare Tunnel                    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"

# ── 1. Check/Install cloudflared ───────────────────────────────────
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}⚠ cloudflared not found. Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install cloudflared
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
        chmod +x cloudflared-linux-amd64
        sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
    else
        echo -e "${RED}✗ Unsupported OS. Install cloudflared manually: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ cloudflared installed${NC}"
fi

# ── 2. Authenticate (if needed) ────────────────────────────────────
if [ ! -f ~/.cloudflared/cert.pem ]; then
    echo -e "${YELLOW}→ Authenticating with Cloudflare...${NC}"
    echo -e "${YELLOW}   (A browser window will open — log in to Cloudflare)${NC}"
    cloudflared tunnel login
fi

# ── 3. Start Docker services ───────────────────────────────────────
echo -e "${CYAN}━━━ Starting Docker Services ─━━${NC}"
docker compose up -d --build
echo -e "${GREEN}✓ Docker services started${NC}"

# ── 4. Verify API locally ──────────────────────────────────────────
echo -e "${CYAN}━━━ Verifying Local API ─━━${NC}"
sleep 3
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is healthy at http://localhost:8000${NC}"
else
    echo -e "${RED}✗ API health check failed. Check: docker compose logs api${NC}"
    exit 1
fi

# ── 5. Start Tunnel ────────────────────────────────────────────────
echo -e "${CYAN}━━━ Starting Cloudflare Tunnel ─━━${NC}"
echo ""
echo -e "${GREEN}✅ Tunnel is running!${NC}"
echo -e "${GREEN}   Copy the URL below (looks like: https://oneagent-api.trycloudflare.com)${NC}"
echo ""
echo -e "${YELLOW}   Then:${NC}"
echo -e "   1. Edit ${CYAN}.env${NC} and set:"
echo -e "      ${CYAN}NEXT_PUBLIC_API_URL=https://your-tunnel-url.trycloudflare.com${NC}"
echo -e "   2. Rebuild and redeploy frontend:"
echo -e "      ${CYAN}bash scripts/deploy-cloudflare.sh${NC}"
echo ""
echo -e "${YELLOW}   Press Ctrl+C to stop the tunnel${NC}"
echo ""

# Run tunnel
cloudflared tunnel --url http://localhost:8000
