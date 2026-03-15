#!/usr/bin/env pwsh

# Project Organization Script
# This script organizes the flashloan project into a clean directory structure

Write-Host "Starting project organization..." -ForegroundColor Green

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

# Core application files
$coreFiles = @(
    "main.py",
    "EconomicSingularity.py*",
    "MetamorphicCore.py*",
    "HumanAISymbiote.py*",
    "InterChainCognitiveMesh.py*",
    "ProtocolSynthesizer.py*",
    "WorldModelSimulator.py*",
    "CausalityEngine.py*"
)
Move-FilesSafely $coreFiles "src/core/"

# Agent files
$agentFiles = @(
    "*agent*.py",
    "INSTITUTIONAL_GRADE_V35.py",
    "PRODUCTION_ARBITRAGE_SYSTEM.py",
    "ULTIMATE_LAUNCHER.py",
    "MAXIMUM_PROFIT_ARBITRAGE_V2.py",
    "MICRO_CAPITAL_ARBITRAGE_V1.py",
    "enhanced_arbitrage_agent_v33.py",
    "distributed_enhanced_arbitrage_agent_v34.py",
    "python_agent_v*.py",
    "reincarnation_agent_v39.py",
    "swarm_intelligence_agent_v38.py",
    "strategy_generator_v37.py",
    "zk_rl_agent_v40.py"
)
Move-FilesSafely $agentFiles "src/agents/"

# Security files
$securityFiles = @(
    "*security*.py",
    "access_control_scanner.py",
    "advanced_threat_detection_engine.py",
    "ai_model_security.py",
    "emergency_security*.py",
    "final_security*.py",
    "secure_*.py",
    "cryptographic_input_validator.py"
)
Move-FilesSafely $securityFiles "src/security/"

# Monitoring files
$monitoringFiles = @(
    "*monitoring*.py",
    "*monitor*.py",
    "alert_*.py",
    "email_alert_manager.py",
    "slack_alert_manager.py",
    "sms_alert_manager.py",
    "webhook_alert_manager.py",
    "predictive_alerting_engine.py"
)
Move-FilesSafely $monitoringFiles "src/monitoring/"

# Oracle files
$oracleFiles = @(
    "*oracle*.py",
    "enhanced_multi_oracle_validator.py"
)
Move-FilesSafely $oracleFiles "src/oracle/"

# MEV protection files
$mevFiles = @(
    "*mev*.py",
    "MEV_SECURITY_SUMMARY.py"
)
Move-FilesSafely $mevFiles "src/mev/"

# Validation files
$validationFiles = @(
    "*validation*.py",
    "*validator*.py",
    "enhanced_input_validator.py",
    "ast_based_validator.py",
    "comprehensive_input_validation_fix.py",
    "emergency_input_sanitizer*.py"
)
Move-FilesSafely $validationFiles "src/validation/"

# Cross-chain files
$crossChainFiles = @(
    "*cross_chain*.py",
    "atomic_cross_chain_arbitrage.py",
    "universal_bridge_protocol.py"
)
Move-FilesSafely $crossChainFiles "src/cross_chain/"

# ZK proof files
$zkFiles = @(
    "*zk*.py",
    "zk_*.py"
)
Move-FilesSafely $zkFiles "src/zk/"

# Compliance files
$complianceFiles = @(
    "*compliance*.py",
    "*aml*.py",
    "*kyc*.py",
    "*halal*.py",
    "regulatory_reporting.py"
)
Move-FilesSafely $complianceFiles "src/compliance/"

# Test files
$testFiles = @(
    "test_*.py",
    "*test*.py",
    "conftest.py"
)
Move-FilesSafely $testFiles "tests/"

# Configuration files
$configFiles = @(
    "*.yaml",
    "*.yml",
    "*.json",
    "config_*.yaml"
)
Move-FilesSafely $configFiles "config/"

# Deployment scripts
$deploymentFiles = @(
    "deploy*.py",
    "deploy*.ps1",
    "deploy*.sh",
    "setup*.py",
    "setup*.ps1"
)
Move-FilesSafely $deploymentFiles "scripts/deployment/"

# Documentation files
$docFiles = @(
    "*.md",
    "README*"
)
Move-FilesSafely $docFiles "docs/"

# Log files
$logFiles = @(
    "*.log",
    "*_report_*.txt",
    "*_report_*.json"
)
Move-FilesSafely $logFiles "logs/"

# Contract files
$contractFiles = @(
    "*.sol"
)
Move-FilesSafely $contractFiles "contracts/solidity/"

# MATLAB files
$matlabFiles = @(
    "*.m",
    "matlab_*.py"
)
Move-FilesSafely $matlabFiles "matlab/"

# Dashboard files
$dashboardFiles = @(
    "*dashboard*.py",
    "streamlit_dashboard.py"
)
Move-FilesSafely $dashboardFiles "dashboard/"

# Tool files
$toolFiles = @(
    "folder2txt.*",
    "combine_files.*",
    "obsidian_mapper.py"
)
Move-FilesSafely $toolFiles "tools/"

Write-Host "Project organization completed!" -ForegroundColor Green
Write-Host "Please review the new structure and adjust as needed." -ForegroundColor Cyan
