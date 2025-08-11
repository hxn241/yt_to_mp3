@echo off
setlocal enabledelayedexpansion

echo 🚀 Iniciando Bot YouTube MP3 - Modo 24/7
echo ==========================================

REM Verificar si el entorno virtual existe
if not exist ".venv\Scripts\Activate.ps1" (
    echo ❌ Error: Virtual environment no encontrado
    echo.
    echo Crea el entorno virtual primero con: uv venv
    pause
    exit /b 1
)

REM Verificar archivos requeridos
if not exist "bot_multiuser.py" (
    echo ❌ Error: bot_multiuser.py no encontrado
    pause
    exit /b 1
)

if not exist ".env" (
    echo ❌ Error: Archivo .env no encontrado
    echo.
    echo Crea un archivo .env con:
    echo TELEGRAM_BOT_TOKEN=tu_token_aqui
    pause
    exit /b 1
)

if not exist "pyproject.toml" (
    echo ❌ Error: pyproject.toml no encontrado
    echo Este archivo es requerido para el proyecto
    pause
    exit /b 1
)

REM Crear carpeta de logs si no existe
if not exist "logs" mkdir logs

echo ✅ Verificaciones completadas
echo.

:RESTART_LOOP
echo 🔄 %date% %time% - Iniciando bot...
echo %date% %time% - Iniciando bot >> logs\startup.log

REM Ejecutar el bot usando PowerShell con virtual environment
powershell -Command "& { .\.venv\Scripts\Activate.ps1; python bot_multiuser.py }"

REM Capturar código de salida
set EXIT_CODE=!ERRORLEVEL!

echo.
echo 🛑 %date% %time% - Bot detenido con código: !EXIT_CODE!
echo %date% %time% - Bot detenido con código: !EXIT_CODE! >> logs\startup.log

REM Si el código es 0, fue una salida normal
if !EXIT_CODE! equ 0 (
    echo ✅ Bot detenido normalmente
    goto END
)

REM Para cualquier otro código, reiniciar después de un delay
echo ⚠️ Bot se detuvo inesperadamente - Reiniciando en 10 segundos...
echo %date% %time% - Reinicio automático en 10 segundos >> logs\startup.log

timeout /t 10 >nul

goto RESTART_LOOP

:END
echo.
echo 👋 Bot terminado
pause
