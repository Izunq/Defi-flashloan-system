Write-Host "Updating combined project file with size optimization..." -ForegroundColor Cyan
Write-Host "Updated: June 17, 2025 - Now uses selective filtering to prevent large files" -ForegroundColor Yellow

# Change to project root directory
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

# Run the combine script with optimized settings (core source + docs, 35MB max)
node "tools\compilation\combine_files.cjs" --output "ALL_PROJECT_FILES.txt" --include-ext ".py,.js,.ts,.jsx,.tsx,.sol,.json,.yaml,.yml,.toml,.env,.md,.sh,.bat,.ps1,.html,.css" --max-total 35 --max-size 3

Write-Host "Done! File updated at $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Green

if (Test-Path "ALL_PROJECT_FILES.txt") {
    $fileInfo = Get-Item "ALL_PROJECT_FILES.txt"
    $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    Write-Host "Combined file location: $projectRoot\ALL_PROJECT_FILES.txt" -ForegroundColor Yellow
    Write-Host "File size: $sizeMB MB (optimized to stay under 35MB)" -ForegroundColor $(if ($sizeMB -lt 20) { "Green" } else { "Yellow" })
} else {
    Write-Host "Error: Combined file was not created." -ForegroundColor Red
}