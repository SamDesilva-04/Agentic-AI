@echo off
title JARVIS — Local AI Assistant
color 0A
echo.
echo  ╔══════════════════════════════════════╗
echo  ║   JARVIS — Local AI Desktop          ║
echo  ╚══════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)

:: Install deps if needed
if not exist ".deps_installed" (
    echo  Installing dependencies...
    pip install -r requirements.txt --quiet
    echo installed > .deps_installed
    echo  Done!
)

:: Check if Ollama is running
echo  Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo  [WARN] Ollama not running. Start it with: ollama serve
    echo  JARVIS will still work for offline tasks.
) else (
    echo  Ollama is running!
)

echo.
echo  Starting JARVIS at http://localhost:7777
echo  Press Ctrl+C to stop.
echo.
python app.py
pause
