#!/bin/bash
# ============================================================
#  AI Resume Screener — One-Click Startup
#  Usage:  bash run.sh
# ============================================================

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

echo -e "${BOLD}${BLUE}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║      AI Resume Screener Startup      ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── Check dependencies ────────────────────────────────────────
echo -e "${YELLOW}[1/4] Checking dependencies...${NC}"

command -v python3 &>/dev/null || { echo -e "${RED}Error: python3 not found${NC}"; exit 1; }
command -v node   &>/dev/null || { echo -e "${RED}Error: node not found${NC}"; exit 1; }
command -v mongod &>/dev/null || echo -e "${YELLOW}Warning: mongod not in PATH, make sure MongoDB is running${NC}"

echo -e "${GREEN}  Python: $(python3 --version)${NC}"
echo -e "${GREEN}  Node:   $(node --version)${NC}"

# ── Backend setup ─────────────────────────────────────────────
echo -e "\n${YELLOW}[2/4] Installing backend dependencies...${NC}"
cd backend
pip install -r requirements.txt -q
echo -e "${GREEN}  Backend dependencies ready.${NC}"

# ── Check / download ML model ─────────────────────────────────
echo -e "\n${YELLOW}[3/4] Checking ML model (all-MiniLM-L6-v2)...${NC}"
python3 -c "
from sentence_transformers import SentenceTransformer
import os
cache = os.path.expanduser('~/.cache/huggingface')
print('Downloading model if not cached...')
SentenceTransformer('all-MiniLM-L6-v2')
print('Model ready.')
"
echo -e "${GREEN}  ML model ready.${NC}"

# ── Start Flask backend ───────────────────────────────────────
echo -e "\n${YELLOW}[4/4] Starting services...${NC}"
echo -e "${GREEN}  Starting Flask backend on http://localhost:5000${NC}"
python3 app.py &
BACKEND_PID=$!
cd ..

# ── Start React frontend ──────────────────────────────────────
echo -e "${GREEN}  Starting React frontend on http://localhost:3000${NC}"
cd frontend
npm install -q 2>/dev/null
npm run dev &
FRONTEND_PID=$!
cd ..

# ── Summary ───────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║  Both services are running!              ║${NC}"
echo -e "${BOLD}${GREEN}║                                          ║${NC}"
echo -e "${BOLD}${GREEN}║  Frontend  →  http://localhost:3000      ║${NC}"
echo -e "${BOLD}${GREEN}║  Backend   →  http://localhost:5000      ║${NC}"
echo -e "${BOLD}${GREEN}║  API Docs  →  http://localhost:5000/api  ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both services.${NC}"

# ── Graceful shutdown on Ctrl+C ───────────────────────────────
trap "echo -e '\n${RED}Shutting down...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait
