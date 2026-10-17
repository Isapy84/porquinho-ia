@echo off
chcp 65001 >nul
title Porquinho IA
cd /d "%~dp0"
echo ==================================================
echo         INICIANDO O PORQUINHO IA (TELEGRAM)
echo ==================================================
echo.
if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual .venv nao encontrado!
    pause
    exit /b 1
)
if not exist ".env" (
    echo [AVISO] Arquivo .env nao encontrado!
    echo Crie o arquivo .env com seu TELEGRAM_TOKEN e GEMINI_API_KEY.
    echo Veja o modelo em .env.example
    echo.
    pause
    exit /b 1
)
echo Executando bot.py... Pressione Ctrl+C para encerrar a qualquer momento.
echo.
".venv\Scripts\python.exe" bot.py
pause
