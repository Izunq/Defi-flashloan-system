#!/usr/bin/env pwsh

# Project Organization Summary Script
Write-Host "=== PROJECT ORGANIZATION SUMMARY ===" -ForegroundColor Cyan
Write-Host ""

function Show-DirectoryContents {
    param(
        [string]$Path,
        [string]$Title,
        [int]$MaxFiles = 10
    )
    
    if (Test-Path $Path) {
        Write-Host "📁 $Title" -ForegroundColor Yellow
        $items = Get-ChildItem $Path -File | Select-Object -First $MaxFiles
        if ($items) {
            foreach ($item in $items) {
                Write-Host "   ├── $($item.Name)" -ForegroundColor Gray
            }
            $totalCount = (Get-ChildItem $Path -File).Count
            if ($totalCount -gt $MaxFiles) {
                Write-Host "   └── ... and $($totalCount - $MaxFiles) more files" -ForegroundColor DarkGray
            }
        } else {
            Write-Host "   └── (empty)" -ForegroundColor DarkGray
        }
        Write-Host ""
    }
}

Write-Host "New Project Structure:" -ForegroundColor Green
Write-Host ""

# Show organized directories
Show-DirectoryContents "src/core" "Core System Components" 8
Show-DirectoryContents "src/agents" "Trading Agents & Strategies" 8
Show-DirectoryContents "src/security" "Security Modules" 8
Show-DirectoryContents "src/monitoring" "Monitoring & Alerting" 8
Show-DirectoryContents "src/oracle" "Oracle Services" 5
Show-DirectoryContents "src/mev" "MEV Protection" 5
Show-DirectoryContents "src/validation" "Input Validation" 5
Show-DirectoryContents "src/cross_chain" "Cross-chain Functionality" 5
Show-DirectoryContents "src/zk" "Zero-Knowledge Proofs" 5
Show-DirectoryContents "src/compliance" "Compliance & Regulatory" 5
Show-DirectoryContents "contracts/solidity" "Smart Contracts" 5
Show-DirectoryContents "tests" "Test Suites" 8
Show-DirectoryContents "scripts/deployment" "Deployment Scripts" 8
Show-DirectoryContents "config" "Configuration Files" 8
Show-DirectoryContents "docs" "Documentation" 8
Show-DirectoryContents "logs" "Log Files" 5
Show-DirectoryContents "tools" "Development Tools" 5

# Count files in root directory
$rootFiles = Get-ChildItem . -File | Where-Object { $_.Name -notlike ".*" -and $_.Name -notlike "organize_project.ps1" -and $_.Name -notlike "cleanup_remaining.ps1" -and $_.Name -notlike "show_organization.ps1" }
Write-Host "📄 Root Directory Files (remaining): $($rootFiles.Count)" -ForegroundColor Magenta
foreach ($file in $rootFiles | Select-Object -First 10) {
    Write-Host "   ├── $($file.Name)" -ForegroundColor Gray
}
if ($rootFiles.Count -gt 10) {
    Write-Host "   └── ... and $($rootFiles.Count - 10) more files" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=== ORGANIZATION COMPLETE ===" -ForegroundColor Green
Write-Host ""
Write-Host "Benefits of the new structure:" -ForegroundColor Cyan
Write-Host "✅ Logical separation of concerns" -ForegroundColor Green
Write-Host "✅ Easier code navigation and maintenance" -ForegroundColor Green
Write-Host "✅ Clear testing and deployment workflows" -ForegroundColor Green
Write-Host "✅ Better scalability for future development" -ForegroundColor Green
Write-Host "✅ Improved documentation organization" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review the PROJECT_STRUCTURE.md file for detailed information" -ForegroundColor White
Write-Host "2. Update import statements in Python files if needed" -ForegroundColor White
Write-Host "3. Update configuration paths in config files" -ForegroundColor White
Write-Host "4. Test the system to ensure everything works correctly" -ForegroundColor White
Write-Host ""
