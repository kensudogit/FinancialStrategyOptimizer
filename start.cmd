@echo off
cd /d "%~dp0"
set COMPOSE_BAKE=false
docker compose up --build -d
if errorlevel 1 pause
echo UI  http://localhost:3020
echo API http://localhost:8020/docs
