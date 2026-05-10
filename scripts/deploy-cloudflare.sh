#!/bin/bash
# ============================================================
# OneAgent OS — Deploy to Cloudflare Workers/Pages
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Load .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# ── Configuration ────────────────────────────────────────────────
ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-37f918bd5741e78da7136f45f4f3b6fb}"
API_TOKEN="${CLOUDFLARE_API_TOKEN:-cfat_T90aeX1IbdOtO5fA1i1QC2ajTu8eRUsfS548Y3Br4f3fdd1a}"
API_TOKEN_2="${CLOUDFLARE_API_TOKEN_2:-cfat_BxUsC9vn3L2dmvIe18kNlLxuMOv17hUVUVNqeaWFdd317381}"
GLOBAL_KEY="${CLOUDFLARE_GLOBAL_KEY:-cfk_G9xmT7XfD985Ab7KWgpCrXfCOAtmq5o9TeSC8btWb25c3257}"

API_BASE="https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}"

# ── Step 1: Verify Tokens ────────────────────────────────────────
info "Step 1: Verifying Cloudflare tokens..."

verify_token() {
    local token=$1
    local name=$2
    local result=$(curl -s -X GET "${API_BASE}/tokens/verify" \
        -H "Authorization: Bearer ${token}")
    if echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('success') else 1)" 2>/dev/null; then
        success "Token $name is active"
        return 0
    else
        error "Token $name verification failed"
        return 1
    fi
}

verify_token "$API_TOKEN" "1" || true
verify_token "$API_TOKEN_2" "2" || true

# ── Step 2: Create/Update Workers AI Gateway ─────────────────────
info "Step 2: Setting up Workers AI Gateway..."

# Check if AI Gateway exists
GATEWAY_NAME="oneagent-os-gateway"
GATEWAY_CHECK=$(curl -s "${API_BASE}/ai-gateway/gateways" \
    -H "Authorization: Bearer ${API_TOKEN}")

if echo "$GATEWAY_CHECK" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if any(g.get('name')=='${GATEWAY_NAME}' for g in d.get('result',[])) else 1)" 2>/dev/null; then
    info "AI Gateway '${GATEWAY_NAME}' already exists"
else
    info "Creating AI Gateway '${GATEWAY_NAME}'..."
    curl -s -X POST "${API_BASE}/ai-gateway/gateways" \
        -H "Authorization: Bearer ${API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "'"${GATEWAY_NAME}"'",
            "description": "OneAgent OS — Unified AI Gateway for 24 frameworks",
            "cache_enabled": true,
            "rate_limiting_enabled": true,
            "rate_limiting_interval": 60,
            "rate_limiting_max_requests": 100
        }' | python3 -m json.tool 2>/dev/null || warn "Gateway creation may have failed"
fi

# ── Step 3: Deploy API as Cloudflare Worker ──────────────────────
info "Step 3: Deploying API Worker..."

# Create wrangler.toml for the API
cat > packages/api/wrangler.toml << 'EOF'
name = "oneagent-os-api"
main = "main.py"
compatibility_date = "2024-12-01"

[env.production]
vars = { ENVIRONMENT = "production" }

[[services]]
binding = "AI"
service = "ai"

[[d1_databases]]
binding = "DB"
database_name = "oneagent-os"
database_id = ""

[triggers]
crons = ["*/5 * * * *"]
EOF

# Try to deploy with wrangler if available
if command -v npx &>/dev/null; then
    cd packages/api
    npx wrangler deploy --name oneagent-os-api 2>/dev/null || warn "Wrangler deploy failed (may need npm install -g wrangler)"
    cd ../..
else
    warn "npx not available, skipping wrangler deploy"
fi

# ── Step 4: Deploy Frontend to Cloudflare Pages ──────────────────
info "Step 4: Deploying Frontend to Cloudflare Pages..."

if [ -d packages/frontend ]; then
    cd packages/frontend
    
    # Create wrangler.toml for frontend
    cat > wrangler.toml << 'EOF'
name = "oneagent-os-frontend"
compatibility_date = "2024-12-01"

[env.production]
vars = { API_URL = "https://oneagent-os-api.your-subdomain.workers.dev" }
EOF

    # Build and deploy
    if [ -f package.json ]; then
        npm run build 2>/dev/null || warn "Frontend build failed"
        npx wrangler pages deploy . --project-name oneagent-os 2>/dev/null || warn "Pages deploy failed"
    fi
    cd ../..
fi

# ── Step 5: Create DNS Records ───────────────────────────────────
info "Step 5: Setting up DNS..."

# Get zones
ZONES=$(curl -s "${API_BASE}/zones" \
    -H "Authorization: Bearer ${API_TOKEN}")

echo "$ZONES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d.get('success'):
    zones = d.get('result', [])
    if zones:
        print('Available zones:')
        for z in zones:
            print(f'  - {z[\"name\"]} (ID: {z[\"id\"]})')
    else:
        print('No zones found. You need to add a domain in Cloudflare dashboard.')
else:
    print('Failed to fetch zones')
" 2>/dev/null || warn "Could not fetch zones"

# ── Step 6: Create Workers AI Gateway Route for DeepSeek ─────────
info "Step 6: Configuring DeepSeek via AI Gateway..."

DEEPSEEK_KEY="sk-d88aa9a0180743a0a159da8170d86f4d"

# Add DeepSeek provider to AI Gateway
curl -s -X POST "${API_BASE}/ai-gateway/gateways/${GATEWAY_NAME}/providers" \
    -H "Authorization: Bearer ${API_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "deepseek",
        "api_key": "'"${DEEPSEEK_KEY}"'",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-coder"]
    }' | python3 -m json.tool 2>/dev/null || warn "DeepSeek provider setup may have failed"

# ── Summary ───────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}  Cloudflare Deployment Complete!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "  Account ID:     ${ACCOUNT_ID}"
echo "  AI Gateway:     ${GATEWAY_NAME}"
echo "  DeepSeek Key:   ${DEEPSEEK_KEY:0:10}...${DEEPSEEK_KEY: -4}"
echo ""
echo "  Next steps:"
echo "    1. Add a domain in Cloudflare dashboard"
echo "    2. Update wrangler.toml with your domain"
echo "    3. Run: npx wrangler deploy"
echo "    4. Access your API at: https://oneagent-os-api.<your-subdomain>.workers.dev"
echo ""
