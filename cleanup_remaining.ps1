#!/usr/bin/env pwsh

# Additional cleanup script for remaining files
Write-Host "Performing additional cleanup..." -ForegroundColor Green

# Function to move files safely
function Move-FilesSafely {
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

# Move remaining Python files to appropriate locations
$remainingAgentFiles = @(
    "arbitrage_exporter.py",
    "StrategySynthesizer.py"
)
Move-FilesSafely $remainingAgentFiles "src/agents/"

$remainingSecurityFiles = @(
    "emergency_action_executor.py",
    "emergency_private_key_remediation.py",
    "verify_access_control.py"
)
Move-FilesSafely $remainingSecurityFiles "src/security/"

$remainingCoreFiles = @(
    "cognitive_kernel_extension.py",
    "database_manager.py",
    "error_handler.py"
)
Move-FilesSafely $remainingCoreFiles "src/core/"

$remainingMonitoringFiles = @(
    "validate_alert_delivery.py"
)
Move-FilesSafely $remainingMonitoringFiles "src/monitoring/"

$remainingUtils = @(
    "enhanced_statistical_outlier_detector.py",
    "simplified_statistical_outlier_detector.py",
    "multi_chain_support.py",
    "ultra_fast_emergency_response.py"
)
Move-FilesSafely $remainingUtils "src/core/"

$sentinelFiles = @(
    "sentinel_contract_manager.py",
    "sentinel_coordinator.py",
    "sentinel_websocket_broadcaster.py",
    "strategy_sentinel.py"
)
Move-FilesSafely $sentinelFiles "src/monitoring/"

$strategyFiles = @(
    "strategy_simulation_engine.py"
)
Move-FilesSafely $strategyFiles "src/agents/"

$launchScripts = @(
    "launch_advanced_system.py",
    "launch_strategy_simulator.py",
    "launch_v34.bat",
    "launch_v34.ps1",
    "start_maximum_profits.py",
    "start_micro_bot.py",
    "start_sentinel_system.py"
)
Move-FilesSafely $launchScripts "scripts/"

$deploymentFiles = @(
    "enhanced_trusted_setup_deployment.py",
    "deploy_halal_only.js",
    "verify_and_deploy_zk.js",
    "phase3_integration.py",
    "prepare_sentinel_production.py"
)
Move-FilesSafely $deploymentFiles "scripts/deployment/"

$testFiles = @(
    "debug_path_traversal.py"
)
Move-FilesSafely $testFiles "tests/"

$optimizationFiles = @(
    "optimize_sentinel_performance.py"
)
Move-FilesSafely $optimizationFiles "tools/"

$backupFiles = @(
    "*.backup*",
    "deploy_halal_system.py.backup",
    "deploy_v36_v38_contracts.py.backup",
    "deploy_v42_contracts.py.backup",
    "deploy_vault.py.backup",
    "python_agent_v33_improved.py.backup"
)
New-Item -ItemType Directory -Path "backups/code" -Force
Move-FilesSafely $backupFiles "backups/code/"

$documentationFiles = @(
    "ALL_PROJECT_FILES.txt",
    "FULL_PROJECT_*.txt",
    "MASTER_PROJECT_COMPILATION.txt",
    "ULTIMATE_PROJECT_COMPILATION.txt",
    "frontend_files.txt",
    "project_structure.txt",
    "deployment_summary.txt"
)
Move-FilesSafely $documentationFiles "docs/"

$compileScripts = @(
    "compile_project.ps1",
    "execute_next_steps.ps1",
    "run_formal_verification.ps1",
    "run_sentinel_phase4.ps1",
    "run_tests.bat",
    "run_tests.ps1",
    "update_combined_file.bat",
    "update_combined_file.ps1"
)
Move-FilesSafely $compileScripts "scripts/"

$setupScripts = @(
    "init_git_repo.ps1",
    "init_git_repo.sh",
    "aws_setup_commands.sh"
)
Move-FilesSafely $setupScripts "scripts/deployment/"

$enterpriseFiles = @(
    "enterprise_features.py"
)
Move-FilesSafely $enterpriseFiles "src/compliance/"

$verificationFiles = @(
    "final_verification.py"
)
Move-FilesSafely $verificationFiles "tests/"

$untitledFiles = @(
    "untitled",
    "Untitled-*.py",
    "Untitled-*.java",
    "Untitled-*.js"
)
New-Item -ItemType Directory -Path "temp/untitled" -Force
Move-FilesSafely $untitledFiles "temp/untitled/"

$logFiles = @(
    "*.log",
    "*.db"
)
Move-FilesSafely $logFiles "logs/"

# Move Docker files to deployment
$dockerFiles = @(
    "Dockerfile*"
)
Move-FilesSafely $dockerFiles "scripts/deployment/"

Write-Host "Additional cleanup completed!" -ForegroundColor Green
