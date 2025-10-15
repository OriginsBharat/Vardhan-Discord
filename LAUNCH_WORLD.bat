@echo off
title My AI World - Master Control
echo Starting all AI services...
echo This window will manage all background processes. Keep it open.

REM Set the model directory explicitly to avoid issues with the service running as a different user.
set OLLAMA_MODELS=%USERPROFILE%\.ollama\models

REM Start Ollama Server
echo Starting Ollama Server...
for /f "tokens=1,* delims==" %%a in ('findstr /b "OLLAMA_PATH" .env') do set OLLAMA_PATH=%%b
start "Ollama" cmd /c ""%OLLAMA_PATH%\ollama.exe" serve"

REM Start XTTS Server
echo Starting XTTSv2 Server...
for /f "tokens=1,* delims==" %%a in ('findstr /b "XTTS_PATH" .env') do set XTTS_PATH=%%b
start "XTTS" cmd /c "cd /d "%XTTS_PATH%" && python server.py"

REM Start ComfyUI Server
echo Starting ComfyUI Server...
for /f "tokens=1,* delims==" %%a in ('findstr /b "COMFYUI_PATH" .env') do set COMFYUI_PATH=%%b
start "ComfyUI" cmd /c "cd /d "%COMFYUI_PATH%" && python main.py --windows-standalone-build"

echo.
echo Waiting 20 seconds for services to initialize completely...
timeout /t 20

echo.
echo Starting My AI World Bot...
call "MyAIWorld\start_world.bat"

echo.
echo All processes launched. The bot should now be online in Discord.
pause