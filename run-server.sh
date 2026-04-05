#!/bin/bash
cd /Users/mohammadmushfiqurrahmanremans/Downloads/skills/PraisonAI
export PRAISONAI_TELEMETRY_DISABLED=true
export DO_NOT_TRACK=true
export PORT="${PORT:-8765}"
source .venv/bin/activate
exec python3 server.py
