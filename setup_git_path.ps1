#!/usr/bin/env powershell
# PowerShell script to add Git to the system PATH permanently
# Run this script as Administrator to add Git to your PATH

Write-Host "🔧 Setting up Git in System PATH..." -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ This script must be run as Administrator to modify system PATH" -ForegroundColor Red
    Write-Host "Right-click on PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Git installation path
$gitPath = "C:\Program Files\Git\bin"

# Check if Git is installed
if (-not (Test-Path $gitPath)) {
    Write-Host "❌ Git not found at $gitPath" -ForegroundColor Red
    Write-Host "Please ensure Git is installed correctly" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Get current system PATH
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")

# Check if Git is already in PATH
if ($currentPath -like "*$gitPath*") {
    Write-Host "✅ Git is already in the system PATH" -ForegroundColor Green
} else {
    # Add Git to system PATH
    $newPath = $currentPath + ";" + $gitPath
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
    Write-Host "✅ Git added to system PATH successfully" -ForegroundColor Green
    Write-Host "You may need to restart your PowerShell/Command Prompt for changes to take effect" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🧪 Testing Git command..." -ForegroundColor Cyan
try {
    & git --version
    Write-Host "✅ Git is working correctly!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Git command may not be available until you restart your terminal" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Restart PowerShell or Command Prompt" -ForegroundColor White
Write-Host "2. Test with: git --version" -ForegroundColor White
Write-Host "3. Set up Git remote repository (GitHub, GitLab, etc.)" -ForegroundColor White
Write-Host "4. Push your repository: git remote add origin <remote-url>" -ForegroundColor White
Write-Host "5. Push to remote: git push -u origin master" -ForegroundColor White

Read-Host "Press Enter to continue"
