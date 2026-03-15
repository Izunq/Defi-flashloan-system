#!/bin/bash

# Flash Loan Arbitrage System - Startup Script
# This script will start all necessary services for the dashboard

echo "🚀 Starting Flash Loan Arbitrage System..."
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null
}

# Function to kill process on port
kill_port() {
    if port_in_use $1; then
        echo -e "${YELLOW}Killing process on port $1${NC}"
        kill -9 $(lsof -ti:$1) 2>/dev/null || true
    fi
}

echo -e "${BLUE}Checking dependencies...${NC}"

# Check Node.js
if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 16+ first.${NC}"
    exit 1
fi

# Check npm
if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed. Please install npm first.${NC}"
    exit 1
fi

# Check Python
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8+ first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All dependencies found${NC}"

# Kill existing processes
echo -e "${BLUE}Cleaning up existing processes...${NC}"
kill_port 3000  # Frontend
kill_port 8080  # Backend
kill_port 5000  # Security Dashboard
kill_port 8501  # Streamlit

# Install frontend dependencies
echo -e "${BLUE}Installing frontend dependencies...${NC}"
if [ ! -d "node_modules" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
        exit 1
    fi
fi

# Install backend dependencies
echo -e "${BLUE}Installing backend dependencies...${NC}"
cd backend
if [ ! -d "node_modules" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install backend dependencies${NC}"
        exit 1
    fi
fi
cd ..

# Install server dependencies
echo -e "${BLUE}Installing server dependencies...${NC}"
cd server
if [ ! -d "node_modules" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install server dependencies${NC}"
        exit 1
    fi
fi
cd ..

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
fi

echo -e "${GREEN}✅ All dependencies installed${NC}"

# Start services
echo -e "${BLUE}Starting services...${NC}"

# Start backend API
echo -e "${YELLOW}Starting Backend API (Port 8080)...${NC}"
cd backend
npm start &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start API proxy server
echo -e "${YELLOW}Starting API Proxy Server (Port 3001)...${NC}"
cd server
PORT=3001 npm start &
SERVER_PID=$!
cd ..

# Wait a moment for server to start
sleep 2

# Start Streamlit dashboard
echo -e "${YELLOW}Starting Streamlit Dashboard (Port 8501)...${NC}"
if [ -f "streamlit_dashboard.py" ]; then
    python3 -m streamlit run streamlit_dashboard.py --server.port 8501 --server.headless true &
    STREAMLIT_PID=$!
fi

# Start frontend
echo -e "${YELLOW}Starting Frontend (Port 3000)...${NC}"
npm run dev &
FRONTEND_PID=$!

# Wait for services to start
echo -e "${BLUE}Waiting for services to initialize...${NC}"
sleep 5

# Check if services are running
echo -e "${BLUE}Checking service status...${NC}"

if port_in_use 3000; then
    echo -e "${GREEN}✅ Frontend running on http://localhost:3000${NC}"
else
    echo -e "${RED}❌ Frontend failed to start${NC}"
fi

if port_in_use 8080; then
    echo -e "${GREEN}✅ Backend API running on http://localhost:8080${NC}"
else
    echo -e "${RED}❌ Backend API failed to start${NC}"
fi

if port_in_use 3001; then
    echo -e "${GREEN}✅ API Proxy running on http://localhost:3001${NC}"
else
    echo -e "${RED}❌ API Proxy failed to start${NC}"
fi

if port_in_use 8501; then
    echo -e "${GREEN}✅ Streamlit Dashboard running on http://localhost:8501${NC}"
else
    echo -e "${YELLOW}⚠️ Streamlit Dashboard not started (optional)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Flash Loan Arbitrage System is running!${NC}"
echo "============================================="
echo -e "${BLUE}📊 Main Dashboard:    ${NC}http://localhost:3000"
echo -e "${BLUE}🔧 API Backend:       ${NC}http://localhost:8080"
echo -e "${BLUE}🛡️ API Proxy:         ${NC}http://localhost:3001"
echo -e "${BLUE}📈 Streamlit:         ${NC}http://localhost:8501"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    kill $FRONTEND_PID 2>/dev/null || true
    kill $BACKEND_PID 2>/dev/null || true
    kill $SERVER_PID 2>/dev/null || true
    kill $STREAMLIT_PID 2>/dev/null || true
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Set trap for cleanup
trap cleanup INT TERM

# Keep script running
wait
