#!/bin/bash
# Sentinel Integration System Deployment Script
# This script deploys the Sentinel Integration System to a production environment

set -e  # Exit on error

# Configuration
DEPLOY_ENV=${1:-"production"}  # Default to production if not specified
CONFIG_DIR="./config"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./deploy_sentinel_$(date +%Y%m%d_%H%M%S).log"

# Create directories
mkdir -p $BACKUP_DIR
mkdir -p logs

# Start logging
exec > >(tee -a $LOG_FILE) 2>&1

echo "=== Sentinel Integration System Deployment ==="
echo "Environment: $DEPLOY_ENV"
echo "Started at: $(date)"
echo

# Function to load environment variables
load_env() {
    echo "Loading environment variables for $DEPLOY_ENV..."
    if [ -f ".env.$DEPLOY_ENV" ]; then
        export $(grep -v '^#' .env.$DEPLOY_ENV | xargs)
        echo "Environment variables loaded from .env.$DEPLOY_ENV"
    else
        echo "Warning: .env.$DEPLOY_ENV file not found, using default .env"
        export $(grep -v '^#' .env | xargs)
    fi
}

# Function to backup existing deployment
backup_existing() {
    echo "Backing up existing deployment..."
    
    # Backup configuration files
    if [ -d "$CONFIG_DIR" ]; then
        cp -r $CONFIG_DIR $BACKUP_DIR/
        echo "Configuration backed up to $BACKUP_DIR/config"
    fi
    
    # Backup database files
    if [ -f "sentinel_data.db" ]; then
        cp sentinel_data.db $BACKUP_DIR/
        echo "Database backed up to $BACKUP_DIR/sentinel_data.db"
    fi
    
    # Backup logs
    if [ -d "logs" ]; then
        cp -r logs $BACKUP_DIR/
        echo "Logs backed up to $BACKUP_DIR/logs"
    fi
    
    echo "Backup completed"
}

# Function to install dependencies
install_dependencies() {
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    
    echo "Installing frontend dependencies..."
    cd frontend
    npm install --production
    cd ..
    
    echo "Dependencies installed"
}

# Function to build frontend
build_frontend() {
    echo "Building frontend..."
    cd frontend
    npm run build
    cd ..
    echo "Frontend built"
}

# Function to configure the system
configure_system() {
    echo "Configuring system for $DEPLOY_ENV..."
    
    # Create config directory if it doesn't exist
    mkdir -p $CONFIG_DIR
    
    # Copy configuration templates
    cp sentinel_config.example.yaml $CONFIG_DIR/sentinel_config.yaml
    cp alert_routing_config.example.yaml $CONFIG_DIR/alert_routing_config.yaml
    
    # Replace environment variables in configuration files
    envsubst < $CONFIG_DIR/sentinel_config.yaml > $CONFIG_DIR/sentinel_config.yaml.tmp && mv $CONFIG_DIR/sentinel_config.yaml.tmp $CONFIG_DIR/sentinel_config.yaml
    envsubst < $CONFIG_DIR/alert_routing_config.yaml > $CONFIG_DIR/alert_routing_config.yaml.tmp && mv $CONFIG_DIR/alert_routing_config.yaml.tmp $CONFIG_DIR/alert_routing_config.yaml
    
    echo "System configured"
}

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    python scripts/migrate_database.py
    echo "Migrations completed"
}

# Function to run tests
run_tests() {
    echo "Running tests..."
    python sentinel_testing_framework.py --unit --integration
    
    if [ $? -ne 0 ]; then
        echo "Tests failed! Deployment aborted."
        exit 1
    fi
    
    echo "Tests passed"
}

# Function to deploy backend
deploy_backend() {
    echo "Deploying backend..."
    
    # Stop existing services
    if [ -f "sentinel.pid" ]; then
        echo "Stopping existing sentinel service..."
        kill -15 $(cat sentinel.pid) || true
        rm sentinel.pid
    fi
    
    # Start services
    echo "Starting sentinel coordinator..."
    nohup python start_sentinel_system.py > logs/sentinel.log 2>&1 &
    echo $! > sentinel.pid
    
    echo "Backend deployed"
}

# Function to deploy frontend
deploy_frontend() {
    echo "Deploying frontend..."
    
    # Copy built frontend to web server directory
    if [ -d "/var/www/sentinel" ]; then
        cp -r frontend/build/* /var/www/sentinel/
        echo "Frontend deployed to /var/www/sentinel/"
    else
        echo "Warning: Web server directory not found, skipping frontend deployment"
    fi
}

# Function to verify deployment
verify_deployment() {
    echo "Verifying deployment..."
    
    # Check if sentinel process is running
    if [ -f "sentinel.pid" ]; then
        if ps -p $(cat sentinel.pid) > /dev/null; then
            echo "Sentinel service is running"
        else
            echo "Error: Sentinel service is not running!"
            exit 1
        fi
    else
        echo "Error: Sentinel PID file not found!"
        exit 1
    fi
    
    # Check if API is responding
    if curl -s http://localhost:8081/health | grep -q "ok"; then
        echo "API health check passed"
    else
        echo "Warning: API health check failed"
    fi
    
    echo "Deployment verified"
}

# Main deployment flow
main() {
    echo "Starting deployment process..."
    
    load_env
    backup_existing
    install_dependencies
    build_frontend
    configure_system
    run_migrations
    run_tests
    deploy_backend
    deploy_frontend
    verify_deployment
    
    echo
    echo "=== Deployment Completed Successfully ==="
    echo "Completed at: $(date)"
    echo "Log file: $LOG_FILE"
}

# Run the deployment
main