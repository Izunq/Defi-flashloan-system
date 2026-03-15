#!/usr/bin/env pwsh

# Documentation Organization Script
Write-Host "Organizing documentation files..." -ForegroundColor Green

# Change to docs directory
cd docs

# Function to move files safely
function Move-DocFiles {
    param(
        [string[]]$Files,
        [string]$Destination
    )
    
    foreach ($file in $Files) {
        if (Test-Path $file) {
            Write-Host "Moving $file to $Destination" -ForegroundColor Yellow
            try {
                Move-Item $file $Destination -Force
            } catch {
                Write-Host "Error moving $file`: $_" -ForegroundColor Red
            }
        }
    }
}

# Security Reports
Write-Host "📁 Organizing Security Reports..." -ForegroundColor Cyan
$securityReports = @(
    "ACCESS_CONTROL_*.md",
    "CRITICAL_*SECURITY*.md",
    "COMPREHENSIVE_SECURITY_AUDIT_REPORT.md",
    "COMPREHENSIVE_SYSTEM_AUDIT_REPORT.md",
    "EMERGENCY_SECURITY_ACTION_PLAN.md",
    "FLASH_LOAN_*SECURITY*.md",
    "FLASH_LOAN_REENTRANCY*.md",
    "GAS_GRIEFING_VULNERABILITIES*.md",
    "ORACLE_MANIPULATION_*.md",
    "ORACLE_SECURITY_*.md",
    "SECURITY_*.md",
    "ZK_CIRCUIT_SECURITY*.md",
    "FINAL_*SECURITY*.md"
)
Move-DocFiles $securityReports "reports/security/"

# Deployment Reports
Write-Host "📁 Organizing Deployment Reports..." -ForegroundColor Cyan
$deploymentReports = @(
    "AWS_DEPLOYMENT_*.md",
    "ENHANCED_MEV_PROTECTION_DEPLOYMENT*.md",
    "MEV_PROTECTION_DEPLOYMENT*.md",
    "emergency_deployment_report*.md",
    "deployment_summary.txt",
    "GIT_REPOSITORY_SETUP*.md",
    "PHASE*_*.md"
)
Move-DocFiles $deploymentReports "reports/deployment/"

# Implementation Reports
Write-Host "📁 Organizing Implementation Reports..." -ForegroundColor Cyan
$implementationReports = @(
    "*IMPLEMENTATION*.md",
    "*COMPLETION_REPORT*.md",
    "DISTRIBUTED_AGENT_*.md",
    "ENHANCED_CROSS_CHAIN_*.md",
    "CROSS_CHAIN_SECURITY_*.md",
    "INPUT_VALIDATION_*.md",
    "OPTIMIZATION_*.md",
    "REENTRANCY_FIX*.md"
)
Move-DocFiles $implementationReports "reports/implementation/"

# Roadmaps and Planning
Write-Host "📁 Organizing Roadmaps..." -ForegroundColor Cyan
$roadmaps = @(
    "*ROADMAP*.md",
    "COMPREHENSIVE_ROADMAP*.md",
    "ADVANCED_RESEARCH_ANALYTICS*.md",
    "CLEANUP_PLAN.md",
    "NEXT_*STEPS*.md",
    "IMMEDIATE_*.md",
    "PATH_TO_MILLIONS*.md"
)
Move-DocFiles $roadmaps "roadmaps/"

# Feature Documentation
Write-Host "📁 Organizing Feature Documentation..." -ForegroundColor Cyan
$features = @(
    "HALAL_*.md",
    "ENTERPRISE_FEATURES*.md",
    "INSTITUTIONAL_*.md",
    "MICRO_*.md",
    "ZK_PROOF_SYSTEM*.md",
    "ORACLE_TESTING*.md",
    "SENTINEL_*.md",
    "V34_*.md",
    "V35_*.md",
    "V42_*.md",
    "V43_*.md"
)
Move-DocFiles $features "features/"

# Integration Guides
Write-Host "📁 Organizing Integration Guides..." -ForegroundColor Cyan
$integrations = @(
    "MATLAB_*.md",
    "AWS_CLOUD_*.md",
    "SPSS_*.md",
    "NVIVO_*.md",
    "TOOL_INTEGRATION*.md",
    "AMOS_*.md",
    "DATAINGESTION_*.md",
    "UNIVERSITY_STUDENT_AWS*.md"
)
Move-DocFiles $integrations "integrations/"

# Guides and Documentation
Write-Host "📁 Organizing Guides..." -ForegroundColor Cyan
$guides = @(
    "*GUIDE*.md",
    "*README*.md",
    "INSTALLATION_GUIDE.md",
    "TESTING_GUIDE.md",
    "QUICK_START*.md",
    "LOCAL_PROFESSIONAL_SUITE*.md",
    "BACKEND_*.md",
    "Process*.md"
)
Move-DocFiles $guides "guides/"

# Critical Alerts
Write-Host "📁 Organizing Critical Alerts..." -ForegroundColor Cyan
$alerts = @(
    "CRITICAL_*.md",
    "EMERGENCY_*.md",
    "*ALERT*.md"
)
Move-DocFiles $alerts "alerts/"

# Version Documentation
Write-Host "📁 Organizing Version Documentation..." -ForegroundColor Cyan
$versions = @(
    "V[0-9]*_*.md"
)
Move-DocFiles $versions "versions/"

# Miscellaneous files
Write-Host "📁 Organizing Miscellaneous Files..." -ForegroundColor Cyan
$misc = @(
    "1.md",
    "ATLAS.md.md",
    "frontend_files.txt",
    "project_structure.txt",
    "EARNINGS_POTENTIAL_ANALYSIS.md"
)
Move-DocFiles $misc "guides/"

Write-Host ""
Write-Host "✅ Documentation organization completed!" -ForegroundColor Green
Write-Host ""

# Show the new structure
Write-Host "📊 New Documentation Structure:" -ForegroundColor Cyan
Get-ChildItem -Directory | ForEach-Object {
    $count = (Get-ChildItem $_.FullName -File -Recurse).Count
    Write-Host "   📁 $($_.Name) - $count files" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📄 Root level files remaining:" -ForegroundColor Magenta
Get-ChildItem -File | ForEach-Object {
    Write-Host "   📄 $($_.Name)" -ForegroundColor Gray
}
