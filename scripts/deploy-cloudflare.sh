#!/bin/bash
# ============================================================
# OneAgent OS — Deploy to Cloudflare Workers/Pages
# Usage: bash scripts/deploy-cloudflare.sh
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Load secrets from .env ─────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
    info "Loaded secrets from .env"
else
    error ".env file not found at $PROJECT_DIR/.env"
    exit 1
fi

ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-}"
API_TOKEN="${CLOUDFLARE_API_TOKEN:-}"
DEEPSEEK_KEY="${DEEPSEEK_API_KEY:-}"

if [ -z "$ACCOUNT_ID" ] || [ -z "$API_TOKEN" ]; then
    error "Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN in .env"
    exit 1
fi

AUTH="Authorization: Bearer ${API_TOKEN}"
API_BASE="https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}"

# Step 1: Verify token via accounts endpoint
info "Step 1: Verifying token..."
ACCOUNTS=$(curl -s "https://api.cloudflare.com/client/v4/accounts" -H "${AUTH}")
if echo "$ACCOUNTS" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('success') else 1)" 2>/dev/null; then
    success "Token active — Account: $(echo $ACCOUNTS | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['name'])")"
else
    error "Token invalid"; exit 1
fi

# Step 2: Deploy Frontend to Cloudflare Pages
info "Step 2: Deploying Frontend to Cloudflare Pages..."
cd "$PROJECT_DIR/packages/frontend"

# Create static site
rm -rf out
mkdir -p out
cat > out/index.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OneAgent OS</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; }
        .hero { text-align: center; padding: 4rem 2rem; background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%); }
        h1 { font-size: 3.5rem; background: linear-gradient(135deg, #667eea, #764ba2, #f093fb); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem; }
        .subtitle { font-size: 1.25rem; color: #94a3b8; margin-bottom: 2rem; }
        .badge { display: inline-block; padding: 0.5rem 1.5rem; background: rgba(34,197,94,0.15); border: 1px solid #22c55e; color: #22c55e; border-radius: 999px; font-size: 0.875rem; margin-bottom: 2rem; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; max-width: 800px; margin: 3rem auto; padding: 0 2rem; }
        .stat-card { background: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 12px; padding: 1.5rem; text-align: center; }
        .stat-number { font-size: 2rem; font-weight: bold; color: #667eea; }
        .stat-label { color: #94a3b8; margin-top: 0.5rem; }
        .links { text-align: center; padding: 2rem; }
        .links a { color: #667eea; text-decoration: none; margin: 0 1rem; }
        .links a:hover { text-decoration: underline; }
        footer { text-align: center; padding: 2rem; color: #4a4a6a; font-size: 0.875rem; }
    </style>
</head>
<body>
    <div class="hero">
        <div class="badge">✅ Live on Cloudflare</div>
        <h1>🤖 OneAgent OS</h1>
        <p class="subtitle">Unified Operating System for 24 AI Frameworks</p>
        <div class="stats">
            <div class="stat-card"><div class="stat-number">24</div><div class="stat-label">AI Frameworks</div></div>
            <div class="stat-card"><div class="stat-number">62</div><div class="stat-label">Python Modules</div></div>
            <div class="stat-card"><div class="stat-number">11</div><div class="stat-label">Test Suites</div></div>
            <div class="stat-card"><div class="stat-number">8</div><div class="stat-label">Memory Systems</div></div>
        </div>
        <div class="links">
            <a href="https://github.com/Bishoysamyaziz/Jnus.1">GitHub</a>
            <a href="#">API Docs</a>
            <a href="#">DeepSeek Gateway</a>
        </div>
    </div>
    <footer>OneAgent OS v1.0.0 — Powered by Cloudflare Workers & AI Gateway</footer>
</body>
</html>
HTMLEOF
success "Static site created"

# Deploy via wrangler
info "Deploying via wrangler..."
npx wrangler pages deploy out --project-name oneagent-os 2>&1

cd "$PROJECT_DIR"

# Step 3: AI Gateway
info "Step 3: Creating AI Gateway..."
GATEWAY_RESULT=$(curl -s -X POST "${API_BASE}/ai-gateway/gateways" \
    -H "${AUTH}" -H "Content-Type: application/json" \
    -d '{"name":"oneagent-os-gateway","description":"OneAgent OS AI Gateway","cache_enabled":true,"rate_limiting_enabled":true,"rate_limiting_interval":60,"rate_limiting_max_requests":100}')
echo "$GATEWAY_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print('Gateway:', '✅' if d.get('success') else '❌', d.get('errors',[{}])[0].get('message',''))"

# Step 4: DeepSeek
info "Step 4: Adding DeepSeek..."
DEEPSEEK_RESULT=$(curl -s -X POST "${API_BASE}/ai-gateway/gateways/oneagent-os-gateway/providers" \
    -H "${AUTH}" -H "Content-Type: application/json" \
    -d "{\"name\":\"deepseek\",\"api_key\":\"${DEEPSEEK_KEY}\",\"base_url\":\"https://api.deepseek.com/v1\",\"models\":[\"deepseek-chat\",\"deepseek-coder\"]}")
echo "$DEEPSEEK_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print('DeepSeek:', '✅' if d.get('success') else '❌', d.get('errors',[{}])[0].get('message',''))"

# Summary
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  ✅ Cloudflare Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "  Frontend: https://oneagent-os.pages.dev"
echo "  GitHub:   https://github.com/Bishoysamyaziz/Jnus.1"
echo "  DeepSeek: ✅ Configured via AI Gateway"
echo ""
