@echo off
REM =================================================================================================
REM LAUNCHER FOR ADVANCED FLASH LOAN ARBITRAGE SYSTEM - V34
REM =================================================================================================

echo ================================================================================
echo ADVANCED FLASH LOAN ARBITRAGE SYSTEM - V34 (LIVE PROVING & HARDENED AGENT)
echo ================================================================================

REM Parse command line arguments
set MODE=institutional
set SETUP_ONLY=0

:parse_args
if "%~1"=="" goto :end_parse_args
if /i "%~1"=="--mode" (
    set MODE=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--setup-only" (
    set SETUP_ONLY=1
    shift
    goto :parse_args
)
shift
goto :parse_args

:end_parse_args

echo Mode: %MODE%
echo ================================================================================

REM Run the launcher script
python launch_v34_agent.py --mode %MODE% %SETUP_ONLY% && (
    echo.
    echo ✅ Agent launched successfully
) || (
    echo.
    echo ❌ Failed to launch agent
)

if %SETUP_ONLY%==1 (
    echo.
    echo Setup completed. Agent not launched.
)

echo.
pause