#!/bin/bash
# ERPClaw Web — server setup script
# Run on the server after cloning the repo to ~/erpclaw-web/
set -e

echo "=== ERPClaw Web Setup ==="

cd ~/erpclaw-web

# ── 1. Python venv + deps ───────────────────────────────────────────────────
echo "Setting up Python environment..."
cd api
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
cd ..

# ── 2. Node deps + build frontend ──────────────────────────────────────────
echo "Building frontend..."
npm install
npm run build

# ── 3. Install nginx config ─────────────────────────────────────────────────
echo "Installing nginx config..."
sudo cp deploy/nginx-erpclaw-web.conf /etc/nginx/sites-available/erpclaw-web
sudo ln -sf /etc/nginx/sites-available/erpclaw-web /etc/nginx/sites-enabled/erpclaw-web
sudo rm -f /etc/nginx/sites-enabled/webclaw
sudo nginx -t && sudo systemctl reload nginx

# ── 4. Install systemd service ──────────────────────────────────────────────
echo "Installing systemd service..."
sudo cp deploy/erpclaw-web-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable erpclaw-web-api
sudo systemctl restart erpclaw-web-api

echo ""
echo "=== Setup complete ==="
echo "  API:      systemctl status erpclaw-web-api"
echo "  Frontend: https://test1.erpclaw.ai"
echo "  Health:   curl http://127.0.0.1:8001/api/health"
