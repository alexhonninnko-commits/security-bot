@echo off
chcp 65001 > nul
title Discord Bot Launcher

echo ===================================================
echo               DISCORD BOT LAUNCHER
echo ===================================================
echo.

echo [1/2] Kontrola a instalace potrebych knihoven...
python -m pip install --upgrade pip > nul 2>&1
python -m pip install discord.py > nul 2>&1

echo.
echo [2/2] Spousteni Discord Bot Dashboards...
echo.

python bot.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CHYBA] Prace bota byla ukoncena s chybou.
)

echo.
pause