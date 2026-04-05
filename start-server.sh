#!/bin/bash
# PraisonAI Secured Server Launcher
# Listens for HTTP requests and activates agents on demand
#
# Usage:
#   ./start-server.sh              # Start on default port 8765
#   PORT=9000 ./start-server.sh    # Start on custom port

set -e
cd "$(dirname "$0")"

# Security environment
export PRAISONAI_TELEMETRY_DISABLED=true
export DO_NOT_TRACK=true

# Load .env if present
if [ -f .env ]; then
    set -a; source .env; set +a
fi

# Activate virtual environment
source .venv/bin/activate

PORT="${PORT:-8765}"

echo "=== PraisonAI Secured Server ==="
echo "  POST http://localhost:${PORT}/chat     — Send a message"
echo "  GET  http://localhost:${PORT}/health   — Health check"
echo "  GET  http://localhost:${PORT}/docs     — API docs"
echo ""
echo "Example:"
echo "  curl -X POST http://localhost:${PORT}/chat \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": \"Hello, what can you do?\"}'"
echo ""

exec python3 "$(dirname "$0")/server.py"
