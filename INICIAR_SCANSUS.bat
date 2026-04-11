@echo off
chcp 65001 >nul
title ScanSUS v4 — Iniciando...
color 0A

echo.
echo  ================================================
echo    ScanSUS v4 - Digitalizador de Documentos
echo  ================================================
echo.

:: ── Limpa certificado antigo ────────
del "%TEMP%\scansus_cert.pem" >nul 2>&1
del "%TEMP%\scansus_key.pem"  >nul 2>&1
del "%TEMP%\scansus_ext.cnf"  >nul 2>&1

:: ── Verifica Python ──────────────────────────────
python --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON=python
    goto :tem_python
)

py --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON=py
    goto :tem_python
)

:: ── Python nao encontrado: baixar e instalar ─────
echo  [!] Python nao encontrado. Instalando automaticamente...
echo      (Isso acontece apenas uma vez)
echo.

set PYTHON_URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe
set PYTHON_INST=%TEMP%\python_scansus_install.exe

echo  Baixando Python...
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INST%' }"

if not exist "%PYTHON_INST%" (
    echo.
    echo  [ERRO] Nao foi possivel baixar o Python.
    echo  Instale manualmente em: https://python.org/downloads
    echo  Marque "Add Python to PATH" durante a instalacao!
    echo.
    pause
    exit /b 1
)

echo  Instalando Python...
"%PYTHON_INST%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del "%PYTHON_INST%" >nul 2>&1

for /f "delims=" %%i in ('powershell -Command "[System.Environment]::GetEnvironmentVariable(\"PATH\",\"User\")"') do set PATH=%%i;%PATH%

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Instalacao falhou. Reinicie e tente novamente.
    echo  Ou instale manualmente em: https://python.org/downloads
    echo.
    pause
    exit /b 1
)
set PYTHON=python
echo  Python instalado com sucesso!
echo.

:tem_python
echo  [OK] Python encontrado.
echo.
echo  Iniciando servidor HTTPS...
echo  O navegador abrira automaticamente.
echo.
echo  ================================================
echo   NAO FECHE ESTA JANELA enquanto usar o app!
echo   O link para CELULAR aparece abaixo do servidor.
echo  ================================================
echo.

%PYTHON% servidor.py

echo.
echo  [Servidor encerrado]
if %errorlevel% neq 0 (
    echo.
    echo  Verifique que estes 3 arquivos estao na mesma pasta:
    echo    - INICIAR_SCANSUS.bat
    echo    - servidor.py
    echo    - scanner-sus-v4.html
    echo.
    pause
)
