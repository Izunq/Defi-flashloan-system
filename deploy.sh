#!/bin/bash

# V35 Deployment Script

# Check if .env file exists
if [ ! -f .env ]; then
  echo "Error: .env file not found. Please create it with the required environment variables."
  exit 1
fi

# Load environment variables
source .env

# Check required environment variables
if [ -z "$RPC_URL" ] || [ -z "$TRUST_CURVE_ADDRESS" ] || [ -z "$PROOF_EXECUTOR_ADDRESS" ] || [ -z "$API_KEY" ]; then
  echo "Error: Required environment variables are missing. Please check your .env file."
  exit 1
fi

echo "Starting V35 deployment..."

# Build and start the containers
echo "Building and starting containers..."
docker-compose build
docker-compose up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Check if services are running
echo "Checking if services are running..."
docker-compose ps

# Test the API
echo "Testing the API..."
cd backend
node test_api.js
cd ..

echo "Deployment completed successfully!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8080"
echo "Python Agent: http://localhost:5000"
echo "MongoDB: mongodb://localhost:27017"

echo "To stop the services, run: docker-compose down"