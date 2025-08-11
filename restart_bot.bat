@echo off
echo 🚀 Reiniciando Bot YouTube MP3 - Modo 24/7
echo ==========================================
echo.

echo ⏹️ Deteniendo todos los procesos de Python...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM python3.exe /T 2>nul
taskkill /F /IM python3.11.exe /T 2>nul

echo ⏳ Esperando a que los procesos se cierren...
timeout /t 3 >nul

echo Starting bot again in 24/7 mode...
echo.
call start_24h_bot.bat

echo.
echo ✅ Bot reiniciado exitosamente
echo ==========================================
