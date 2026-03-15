@echo off
echo Updating combined project file...

REM Change to project root directory (two levels up from tools\compilation)
cd /d "%~dp0..\.."

REM Run the combine script from project root
node "tools\compilation\combine_files.cjs" --output "ALL_PROJECT_FILES.txt"

echo Done! File updated at %time%
echo Combined file location: %cd%\ALL_PROJECT_FILES.txt