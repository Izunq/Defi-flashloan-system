# Enhanced Cross-Chain Deployment with Security
# Deploys the enhanced cross-chain security system

Write-Host "Enhanced Cross-Chain Security Deployment" -ForegroundColor Green
Write-Host "=" * 50

# Deploy enhanced security contracts
Write-Host "Deploying Security Contracts..." -ForegroundColor Yellow
python deploy_cross_chain_security.py --network production

# Start security monitoring
Write-Host "Starting Security Monitoring..." -ForegroundColor Yellow
Start-Process -NoNewWindow python -ArgumentList "cross_chain_security_monitor.py --config production"

# Run security tests
Write-Host "Running Security Tests..." -ForegroundColor Yellow
python test_cross_chain_security.py --mode production

Write-Host "Enhanced Cross-Chain Security Deployment Complete!" -ForegroundColor Green
