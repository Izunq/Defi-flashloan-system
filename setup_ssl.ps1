# SSL Certificate Setup Script for Windows
# This script sets up SSL certificates using Let's Encrypt for secure HTTPS connections

# Parameters
param (
    [Parameter(Mandatory=$true)]
    [string]$Domain,
    
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$false)]
    [switch]$Staging = $false
)

Write-Host "Setting up SSL certificates for $Domain..." -ForegroundColor Green

# Create directories for certificates
$CertPath = "./ssl"
if (-not (Test-Path $CertPath)) {
    New-Item -ItemType Directory -Path $CertPath | Out-Null
    Write-Host "Created directory: $CertPath" -ForegroundColor Cyan
}

# Check if Docker is installed
try {
    docker --version | Out-Null
} catch {
    Write-Error "Docker is not installed or not in PATH. Please install Docker first."
    exit 1
}

# Set up staging flag for testing
$StagingFlag = ""
if ($Staging) {
    $StagingFlag = "--staging"
    Write-Host "Using staging environment for testing" -ForegroundColor Yellow
}

# Run Certbot in Docker to obtain certificates
Write-Host "Obtaining SSL certificates from Let's Encrypt..." -ForegroundColor Cyan
docker run -it --rm `
    -v ${PWD}/ssl:/etc/letsencrypt `
    -v ${PWD}/ssl:/var/lib/letsencrypt `
    certbot/certbot certonly `
    --standalone `
    -d $Domain `
    --email $Email `
    --agree-tos `
    --no-eff-email `
    $StagingFlag

# Check if certificates were obtained successfully
if (Test-Path "$CertPath/live/$Domain/fullchain.pem" -and Test-Path "$CertPath/live/$Domain/privkey.pem") {
    Write-Host "SSL certificates obtained successfully!" -ForegroundColor Green
    
    # Update Nginx configuration (if using Nginx)
    Write-Host "Updating Nginx configuration..." -ForegroundColor Cyan
    
    # Create Nginx configuration template
    $NginxConfig = @"
server {
    listen 80;
    server_name $Domain;
    return 301 https://`$host`$request_uri;
}

server {
    listen 443 ssl;
    server_name $Domain;

    ssl_certificate /etc/letsencrypt/live/$Domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$Domain/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
    }
    
    # Backend API
    location /api {
        proxy_pass http://backend:8080;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://backend:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade `$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
    }
}
"@

    # Save Nginx configuration
    $NginxConfig | Out-File -FilePath "$CertPath/nginx-$Domain.conf" -Encoding utf8
    Write-Host "Nginx configuration saved to $CertPath/nginx-$Domain.conf" -ForegroundColor Cyan
    
    # Create renewal script
    $RenewalScript = @"
# SSL Certificate Renewal Script
# Run this script periodically (e.g., monthly) to renew certificates

docker run -it --rm `
    -v ${PWD}/ssl:/etc/letsencrypt `
    -v ${PWD}/ssl:/var/lib/letsencrypt `
    certbot/certbot renew

# Restart Nginx after renewal
docker-compose restart nginx
"@

    $RenewalScript | Out-File -FilePath "renew_ssl.ps1" -Encoding utf8
    Write-Host "SSL renewal script created: renew_ssl.ps1" -ForegroundColor Cyan
    
    Write-Host "SSL setup completed successfully!" -ForegroundColor Green
    Write-Host "To use these certificates with your application:" -ForegroundColor Yellow
    Write-Host "1. Update your docker-compose.yml to include the Nginx service" -ForegroundColor Yellow
    Write-Host "2. Mount the certificate directory to your Nginx container" -ForegroundColor Yellow
    Write-Host "3. Use the generated Nginx configuration" -ForegroundColor Yellow
    Write-Host "4. Set up a scheduled task to run renew_ssl.ps1 monthly" -ForegroundColor Yellow
} else {
    Write-Error "Failed to obtain SSL certificates. Check the error messages above."
    exit 1
}