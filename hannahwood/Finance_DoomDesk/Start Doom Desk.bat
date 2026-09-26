@echo off
title Doom Desk
cd /d "%~dp0"
python -c "import fastapi, uvicorn, anthropic, yfinance" 2>nul || (
    echo Installing requirements...
    python -m pip install -r requirements.txt
)
python doom_bot.py
if errorlevel 1 pause
