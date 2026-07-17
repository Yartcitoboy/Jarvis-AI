@echo off
title J.A.R.V.I.S.
echo Iniciando sistemas de J.A.R.V.I.S...
cd /d "%~dp0"
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Ocurrio un error al ejecutar Jarvis. Asegurate de tener instalados los requisitos.
    pause
)
