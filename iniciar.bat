@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Sistema de Transmissoes Universitarias

echo ================================================
echo   SISTEMA DE TRANSMISSOES UNIVERSITARIAS
echo ================================================
echo.

REM 1. Verifica se Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no sistema.
    echo Por favor, instale o Python antes de continuar.
    echo Download: https://www.python.org/downloads/
    echo IMPORTANTE: Marque "Add Python to PATH" na instalacao.
    pause
    exit
)

REM 2. Chama a funcao de verificacao de bibliotecas
echo Verificando dependencias...
call :verificar_bibliotecas

echo.
echo.
echo Iniciando Sistema de Transmissoes no Desktop...
echo.
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Ocorreu um erro ao executar o sistema.
    pause
)
exit

:verificar_bibliotecas
REM Verificacao rapida se as bibliotecas estao instaladas (Flet, Openpyxl, Docx, Pillow)
python -c "import importlib.util as i; r=['flet','openpyxl','docx','PIL']; m=[p for p in r if i.find_spec(p) is None]; exit(1 if m else 0)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Bibliotecas faltando. Instalando dependencias...
    python -m pip install -r requirements.txt
) else (
    echo [OK] Todas as dependencias ja estao instaladas.
)
goto :eof
