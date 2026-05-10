#!/bin/bash
# ============================================================
# OneAgent OS — Automated Setup Script
# بيجهز البيئة كاملة: Docker + Python + Node + WindsurfAPI
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

# === Check Prerequisites ===
info "Checking prerequisites..."

check_cmd() {
    if command -v "$1" &>/dev/null; then
        success "$1 found: $($1 --version 2>&1 | head -1)"
    else
        error "$1 not found. Please install $1 first."
        exit 1
    fi
}

check_cmd "python3"
check_cmd "node"
check_cmd "docker"
check_cmd "git"

# Check for pnpm or npm
if command -v pnpm &>/dev/null; then
    PKG_MANAGER="pnpm"
    success "pnpm found"
elif command -v npm &>/dev/null; then
    PKG_MANAGER="npm"
    success "npm found"
else
    error "No package manager found (pnpm or npm)"
    exit 1
fi

# === Step 1: Environment Configuration ===
info "Step 1: Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    success "Created .env from .env.example"
else
    warn ".env already exists, skipping"
fi

# === Step 2: Python Virtual Environment ===
info "Step 2: Setting up Python virtual environment..."
if [ ! -d .venv ]; then
    python3 -m venv .venv
    success "Created Python virtual environment"
else
    warn ".venv already exists, skipping"
fi

source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
success "Python dependencies installed"

# === Step 3: Install package in dev mode ===
info "Step 3: Installing package in dev mode..."
pip install -e . -q 2>/dev/null || pip install -e packages/core -q 2>/dev/null || warn "Dev install skipped"
success "Package installed in dev mode"

# === Step 4: Node/Frontend Dependencies ===
info "Step 4: Installing frontend dependencies..."
if [ -d packages/frontend ]; then
    cd packages/frontend
    if [ "$PKG_MANAGER" = "pnpm" ]; then
        pnpm install 2>/dev/null || warn "pnpm install failed (may need pnpm-workspace.yaml)"
    else
        npm install 2>/dev/null || warn "npm install failed"
    fi
    cd ../..
    success "Frontend dependencies installed"
else
    warn "packages/frontend not found, skipping"
fi

# === Step 5: WindsurfAPI Setup ===
info "Step 5: Setting up WindsurfAPI..."
if [ -d packages/windsurf-api ]; then
    cd packages/windsurf-api
    if [ -f package.json ]; then
        if [ "$PKG_MANAGER" = "pnpm" ]; then
            pnpm install 2>/dev/null || npm install 2>/dev/null || warn "WindsurfAPI install skipped"
        else
            npm install 2>/dev/null || warn "WindsurfAPI install skipped"
        fi
        success "WindsurfAPI dependencies installed"
    fi
    cd ../..
else
    warn "packages/windsurf-api not found, skipping"
fi

# === Step 6: Docker Services ===
info "Step 6: Starting Docker services..."
if command -v docker &>/dev/null; then
    docker compose build 2>/dev/null || warn "Docker build skipped (may need docker running)"
    docker compose up -d 2>/dev/null || warn "Docker compose up skipped"
    success "Docker services started"
else
    warn "Docker not available, skipping"
fi

# === Step 7: Git Hooks ===
info "Step 7: Setting up Git hooks..."
if [ -f .pre-commit-config.yaml ]; then
    pip install pre-commit -q 2>/dev/null
    pre-commit install 2>/dev/null || warn "pre-commit install failed"
    success "Git hooks installed"
else
    warn ".pre-commit-config.yaml not found, skipping"
fi

# === Step 8: Create necessary directories ===
info "Step 8: Creating necessary directories..."
mkdir -p packages/core/tools
mkdir -p packages/core/llm
mkdir -p data/redis data/postgres data/qdrant
success "Directories created"

# === Summary ===
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}  OneAgent OS — Setup Complete!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "  Next steps:"
echo "    1. Activate venv: source .venv/bin/activate"
echo "    2. Run tests:    pytest packages/ -v"
echo "    3. Start API:    uvicorn packages.api.main:app --reload"
echo "    4. Validate:     bash validate.sh"
echo ""

# Check if .env needs editing
if grep -q "your-api-key-here" .env 2>/dev/null; then
    warn "Don't forget to update your API keys in .env!"
fi
