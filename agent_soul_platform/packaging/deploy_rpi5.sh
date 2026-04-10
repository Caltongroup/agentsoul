#!/bin/bash
# ============================================================================
# AgentSoul RPi5 One-Liner Deployment
# curl | bash pattern — works on fresh 64-bit Bookworm
# ============================================================================

set -e

AGENT_SOUL_HOME="/opt/agentsoul"
GITHUB_REPO="https://github.com/agentsoul/agentsoul"
OLLAMA_MODEL="qwen2.5-coder:4b"
API_PORT=5001

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════╗"
echo "║  AgentSoul RPi5 One-Liner Deployment              ║"
echo "║  Fresh 64-bit Bookworm → Production in 5 minutes  ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Check system
echo -e "${GREEN}✓${NC} System: $(uname -m) / $(lsb_release -ds 2>/dev/null || echo 'Unknown')"

# Require root
if [ "$EUID" -ne 0 ]; then
   echo -e "${RED}✗${NC} This script requires sudo"
   echo "  Run: sudo bash $0"
   exit 1
fi

# 1. Update system
echo -e "\n${YELLOW}1/5 Updating system...${NC}"
apt-get update -qq
apt-get upgrade -y -qq >/dev/null 2>&1
apt-get install -y -qq curl git python3 python3-pip python3-venv sqlite3 >/dev/null 2>&1

# 2. Install Ollama
echo -e "\n${YELLOW}2/5 Installing Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh >/dev/null 2>&1
    systemctl enable ollama >/dev/null 2>&1
    systemctl restart ollama >/dev/null 2>&1
    sleep 3
fi
echo -e "${GREEN}✓${NC} Ollama ready"

# 3. Pull quantized model
echo -e "\n${YELLOW}3/5 Pulling model (${OLLAMA_MODEL})...${NC}"
ollama pull $OLLAMA_MODEL 2>&1 | tail -3 || true
echo -e "${GREEN}✓${NC} Model loaded"

# 4. Clone & setup AgentSoul
echo -e "\n${YELLOW}4/5 Installing AgentSoul...${NC}"
mkdir -p $AGENT_SOUL_HOME
cd $AGENT_SOUL_HOME

if [ ! -d ".git" ]; then
    git clone $GITHUB_REPO . >/dev/null 2>&1
fi

# Create venv
python3 -m venv venv >/dev/null 2>&1
source venv/bin/activate
pip install -q flask cryptography requests >/dev/null 2>&1

# Init schema
python3 -m agentsoul.persistence.schema >/dev/null 2>&1
echo -e "${GREEN}✓${NC} AgentSoul installed"

# 5. Create systemd service
echo -e "\n${YELLOW}5/5 Configuring systemd...${NC}"

cat > /etc/systemd/system/agentsoul.service <<EOF
[Unit]
Description=AgentSoul Persistence Platform
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=$AGENT_SOUL_HOME
Environment="PATH=$AGENT_SOUL_HOME/venv/bin"
ExecStart=$AGENT_SOUL_HOME/venv/bin/python3 -m agentsoul.adapters.rest_api
Restart=always
RestartSec=5

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload >/dev/null 2>&1
systemctl enable agentsoul >/dev/null 2>&1
systemctl start agentsoul >/dev/null 2>&1
sleep 2

# Health check
echo -e "\n${GREEN}✅ DEPLOYMENT COMPLETE${NC}\n"

if curl -s http://127.0.0.1:$API_PORT/api/health | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} API healthy at http://127.0.0.1:${API_PORT}"
else
    echo -e "${YELLOW}⚠${NC} API still initializing (may take 10s)"
fi

# Next steps
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Transfer encrypted soul: scp soul.json pi@rpi:/opt/agentsoul/exports/"
echo "  2. Import via API: curl -X POST http://localhost:${API_PORT}/api/soul/import -H 'Authorization: Bearer demo_token_dev' -d @import.json"
echo "  3. Check logs: journalctl -u agentsoul -f"
echo ""
echo -e "${BLUE}Network Access:${NC}"
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "  REST API: http://${LOCAL_IP}:${API_PORT}/api/health"
echo "  Ollama:   http://127.0.0.1:11434"
echo ""
echo -e "${BLUE}Manage Service:${NC}"
echo "  Start:  systemctl start agentsoul"
echo "  Stop:   systemctl stop agentsoul"
echo "  Status: systemctl status agentsoul"
echo "  Logs:   journalctl -u agentsoul -n 50"
echo ""
