@echo off
setlocal
cd /d "%~dp0.."
powershell.exe -ExecutionPolicy Bypass -File ".\scripts\restart-all.ps1"
