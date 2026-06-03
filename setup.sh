#!/bin/bash
# ============================================================================
#  CATIA V5 MCP Server - Setup Script
#  Run on Windows (Git Bash, WSL, or PowerShell with bash)
#
#  What this does:
#    1. Create virtual environment
#    2. Install dependencies (mcp, pywin32, pycatia, SSE, Streamable HTTP)
#    3. Verify installation
#
#  After setup, configure your MCP client (see README):
#    - Claude Desktop  → %APPDATA%\Claude\claude_desktop_config.json
#    - Claude Code     → claude mcp add catia-v5 python -- -m catia_mcp
#    - LM Studio       → python -m catia_mcp --sse
#    - Open WebUI      → python -m catia_mcp --streamable-http
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "=============================================="
echo "   CATIA V5 MCP Server - Setup"
echo "=============================================="
echo -e "${NC}"

# ── Step 1: Check OS ──
echo -e "${YELLOW}[1/4] Checking environment...${NC}"
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" && "$OSTYPE" != "win32" ]]; then
    if command -v cmd.exe &>/dev/null; then
        echo -e "${GREEN}  WSL detected - OK (CATIA and MCP server run on Windows host)${NC}"
    else
        echo -e "${RED}  WARNING: This MCP server requires Windows (COM automation).${NC}"
        echo -e "${RED}  You can install, but it will only run on Windows.${NC}"
        read -p "  Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${GREEN}  Windows detected - OK${NC}"
fi

# ── Step 2: Find Python ──
echo -e "${YELLOW}[2/4] Finding Python...${NC}"
PYTHON_CMD=""
for cmd in python python3 py; do
    if command -v $cmd &>/dev/null; then
        version=$($cmd --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [[ "$major" -ge 3 && "$minor" -ge 10 ]]; then
            PYTHON_CMD=$cmd
            echo -e "${GREEN}  Found $cmd ($($cmd --version))${NC}"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo -e "${RED}  Python 3.10+ not found!${NC}"
    echo -e "${RED}  Download: https://www.python.org/downloads/${NC}"
    echo -e "${RED}  Check 'Add Python to PATH' during install.${NC}"
    exit 1
fi

# ── Step 3: Create venv & install ──
echo -e "${YELLOW}[3/4] Setting up virtual environment...${NC}"

# Create venv
echo "  Creating .venv..."
$PYTHON_CMD -m venv .venv 2>/dev/null || true

# Activate and install
echo "  Installing dependencies..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate 2>/dev/null || . .venv/Scripts/activate
else
    source .venv/bin/activate 2>/dev/null || . .venv/bin/activate
fi

python -m pip install --upgrade pip setuptools wheel 2>/dev/null || true
python -m pip install -e ".[dev]" 2>/dev/null || true
echo -e "${GREEN}  Done${NC}"

# ── Step 4: Verify ──
echo -e "${YELLOW}[4/4] Verifying...${NC}"

if python -c "import mcp" 2>/dev/null; then
    echo -e "${GREEN}  mcp package ........... OK${NC}"
else
    echo -e "${RED}  mcp package ........... FAILED${NC}"
fi

if python -c "import catia_mcp" 2>/dev/null; then
    echo -e "${GREEN}  catia_mcp ............. OK${NC}"
else
    echo -e "${RED}  catia_mcp ............. FAILED${NC}"
fi

if python -c "import win32com" 2>/dev/null; then
    echo -e "${GREEN}  pywin32 (COM) ......... OK${NC}"
else
    echo -e "${YELLOW}  pywin32 (COM) ......... SKIPPED (requires Windows)${NC}"
fi

if python -c "import pycatia" 2>/dev/null; then
    echo -e "${GREEN}  pycatia ............... OK${NC}"
else
    echo -e "${YELLOW}  pycatia ............... SKIPPED (requires Windows)${NC}"
fi

if python -c "import sse_starlette" 2>/dev/null; then
    echo -e "${GREEN}  sse-starlette ......... OK${NC}"
else
    echo -e "${YELLOW}  sse-starlette ......... SKIPPED (optional - needed for SSE mode)${NC}"
fi

if python -c "import uvicorn" 2>/dev/null; then
    echo -e "${GREEN}  uvicorn ............... OK${NC}"
else
    echo -e "${YELLOW}  uvicorn ............... SKIPPED (optional - needed for HTTP modes)${NC}"
fi

echo ""
echo -e "${GREEN}=============================================="
echo "   Setup complete!"
echo "==============================================${NC}"
echo ""
echo -e "  ${CYAN}Next steps:${NC}"
echo "  1. Make sure CATIA V5 is running"
echo "  2. Configure your MCP client (see README):"
echo "     - Claude Desktop  → edit %APPDATA%\\Claude\\claude_desktop_config.json"
echo "     - Claude Code     → claude mcp add catia-v5 python -- -m catia_mcp"
echo "     - LM Studio       → python -m catia_mcp --sse"
echo "     - Open WebUI      → python -m catia_mcp --streamable-http"
echo ""
echo -e "  ${CYAN}Manual test:${NC}"
echo "  python -m catia_mcp"
echo ""
