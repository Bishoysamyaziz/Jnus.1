#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# OneAgent OS — Unified Deployment Script
# ═══════════════════════════════════════════════════════════════════
# يدعم 3 طرق للنشر:
#   1. VPS (Docker + Nginx)
#   2. Cloudflare Tunnel (محلي)
#   3. Render (سحابي)
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     OneAgent OS — Unified Deployment Script        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"

# ── Load .env ──────────────────────────────────────────────────────
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo -e "${GREEN}✓ .env loaded${NC}"
else
    echo -e "${RED}✗ .env not found. Run: cp .env.example .env${NC}"
    exit 1
fi

# ── Select Mode ────────────────────────────────────────────────────
echo ""
echo -e "Choose deployment mode:"
echo -e "  ${CYAN}1${NC}) VPS (Docker + Nginx) — ${GREEN}Recommended for production${NC}"
echo -e "  ${CYAN}2${NC}) Cloudflare Tunnel — ${YELLOW}Free, for testing${NC}"
echo -e "  ${CYAN}3${NC}) Render.com — ${YELLOW}Easiest, free tier${NC}"
echo -e "  ${CYAN}4${NC}) Local development only"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)  # ── VPS Mode ──────────────────────────────────────────────
        echo -e "${CYAN}━━━ VPS Deployment ─━━${NC}"
        read -p "Enter VPS IP address: " VPS_IP
        read -p "Enter VPS SSH user [root]: " VPS_USER
        VPS_USER=${VPS_USER:-root}
        read -p "Enter domain (e.g., api.oneagent-os.com) [optional]: " DOMAIN

        echo -e "${YELLOW}→ Copying files to VPS...${NC}"
        rsync -avz --exclude 'node_modules' --exclude '.next' --exclude '__pycache__' \
            --exclude '.git' --exclude '*.pyc' \
            ./ ${VPS_USER}@${VPS_IP}:/opt/oneagent/

        echo -e "${YELLOW}→ Installing Docker on VPS...${NC}"
        ssh ${VPS_USER}@${VPS_IP} "
            apt update && apt install -y docker.io docker-compose-v2 nginx certbot python3-certbot-nginx
            cd /opt/oneagent
            docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
        "

        if [ -n "$DOMAIN" ]; then
            echo -e "${YELLOW}→ Setting up Nginx + SSL for $DOMAIN...${NC}"
            ssh ${VPS_USER}@${VPS_IP} "
                cat > /etc/nginx/sites-available/oneagent << 'EOF'
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
EOF
                ln -sf /etc/nginx/sites-available/oneagent /etc/nginx/sites-enabled/
                nginx -t && systemctl reload nginx
                certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN || true
            "
        fi

        echo -e "${GREEN}✅ VPS deployment complete!${NC}"
        echo -e "   API URL: ${CYAN}http://${VPS_IP}:8000${NC}"
        [ -n "$DOMAIN" ] && echo -e "   Domain: ${CYAN}https://${DOMAIN}${NC}"
        echo -e "   ${YELLOW}→ Update NEXT_PUBLIC_API_URL in .env and redeploy frontend${NC}"
        ;;

    2)  # ── Cloudflare Tunnel Mode ────────────────────────────────
        echo -e "${CYAN}━━━ Cloudflare Tunnel Deployment ─━━${NC}"

        # Check if cloudflared is installed
        if ! command -v cloudflared &> /dev/null; then
            echo -e "${YELLOW}⚠ cloudflared not found. Installing...${NC}"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                brew install cloudflared
            else
                wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
                chmod +x cloudflared-linux-amd64
                sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
            fi
        fi

        echo -e "${YELLOW}→ Starting Docker services...${NC}"
        docker compose up -d --build

        echo -e "${YELLOW}→ Starting Cloudflare Tunnel...${NC}"
        echo -e "${GREEN}✓ Tunnel will start. Copy the URL shown below.${NC}"
        echo -e "${GREEN}✓ Then update NEXT_PUBLIC_API_URL in .env${NC}"
        echo ""
        cloudflared tunnel --url http://localhost:8000
        ;;

    3)  # ── Render Mode ───────────────────────────────────────────
        echo -e "${CYAN}━━━ Render.com Deployment ─━━${NC}"
        echo -e "${YELLOW}→ render.yaml is already configured.${NC}"
        echo -e "${YELLOW}→ Push to GitHub and connect to Render.${NC}"
        echo ""
        echo -e "Steps:"
        echo -e "  1. ${CYAN}git push origin main${NC}"
        echo -e "  2. Go to ${CYAN}https://dashboard.render.com${NC}"
        echo -e "  3. Click 'New +' → 'Blueprint'"
        echo -e "  4. Connect your GitHub repo"
        echo -e "  5. Render will auto-deploy using render.yaml"
        echo -e "  6. Get your URL: ${CYAN}https://oneagent-os-api.onrender.com${NC}"
        echo -e "  7. Update NEXT_PUBLIC_API_URL in .env"
        echo ""
        echo -e "${YELLOW}⚠ Note: Render free tier sleeps after inactivity${NC}"
        ;;

    4)  # ── Local Development ─────────────────────────────────────
        echo -e "${CYAN}━━━ Local Development ─━━${NC}"
        echo -e "${YELLOW}→ Starting infrastructure services...${NC}"
        docker compose up -d redis postgres qdrant ollama windsurf-api

        echo -e "${YELLOW}→ Starting API...${NC}"
        echo -e "   Run in a separate terminal:"
        echo -e "   ${CYAN}make dev-api${NC}"
        echo ""
        echo -e "${YELLOW}→ Starting Frontend...${NC}"
        echo -e "   Run in a separate terminal:"
        echo -e "   ${CYAN}make dev-frontend${NC}"
        echo ""
        echo -e "${GREEN}✓ Local setup ready!${NC}"
        echo -e "   API:      ${CYAN}http://localhost:8000${NC}"
        echo -e "   Frontend: ${CYAN}http://localhost:3000${NC}"
        echo -e "   Docs:     ${CYAN}http://localhost:8000/docs${NC}"
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ OneAgent OS deployment complete!                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
