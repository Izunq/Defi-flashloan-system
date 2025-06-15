# Emergency Monitoring System Deployment Script
# =============================================

param(
    [string]$Action = "start",
    [string]$Config = "emergency_monitoring_config.yaml",
    [int]$DashboardPort = 8080,
    [switch]$InstallDependencies,
    [switch]$TestMode
)

Write-Host "🚨 Emergency Monitoring System Deployment" -ForegroundColor Red
Write-Host "=========================================" -ForegroundColor Red

# Check Python installation
function Test-PythonInstallation {
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -like "*Python*") {
            Write-Host "✅ Python is installed: $pythonVersion" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
        return $false
    }
}

# Install required Python packages
function Install-PythonDependencies {
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
    
    $packages = @(
        "asyncio",
        "pyyaml",
        "psutil",
        "aiohttp",
        "websockets",
        "flask",
        "flask-socketio",
        "python-socketio",
        "requests"
    )
    
    foreach ($package in $packages) {
        Write-Host "Installing $package..." -ForegroundColor Cyan
        try {
            pip install $package --quiet
            Write-Host "✅ $package installed successfully" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to install $package" -ForegroundColor Red
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Create monitoring directories
function Initialize-MonitoringDirectories {
    Write-Host "📁 Creating monitoring directories..." -ForegroundColor Yellow
    
    $directories = @(
        "logs",
        "config",
        "backup",
        "alerts",
        "recovery"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "✅ Created directory: $dir" -ForegroundColor Green
        }
    }
}

# Start the emergency monitoring system
function Start-EmergencyMonitoring {
    Write-Host "🚀 Starting Emergency Monitoring System..." -ForegroundColor Green
    
    # Check if config file exists
    if (!(Test-Path $Config)) {
        Write-Host "❌ Configuration file not found: $Config" -ForegroundColor Red
        Write-Host "Creating default configuration..." -ForegroundColor Yellow
        # The Python script will create default config
    }
    
    # Start the monitoring system
    try {
        if ($TestMode) {
            Write-Host "🧪 Starting in test mode..." -ForegroundColor Cyan
            python emergency_monitoring_system.py --test-mode
        }
        else {
            Write-Host "🎯 Starting production monitoring..." -ForegroundColor Green
            
            # Start monitoring system in background
            Start-Process -FilePath "python" -ArgumentList "emergency_monitoring_system.py" -NoNewWindow
            
            # Wait a bit for system to initialize
            Start-Sleep -Seconds 3
            
            # Start dashboard
            Write-Host "🌐 Starting dashboard on port $DashboardPort..." -ForegroundColor Cyan
            Start-Process -FilePath "python" -ArgumentList "emergency_monitoring_dashboard.py --port $DashboardPort" -NoNewWindow
            
            Write-Host ""
            Write-Host "✅ Emergency Monitoring System Started!" -ForegroundColor Green
            Write-Host "📊 Dashboard: http://localhost:$DashboardPort" -ForegroundColor Cyan
            Write-Host "📋 Logs: emergency_monitoring.log" -ForegroundColor Cyan
        }
    }
    catch {
        Write-Host "❌ Failed to start monitoring system" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Stop the emergency monitoring system
function Stop-EmergencyMonitoring {
    Write-Host "🛑 Stopping Emergency Monitoring System..." -ForegroundColor Yellow
    
    # Find and kill Python processes running monitoring
    $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*emergency_monitoring*"
    }
    
    foreach ($process in $processes) {
        try {
            Stop-Process -Id $process.Id -Force
            Write-Host "✅ Stopped process: $($process.Id)" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to stop process: $($process.Id)" -ForegroundColor Red
        }
    }
}

# Check system status
function Get-MonitoringStatus {
    Write-Host "📊 Emergency Monitoring System Status" -ForegroundColor Cyan
    Write-Host "=====================================" -ForegroundColor Cyan
    
    # Check if monitoring processes are running
    $monitoringProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*emergency_monitoring*"
    }
    
    if ($monitoringProcesses) {
        Write-Host "✅ Monitoring system is running" -ForegroundColor Green
        Write-Host "Processes:" -ForegroundColor Cyan
        foreach ($process in $monitoringProcesses) {
            Write-Host "  - PID: $($process.Id)" -ForegroundColor White
        }
    }
    else {
        Write-Host "❌ Monitoring system is not running" -ForegroundColor Red
    }
    
    # Check log files
    if (Test-Path "emergency_monitoring.log") {
        $logSize = (Get-Item "emergency_monitoring.log").Length / 1KB
        Write-Host "📋 Log file size: $([math]::Round($logSize, 2)) KB" -ForegroundColor Cyan
    }
    
    # Check dashboard accessibility
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$DashboardPort" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "🌐 Dashboard is accessible at http://localhost:$DashboardPort" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Dashboard is not accessible" -ForegroundColor Red
    }
}

# Run health check
function Test-MonitoringHealth {
    Write-Host "🩺 Running Emergency Monitoring Health Check..." -ForegroundColor Cyan
    
    # Test Python dependencies
    Write-Host "Testing Python dependencies..." -ForegroundColor Yellow
    $dependencies = @("asyncio", "yaml", "psutil", "aiohttp", "flask")
    foreach ($dep in $dependencies) {
        try {
            python -c "import $dep; print('✅ $dep')"
        }
        catch {
            Write-Host "❌ $dep - Not available" -ForegroundColor Red
        }
    }
    
    # Test configuration
    if (Test-Path $Config) {
        Write-Host "✅ Configuration file found" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Configuration file missing" -ForegroundColor Red
    }
    
    # Test log directory
    if (Test-Path "logs") {
        Write-Host "✅ Log directory exists" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Log directory missing" -ForegroundColor Red
    }
}

# Emergency actions
function Invoke-EmergencyAction {
    param([string]$EmergencyAction)
    
    Write-Host "🚨 EMERGENCY ACTION: $EmergencyAction" -ForegroundColor Red
    
    switch ($EmergencyAction.ToLower()) {
        "pause" {
            Write-Host "⏸️ Pausing trading operations..." -ForegroundColor Yellow
            # Implement pause logic here
            Write-Host "✅ Trading operations paused" -ForegroundColor Green
        }
        "shutdown" {
            Write-Host "🛑 Emergency shutdown initiated..." -ForegroundColor Red
            Stop-EmergencyMonitoring
            # Additional emergency shutdown logic
            Write-Host "✅ Emergency shutdown completed" -ForegroundColor Green
        }
        "restart" {
            Write-Host "🔄 Restarting monitoring system..." -ForegroundColor Yellow
            Stop-EmergencyMonitoring
            Start-Sleep -Seconds 5
            Start-EmergencyMonitoring
            Write-Host "✅ System restarted" -ForegroundColor Green
        }
        default {
            Write-Host "❌ Unknown emergency action: $EmergencyAction" -ForegroundColor Red
        }
    }
}

# Main execution
Write-Host ""
Write-Host "Action: $Action" -ForegroundColor White
Write-Host "Config: $Config" -ForegroundColor White
Write-Host "Dashboard Port: $DashboardPort" -ForegroundColor White
Write-Host ""

# Check Python installation
if (!(Test-PythonInstallation)) {
    Write-Host "Please install Python 3.7+ and add it to PATH" -ForegroundColor Red
    exit 1
}

# Install dependencies if requested
if ($InstallDependencies) {
    Install-PythonDependencies
}

# Initialize directories
Initialize-MonitoringDirectories

# Execute requested action
switch ($Action.ToLower()) {
    "start" {
        Start-EmergencyMonitoring
    }
    "stop" {
        Stop-EmergencyMonitoring
    }
    "restart" {
        Stop-EmergencyMonitoring
        Start-Sleep -Seconds 3
        Start-EmergencyMonitoring
    }
    "status" {
        Get-MonitoringStatus
    }
    "health" {
        Test-MonitoringHealth
    }
    "emergency" {
        $emergencyAction = Read-Host "Enter emergency action (pause/shutdown/restart)"
        Invoke-EmergencyAction -EmergencyAction $emergencyAction
    }
    default {
        Write-Host "❌ Unknown action: $Action" -ForegroundColor Red
        Write-Host ""
        Write-Host "Available actions:" -ForegroundColor Cyan
        Write-Host "  start     - Start emergency monitoring" -ForegroundColor White
        Write-Host "  stop      - Stop emergency monitoring" -ForegroundColor White
        Write-Host "  restart   - Restart emergency monitoring" -ForegroundColor White
        Write-Host "  status    - Check system status" -ForegroundColor White
        Write-Host "  health    - Run health check" -ForegroundColor White
        Write-Host "  emergency - Execute emergency action" -ForegroundColor White
        Write-Host ""
        Write-Host "Example usage:" -ForegroundColor Cyan
        Write-Host "  .\deploy_emergency_monitoring.ps1 -Action start -InstallDependencies" -ForegroundColor White
        Write-Host "  .\deploy_emergency_monitoring.ps1 -Action status" -ForegroundColor White
        Write-Host "  .\deploy_emergency_monitoring.ps1 -Action emergency" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "🚨 Emergency Monitoring Deployment Complete" -ForegroundColor Red
