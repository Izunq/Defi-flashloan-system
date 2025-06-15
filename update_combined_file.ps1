Write-Host "Updating combined project file..." -ForegroundColor Cyan
node combine_files.cjs --output ALL_PROJECT_FILES.txt
Write-Host "Done! File updated at $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Green