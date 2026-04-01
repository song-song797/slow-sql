@echo off
setlocal
cd /d "%~dp0.."
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml up -d --build
