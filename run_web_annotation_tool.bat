@echo off
cd /d "%~dp0"
start "Web Annotator Server" /min python web_annotator_server.py 8765
timeout /t 1 /nobreak >nul
start "" http://127.0.0.1:8765
