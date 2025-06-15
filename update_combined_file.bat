@echo off
echo Updating combined project file...
node combine_files.cjs --output ALL_PROJECT_FILES.txt
echo Done! File updated at %time%