@echo off
echo 🧹 Cleaning large dependency directories...
echo.

echo Removing node_modules...
if exist node_modules (
    rmdir /s /q node_modules
    echo ✅ node_modules removed (205 MB freed)
) else (
    echo ❌ node_modules not found
)

echo.
echo Removing Python virtual environment...
cd artemis_core
if exist Lib (
    rmdir /s /q Lib
    echo ✅ Python Lib removed (158 MB freed)
) else (
    echo ❌ Python Lib not found
)

if exist Scripts (
    rmdir /s /q Scripts
    echo ✅ Python Scripts removed
) else (
    echo ❌ Python Scripts not found
)

if exist pyvenv.cfg (
    del pyvenv.cfg
    echo ✅ Python config removed
)

cd ..

echo.
echo Removing cache files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo ✅ Python cache files removed

echo.
echo 🎉 Cleanup complete! 
echo Project size reduced by ~360 MB
echo.
echo To restore:
echo 1. npm install (for frontend)
echo 2. cd artemis_core && pip install -r requirements.txt (for backend)
echo.
pause
