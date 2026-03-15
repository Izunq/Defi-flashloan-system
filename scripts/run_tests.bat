@echo off
REM Flash Loan System - Simple Test Runner for Windows
REM This batch file provides quick access to common testing scenarios

echo.
echo ============================================================
echo                🧪 Flash Loan Test Runner 🧪
echo                     Quick Test Launcher
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Show menu if no arguments provided
if "%1"=="" goto :menu

REM Direct execution with arguments
if "%1"=="smoke" goto :smoke
if "%1"=="unit" goto :unit
if "%1"=="security" goto :security
if "%1"=="integration" goto :integration
if "%1"=="all" goto :all
if "%1"=="install" goto :install
if "%1"=="help" goto :help

echo ❌ Unknown command: %1
goto :help

:menu
echo Select test type to run:
echo.
echo 1. Smoke Tests (Quick validation)
echo 2. Unit Tests (Component testing)
echo 3. Security Tests (Vulnerability checks)
echo 4. Integration Tests (System interaction)
echo 5. All Tests (Complete suite)
echo 6. Install Dependencies
echo 7. Help
echo 8. Exit
echo.
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto :smoke
if "%choice%"=="2" goto :unit
if "%choice%"=="3" goto :security
if "%choice%"=="4" goto :integration
if "%choice%"=="5" goto :all
if "%choice%"=="6" goto :install
if "%choice%"=="7" goto :help
if "%choice%"=="8" goto :exit

echo ❌ Invalid choice. Please try again.
goto :menu

:smoke
echo ℹ️  Running Smoke Tests...
powershell -ExecutionPolicy Bypass -File "run_tests.ps1" -TestType smoke -Quick
goto :end

:unit
echo ℹ️  Running Unit Tests...
powershell -ExecutionPolicy Bypass -File "run_tests.ps1" -TestType unit -Coverage
goto :end

:security
echo ℹ️  Running Security Tests...
powershell -ExecutionPolicy Bypass -File "run_tests.ps1" -TestType security -Verbose
goto :end

:integration
echo ℹ️  Running Integration Tests...
powershell -ExecutionPolicy Bypass -File "run_tests.ps1" -TestType integration
goto :end

:all
echo ℹ️  Running All Tests...
powershell -ExecutionPolicy Bypass -File "run_tests.ps1" -TestType all -Coverage -Report
goto :end

:install
echo ℹ️  Installing Dependencies...
echo Installing core dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if exist requirements_test.txt (
    echo Installing test dependencies...
    python -m pip install -r requirements_test.txt
)
if exist requirements_fixed.txt (
    echo Installing fixed dependencies...
    python -m pip install -r requirements_fixed.txt
)
echo ✅ Dependencies installed successfully!
pause
goto :menu

:help
echo.
echo Flash Loan Test Runner - Help
echo =============================
echo.
echo This batch file provides easy access to the comprehensive test suite.
echo.
echo Direct Usage:
echo   run_tests.bat smoke        - Run quick smoke tests
echo   run_tests.bat unit         - Run unit tests with coverage
echo   run_tests.bat security     - Run security tests
echo   run_tests.bat integration  - Run integration tests
echo   run_tests.bat all          - Run complete test suite
echo   run_tests.bat install      - Install all dependencies
echo   run_tests.bat help         - Show this help
echo.
echo Interactive Usage:
echo   run_tests.bat              - Show interactive menu
echo.
echo Advanced Usage:
echo   For advanced options, use the PowerShell script directly:
echo   powershell -File run_tests.ps1 -TestType unit -Coverage -Parallel
echo.
echo Test Types:
echo   - smoke: Quick validation tests (~1-2 minutes)
echo   - unit: Component-level tests (~5-10 minutes)
echo   - security: Security and vulnerability tests (~10-15 minutes)
echo   - integration: End-to-end system tests (~15-30 minutes)
echo   - all: Complete test suite (~30-60 minutes)
echo.
echo Output:
echo   Test results are saved in the 'test_results' directory
echo   HTML reports are generated for easy viewing
echo   Coverage reports show code coverage statistics
echo.
pause
goto :menu

:end
echo.
echo Test execution completed.
if %ERRORLEVEL% EQU 0 (
    echo ✅ Tests completed successfully!
) else (
    echo ❌ Some tests failed. Check the reports for details.
)
echo.
echo 📁 Results location: test_results\
echo 🌐 HTML Report: test_results\report.html
if exist test_results\htmlcov\index.html (
    echo 📊 Coverage Report: test_results\htmlcov\index.html
)
echo.
pause

:exit
echo Goodbye! 👋
exit /b 0
