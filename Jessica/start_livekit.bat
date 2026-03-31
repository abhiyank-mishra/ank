@echo off
title Jessica LiveKit Agent
cd /d "%~dp0"
call ..\venv\Scripts\activate
echo.
echo =============================================
echo   JESSICA LiveKit Voice Agent
echo   Owner: Abhiyank
echo =============================================
echo.
echo Starting Jessica LiveKit Agent in DEV mode...
echo (Uses Gemini Realtime - speech to speech)
echo.
echo To test locally with mic/speaker: python livekit_agent.py console
echo To run in production mode:        python livekit_agent.py start
echo.
python livekit_agent.py dev
pause
