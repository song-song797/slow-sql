@echo off
setlocal
cd /d "%~dp0.."
powershell.exe -ExecutionPolicy Bypass -File ".\scripts\stop-all.ps1"
