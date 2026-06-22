@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title SmartBathroom - Backend
set PYTHONIOENCODING=utf-8

cd /d "%~dp0\backend"

REM Cria o .env se ainda nao existir
if not exist ".env" (
    if exist ".env.example" (
        echo [SETUP] Criando .env a partir do exemplo...
        copy ".env.example" ".env" >nul
        echo [AVISO] Configure o .env antes de continuar se precisar de ngrok.
    )
)

REM Cria ambiente virtual se nao existir
if not exist "venv\" (
    echo [SETUP] Criando ambiente virtual Python...
    python -m venv venv
    if errorlevel 1 (
        echo [ERRO] Python nao encontrado. Instale em https://python.org
        pause
        exit /b 1
    )
)

REM Ativa o venv
call venv\Scripts\activate.bat

REM Instala dependencias
echo [SETUP] Verificando dependencias...
pip install -r requirements.txt -q --disable-pip-version-check

echo.
echo ============================================================
echo   SmartBathroom iniciando...
echo   Acesse: http://localhost:5000
echo   Login limpeza: limpeza.atitus / limpeza2026
echo   Cadastro aluno: http://localhost:5000/cadastro
echo ============================================================
echo.

python run.py

pause
