@echo off
title Flash Loan Project - Complete Compilation Update

echo ==========================================
echo Flash Loan Project Compilation Update
echo ==========================================
echo.

echo Starting complete project scan...
echo.

REM Run the PowerShell script
powershell -ExecutionPolicy Bypass -File "update_project_compilation.ps1"

REM Pause so user can see results
pause
