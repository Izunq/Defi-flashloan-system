# Flash Loan Project - Complete Project Compilation Update Script
# This script creates a comprehensive text file containing all project files

Write-Host "=== Flash Loan Project Compilation Update ===" -ForegroundColor Cyan
Write-Host "Starting complete project scan..." -ForegroundColor Yellow

# Record start time
$startTime = Get-Date

# Run the compilation script
try {
    & "tools\compilation\update_combined_file.ps1"
    
    # Calculate execution time
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    # Show results
    Write-Host "`n=== Compilation Complete ===" -ForegroundColor Green
    Write-Host "Execution time: $($duration.TotalSeconds.ToString('F2')) seconds" -ForegroundColor White
    
    # Show file info if it exists
    if (Test-Path "ALL_PROJECT_FILES.txt") {
        $fileInfo = Get-Item "ALL_PROJECT_FILES.txt"
        $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
        Write-Host "Generated file: ALL_PROJECT_FILES.txt" -ForegroundColor White
        Write-Host "File size: $fileSizeMB MB" -ForegroundColor White
        
        # Count lines (approximately)
        $lineCount = (Get-Content "ALL_PROJECT_FILES.txt" | Measure-Object -Line).Lines
        Write-Host "Total lines: $lineCount" -ForegroundColor White
    }
    
    Write-Host "`nThe complete project compilation is now available!" -ForegroundColor Green
    
} catch {
    Write-Host "Error during compilation: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
