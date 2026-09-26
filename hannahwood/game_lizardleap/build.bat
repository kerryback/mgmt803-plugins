@echo off
rem Double-click to rebuild dist\LizardLeap.html and dist\LizardLeap.exe from game.py
cd /d "%~dp0"
python build.py
echo.
pause
