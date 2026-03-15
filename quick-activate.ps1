#!/usr/bin/env pwsh
# 🚀 Quick System Activation Script
# Starts the arbitrage system components that are ready to run

Write-Host "🚀 ARTEMIS ARBITRAGE SYSTEM - QUICK ACTIVATION" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# Function to check if a port is available
function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

# Function to start monitoring stack with Docker
function Start-MonitoringStack {
    Write-Host "📊 Starting monitoring stack..." -ForegroundColor Yellow
    
    # Check if Docker is available
    try {
        docker --version | Out-Null
        Write-Host "✅ Docker is available" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker not found. Please install Docker Desktop" -ForegroundColor Red
        Write-Host "   Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        return $false
    }
    
    # Check if Docker daemon is running
    try {
        docker ps | Out-Null
        Write-Host "✅ Docker daemon is running" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker daemon not running. Please start Docker Desktop" -ForegroundColor Red
        return $false
    }
    
    # Start monitoring services
    Set-Location "config"
    try {
        docker-compose -f docker-compose.monitoring.yml up -d
        Start-Sleep 5
        
        # Check if services are running
        $prometheusRunning = Test-Port -Port 9090
        $grafanaRunning = Test-Port -Port 3001
        
        if ($prometheusRunning -and $grafanaRunning) {
            Write-Host "✅ Monitoring stack started successfully!" -ForegroundColor Green
            Write-Host "   📊 Grafana: http://localhost:3001 (admin/admin)" -ForegroundColor Cyan
            Write-Host "   📈 Prometheus: http://localhost:9090" -ForegroundColor Cyan
            return $true
        } else {
            Write-Host "⚠️  Some monitoring services may not be ready yet" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "❌ Failed to start monitoring stack" -ForegroundColor Red
        return $false
    } finally {
        Set-Location ".."
    }
}

# Function to check system status
function Get-SystemStatus {
    Write-Host "🔍 Checking system status..." -ForegroundColor Yellow
    
    $status = @{
        'Frontend (3000)' = Test-Port -Port 3000
        'Backend (8080)' = Test-Port -Port 8080
        'Artemis AI (8082)' = Test-Port -Port 8082
        'Prometheus (9090)' = Test-Port -Port 9090
        'Grafana (3001)' = Test-Port -Port 3001
    }
    
    Write-Host ""
    Write-Host "📊 SYSTEM STATUS:" -ForegroundColor Cyan
    Write-Host "=================" -ForegroundColor Cyan
    
    foreach ($service in $status.Keys) {
        $isRunning = $status[$service]
        $icon = if ($isRunning) { "✅" } else { "❌" }
        $color = if ($isRunning) { "Green" } else { "Red" }
        Write-Host "$icon $service" -ForegroundColor $color
    }
    
    Write-Host ""
}

# Function to start available services
function Start-AvailableServices {
    Write-Host "🚀 Starting available services..." -ForegroundColor Yellow
    
    # Start monitoring stack
    $monitoringStarted = Start-MonitoringStack
    
    # Start frontend if Node.js is available
    try {
        node --version | Out-Null
        Write-Host "🌐 Starting frontend..." -ForegroundColor Yellow
        Set-Location "frontend"
        Start-Process -FilePath "pwsh" -ArgumentList "-Command", "npm install && npm run dev" -WindowStyle Minimized
        Set-Location ".."
        Start-Sleep 3
        Write-Host "✅ Frontend starting..." -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Node.js not found - skipping frontend" -ForegroundColor Yellow
    }
    
    # Create a simple HTML dashboard if no services are running
    if (-not $monitoringStarted) {
        Create-SimpleDashboard
    }
}

# Function to create a simple HTML dashboard
function Create-SimpleDashboard {
    Write-Host "🎮 Creating simple dashboard..." -ForegroundColor Yellow
    
    $dashboardHtml = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artemis Arbitrage System - Control Panel</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .header h1 {
            font-size: 3em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .status-card h3 {
            margin-top: 0;
            color: #00ff88;
        }
        .service-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .service-item:last-child {
            border-bottom: none;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .status-online {
            background: #00ff88;
            box-shadow: 0 0 10px #00ff88;
        }
        .status-offline {
            background: #ff4444;
        }
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .action-btn {
            background: rgba(0, 255, 136, 0.2);
            border: 2px solid #00ff88;
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            text-decoration: none;
            text-align: center;
            transition: all 0.3s ease;
            font-weight: bold;
        }
        .action-btn:hover {
            background: rgba(0, 255, 136, 0.3);
            transform: translateY(-2px);
        }
        .logs {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 ARTEMIS</h1>
            <p>AI-Powered Arbitrage System Control Panel</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>🚀 System Services</h3>
                <div class="service-item">
                    <span>Artemis AI Core</span>
                    <span class="status-indicator status-offline" id="artemis-status"></span>
                </div>
                <div class="service-item">
                    <span>Data Ingestion</span>
                    <span class="status-indicator status-offline" id="data-status"></span>
                </div>
                <div class="service-item">
                    <span>Frontend Dashboard</span>
                    <span class="status-indicator status-offline" id="frontend-status"></span>
                </div>
                <div class="service-item">
                    <span>Monitoring Stack</span>
                    <span class="status-indicator status-offline" id="monitoring-status"></span>
                </div>
            </div>
            
            <div class="status-card">
                <h3>📊 Performance Metrics</h3>
                <div class="service-item">
                    <span>Total Trades</span>
                    <span>0</span>
                </div>
                <div class="service-item">
                    <span>Active Strategies</span>
                    <span>3</span>
                </div>
                <div class="service-item">
                    <span>Success Rate</span>
                    <span>--</span>
                </div>
                <div class="service-item">
                    <span>System Uptime</span>
                    <span id="uptime">00:00:00</span>
                </div>
            </div>
        </div>
        
        <div class="quick-actions">
            <a href="http://localhost:3001" class="action-btn" target="_blank">📊 Grafana Dashboard</a>
            <a href="http://localhost:9090" class="action-btn" target="_blank">📈 Prometheus Metrics</a>
            <a href="http://localhost:8082/docs" class="action-btn" target="_blank">🧠 Artemis API</a>
            <a href="http://localhost:3000" class="action-btn" target="_blank">🌐 Frontend</a>
        </div>
        
        <div class="logs">
            <div id="log-content">
                <div>🚀 System initialized</div>
                <div>📊 Monitoring stack starting...</div>
                <div>🔍 Checking service status...</div>
                <div>✅ Dashboard ready</div>
            </div>
        </div>
    </div>
    
    <script>
        // Simple service status checker
        function checkServices() {
            const services = [
                { id: 'artemis-status', port: 8082 },
                { id: 'data-status', port: 8080 },
                { id: 'frontend-status', port: 3000 },
                { id: 'monitoring-status', port: 9090 }
            ];
            
            services.forEach(service => {
                fetch(`http://localhost:${service.port}`)
                    .then(() => {
                        document.getElementById(service.id).className = 'status-indicator status-online';
                    })
                    .catch(() => {
                        document.getElementById(service.id).className = 'status-indicator status-offline';
                    });
            });
        }
        
        // Update uptime
        let startTime = Date.now();
        function updateUptime() {
            const uptime = Date.now() - startTime;
            const hours = Math.floor(uptime / 3600000);
            const minutes = Math.floor((uptime % 3600000) / 60000);
            const seconds = Math.floor((uptime % 60000) / 1000);
            document.getElementById('uptime').textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        // Auto-refresh
        setInterval(checkServices, 5000);
        setInterval(updateUptime, 1000);
        
        // Initial check
        checkServices();
        updateUptime();
    </script>
</body>
</html>
"@
    
    $dashboardHtml | Out-File -FilePath "dashboard.html" -Encoding UTF8
    
    # Open the dashboard in default browser
    Start-Process "dashboard.html"
    
    Write-Host "✅ Simple dashboard created and opened!" -ForegroundColor Green
    Write-Host "   📊 Dashboard: dashboard.html" -ForegroundColor Cyan
}

# Function to show quick start guide
function Show-QuickStartGuide {
    Write-Host ""
    Write-Host "📚 QUICK START GUIDE" -ForegroundColor Cyan
    Write-Host "====================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🔧 Prerequisites:" -ForegroundColor Yellow
    Write-Host "   1. Run setup-prerequisites.ps1 first" -ForegroundColor White
    Write-Host "   2. Configure .env file with your API keys" -ForegroundColor White
    Write-Host "   3. Ensure Docker Desktop is running" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 Next Steps:" -ForegroundColor Yellow
    Write-Host "   1. Copy .env.template to .env" -ForegroundColor White
    Write-Host "   2. Add your API keys to .env" -ForegroundColor White
    Write-Host "   3. Run deploy-full-system.ps1 for full deployment" -ForegroundColor White
    Write-Host ""
    Write-Host "🔗 Important Links:" -ForegroundColor Yellow
    Write-Host "   • Get Alchemy API key: https://alchemy.com" -ForegroundColor White
    Write-Host "   • Get Google AI key: https://makersuite.google.com/app/apikey" -ForegroundColor White
    Write-Host "   • Docker Desktop: https://docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host ""
}

# Main execution
function Main {
    Get-SystemStatus
    Start-AvailableServices
    Get-SystemStatus
    Show-QuickStartGuide
    
    Write-Host "🎉 QUICK ACTIVATION COMPLETE!" -ForegroundColor Green
    Write-Host "==============================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your Artemis system is now partially activated." -ForegroundColor White
    Write-Host "Complete the setup by configuring API keys and running the full deployment." -ForegroundColor White
}

# Execute main function
Main
