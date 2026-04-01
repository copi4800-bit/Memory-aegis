#!/bin/bash
# Aegis v10: Universal One-Command Installer
set -e

echo "🛡️  Aegis v10: Initializing Infrastructure..."

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.11+."
    exit 1
fi

# 2. Check Virtual Environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment (.venv)..."
    python3 -m venv .venv
else
    echo "✅ Virtual environment detected."
fi

# 3. Install Dependencies
echo "🧪 Installing Python dependencies..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .

# 4. Initialize Database & Readiness Check
echo "🔍 Running final readiness audit..."
.venv/bin/python aegis_py/install_check.py

echo ""
echo "✨ Aegis v10 is READY!"
echo "--------------------------------------------------"
echo "To use with OpenClaw, ensure your config.json has:"
echo "--------------------------------------------------"
echo "  \"mcpServers\": {"
echo "    \"aegis\": {"
echo "      \"command\": \"$(pwd)/.venv/bin/python\","
echo "      \"args\": [\"$(pwd)/aegis_py/mcp/server.py\"],"
echo "      \"env\": { \"PYTHONPATH\": \"$(pwd)\" }"
echo "    }"
echo "  }"
echo "--------------------------------------------------"
