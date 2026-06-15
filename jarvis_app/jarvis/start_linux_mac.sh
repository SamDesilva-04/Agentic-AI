#!/bin/bash
echo ""
echo " ╔══════════════════════════════════════╗"
echo " ║   JARVIS — Local AI Desktop          ║"
echo " ╚══════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo " [ERROR] Python3 not found. Install from https://python.org"
    exit 1
fi

# Install deps if not done
if [ ! -f ".deps_installed" ]; then
    echo " Installing dependencies..."
    pip3 install -r requirements.txt --quiet
    touch .deps_installed
    echo " Done!"
fi

# Check Ollama
if curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo " Ollama is running!"
else
    echo " [WARN] Ollama not running. Run: ollama serve"
    echo " JARVIS will still work for offline tasks."
fi

echo ""
echo " Starting JARVIS at http://localhost:7777"
echo " Press Ctrl+C to stop."
echo ""
python3 app.py
