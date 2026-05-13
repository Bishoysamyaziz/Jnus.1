#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# OneAgent OS — VPS Setup Script
# ═══════════════════════════════════════════════════════════════════
# يُشغّل على VPS جديد لتجهيز كل شيء
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     OneAgent OS — VPS Setup                         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"

# ── 1. System Update ───────────────────────────────────────────────
echo -e "${CYAN}━━━ 1. System Update ─━━${NC}"
apt update && apt upgrade -y
echo -e "${GREEN}✓ System updated${NC}"

# ── 2. Install Docker ──────────────────────────────────────────────
echo -e "${CYAN}━━━ 2. Installing Docker ─━━${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${GREEN}✓ Docker already installed${NC}"
fi

# ── 3. Install Docker Compose ──────────────────────────────────────
echo -e "${CYAN}━━━ 3. Installing Docker Compose ─━━${NC}"
if ! command -v docker-compose-v2 &> /dev/null && ! docker compose version &> /dev/null; then
    apt install -y docker-compose-v2
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✓ Docker Compose already installed${NC}"
fi

# ── 4. Install Nginx ───────────────────────────────────────────────
echo -e "${CYAN}━━━ 4. Installing Nginx ─━━${NC}"
apt install -y nginx certbot python3-certbot-nginx
systemctl enable nginx
systemctl start nginx
echo -e "${GREEN}✓ Nginx + Certbot installed${NC}"

# ── 5. Install Monitoring Tools ────────────────────────────────────
echo -e "${CYAN}━━━ 5. Installing Monitoring Tools ─━━${NC}"
apt install -y htop net-tools ufw
echo -e "${GREEN}✓ Monitoring tools installed${NC}"

# ── 6. Configure Firewall ──────────────────────────────────────────
echo -e "${CYAN}━━━ 6. Configuring Firewall ─━━${NC}"
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw allow 8000/tcp    # API (optional, behind Nginx)
ufw --force enable
echo -e "${GREEN}✓ Firewall configured${NC}"

# ── 7. Clone Repository ────────────────────────────────────────────
echo -e "${CYAN}━━━ 7. Cloning Repository ─━━${NC}"
if [ ! -d /opt/oneagent ]; then
    git clone https://github.com/Bishoysamyaziz/Jnus.1 /opt/oneagent
    echo -e "${GREEN}✓ Repository cloned${NC}"
else
    echo -e "${YELLOW}⚠ Repository already exists, updating...${NC}"
    cd /opt/oneagent && git pull
fi

# ── 8. Create .env ─────────────────────────────────────────────────
echo -e "${CYAN}━━━ 8. Setting up .env ─━━${NC}"
if [ ! -f /opt/oneagent/.env ]; then
    cp /opt/oneagent/.env.example /opt/oneagent/.env
    echo -e "${YELLOW}⚠ Please edit /opt/oneagent/.env with your API keys${NC}"
    echo -e "${YELLOW}   nano /opt/oneagent/.env${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# ── 9. Start Services ──────────────────────────────────────────────
echo -e "${CYAN}━━━ 9. Starting Docker Services ─━━${NC}"
cd /opt/oneagent
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
echo -e "${GREEN}✓ Docker services started${NC}"

# ── 10. Verify ─────────────────────────────────────────────────────
echo -e "${CYAN}━━━ 10. Verification ─━━${NC}"
sleep 5
curl -f http://localhost:8000/health && echo -e "${GREEN}✓ API is healthy${NC}" || echo -e "${RED}✗ API health check failed${NC}"

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ VPS Setup Complete!                             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "API:      ${CYAN}http://$(curl -s ifconfig.me):8000${NC}"
echo -e "Health:   ${CYAN}http://$(curl -s ifconfig.me):8000/health${NC}"
echo -e "Docs:     ${CYAN}http://$(curl -s ifconfig.me):8000/docs${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Edit .env: ${CYAN}nano /opt/oneagent/.env${NC}"
echo -e "  2. Set up domain: ${CYAN}certbot --nginx -d api.yourdomain.com${NC}"
echo -e "  3. Update frontend API_URL and redeploy"
echo -e "  4. Monitor: ${CYAN}docker compose -f /opt/oneagent/docker-compose.yml logs -f${NC}"
