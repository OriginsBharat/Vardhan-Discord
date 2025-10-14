@echo off
REM This batch file will be responsible for starting the AI servers (Ollama, ComfyUI)
REM and the main Python bot application as background processes.
REM The final implementation will ensure these processes run silently.

ECHO Starting the world...
REM Placeholder for starting the main application
start python src/main.py
ECHO World startup initiated.