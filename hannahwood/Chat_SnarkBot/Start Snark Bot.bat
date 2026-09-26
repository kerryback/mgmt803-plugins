@echo off
title Snark Bot
cd /d "%~dp0"
python -c "import fastapi, uvicorn, anthropic" 2>nul || (
    echo Installing requirements...
    python -m pip install -r requirements.txt
)
python chatbot.py
if errorlevel 1 pause
