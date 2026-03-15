#!/usr/bin/env pwsh

Write-Host "🔄 Updating combined project file with selective filtering..." -ForegroundColor Cyan
Write-Host "📝 Updated: June 17, 2025 - Optimized for manageable file sizes" -ForegroundColor Yellow

# Change to project root directory
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

Write-Host "📂 Working from: $projectRoot" -ForegroundColor Gray

# Create different selective combinations based on need
Write-Host "`n🎯 Choose what to include:" -ForegroundColor Green
Write-Host "1. Essential source code only (Python, JS, Solidity, configs)" -ForegroundColor White
Write-Host "2. Documentation and markdown files only" -ForegroundColor White  
Write-Host "3. Core source + key docs (recommended)" -ForegroundColor Yellow
Write-Host "4. Everything with size limits (50MB max)" -ForegroundColor White

$choice = Read-Host "Enter choice (1-4) or press Enter for option 3"

switch ($choice) {
    "1" {
        Write-Host "📋 Creating ESSENTIAL source code compilation..." -ForegroundColor Cyan
        node "tools\compilation\combine_files.cjs" --output "ALL_PROJECT_FILES.txt" --include-ext ".py,.js,.ts,.sol,.json,.yaml,.yml,.toml,.env" --max-total 25
    }
    "2" {
        Write-Host "📚 Creating DOCUMENTATION compilation..." -ForegroundColor Cyan
        node "tools\compilation\combine_files.cjs" --output "ALL_PROJECT_FILES.txt" --include-ext ".md,.txt,.rst" --max-total 20
    }
    "4" {
        Write-Host "🗂️ Creating FULL compilation with size limits..." -ForegroundColor Cyan
        node "tools\compilation\combine_files.cjs" --output "ALL_PROJECT_FILES.txt" --max-total 50 --max-size 5
    }
    default {
        Write-Host "🎯 Creating CORE source + docs compilation (recommended)..." -ForegroundColor Yellow
        node "tools\compilation\combine_files.cjs" --output "ALL_PROJECT_FILES.txt" --include-ext ".py,.js,.ts,.jsx,.tsx,.sol,.json,.yaml,.yml,.toml,.env,.md,.sh,.bat,.ps1,.html,.css" --max-total 35 --max-size 3
    }
}

Write-Host "`n✅ Done! File updated at $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Green

if (Test-Path "ALL_PROJECT_FILES.txt") {
    $fileInfo = Get-Item "ALL_PROJECT_FILES.txt"
    $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    
    Write-Host "📄 Combined file location: $projectRoot\ALL_PROJECT_FILES.txt" -ForegroundColor Yellow
    Write-Host "📊 File size: $sizeMB MB" -ForegroundColor $(if ($sizeMB -gt 50) { "Red" } elseif ($sizeMB -gt 20) { "Yellow" } else { "Green" })
    
    if ($sizeMB -gt 50) {
        Write-Host "⚠️  Warning: File is large. Consider using option 1 or 2 for smaller output." -ForegroundColor Red
    } elseif ($sizeMB -gt 20) {
        Write-Host "📈 File size is manageable for AI analysis." -ForegroundColor Yellow
    } else {
        Write-Host "🎯 Optimal file size for AI processing!" -ForegroundColor Green
    }
    
    $lineCount = (Get-Content "ALL_PROJECT_FILES.txt" | Measure-Object -Line).Lines
    Write-Host "📝 Total lines: $lineCount" -ForegroundColor Gray
} else {
    Write-Host "❌ Error: Combined file was not created." -ForegroundColor Red
}

Write-Host "`n💡 Tip: Use this selective approach to keep file sizes manageable!" -ForegroundColor Cyan
