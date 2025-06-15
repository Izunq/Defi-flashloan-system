# V35 Backend Implementation

## Overview

This document outlines the backend implementation for the V35 upgrade of the Flashloan system. The backend consists of a Node.js Express server with WebSocket support and a Python agent for AI model integration.

## Components

### 1. Node.js Express Server

The Express server provides REST API endpoints and WebSocket connections for real-time updates. It interacts with the blockchain to fetch on-chain data and execute transactions.

#### Key Features:
- REST API for AI insights, ZK proofs, and strategy data
- WebSocket server for real-time updates
- Blockchain integration with ethers.js
- MongoDB integration for data persistence

#### API Endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/insights` | GET | Get latest AI insights |
| `/api/ai/strategy/:id` | GET | Get strategy by ID |
| `/api/ai/strategies` | GET | Get all strategies |
| `/api/ai/execute/:id` | POST | Execute a strategy |
| `/api/ai/metrics/:id` | GET | Get performance metrics for a strategy |
| `/api/zk/proofs` | GET | Get latest ZK proofs |
| `/api/zk/proof/:id` | GET | Get proof by strategy ID |
| `/api/zk/proof/hash/:hash` | GET | Get proof by hash |
| `/api/zk/verify` | POST | Verify a ZK proof |
| `/api/zk/submit` | POST | Submit a new ZK proof |
| `/api/zk/verifications/:id` | GET | Get verification history for a strategy |
| `/api/zk/submissions/:id` | GET | Get submission history for a strategy |
| `/api/strategy/:id` | GET | Get comprehensive strategy data |
| `/api/strategy/:id/history` | GET | Get execution history for a strategy |
| `/api/strategy/:id/performance` | GET | Get performance metrics for a strategy |
| `/api/strategy/:id/simulate` | POST | Simulate strategy execution |
| `/health` | GET | Health check endpoint |

#### WebSocket Channels:

| Channel | Description |
|---------|-------------|
| `ai_insights` | Real-time AI strategy insights |
| `zk_proofs` | ZK proof verification updates |
| `strategy_updates` | Strategy execution and performance updates |

### 2. Python Agent

The Python agent provides AI model integration and generates insights and ZK proofs for strategies.

#### Key Features:
- Flask API for AI model integration
- Mock data generation for development
- Blockchain integration with Web3.py

#### API Endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/insights` | GET | Get AI insights for strategies |
| `/api/proofs` | GET | Get ZK proofs for strategies |
| `/api/strategies` | GET | Get all strategies |
| `/api/strategy/:id` | GET | Get strategy by ID |
| `/api/proof/:id` | GET | Get proof by strategy ID |
| `/health` | GET | Health check endpoint |

## Setup and Configuration

### Environment Variables

#### Node.js Server:
```
PORT=8080
NODE_ENV=development
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=flashloan_v35
RPC_URL=http://localhost:8545
PRIVATE_KEY=0x0000000000000000000000000000000000000000000000000000000000000000
TRUST_CURVE_ADDRESS=0x0000000000000000000000000000000000000000
PROOF_EXECUTOR_ADDRESS=0x0000000000000000000000000000000000000000
API_KEY=your_api_key_here
PYTHON_AGENT_URL=http://localhost:5000
```

#### Python Agent:
```
PORT=5000
RPC_URL=http://localhost:8545
TRUST_CURVE_ADDRESS=0x0000000000000000000000000000000000000000
PROOF_EXECUTOR_ADDRESS=0x0000000000000000000000000000000000000000
API_KEY=your_api_key_here
```

### Installation

#### Node.js Server:
```bash
cd backend
npm install
npm start
```

#### Python Agent:
```bash
cd python_agent
pip install -r requirements.txt
python app.py
```

### Docker Deployment

The entire stack can be deployed using Docker Compose:

```bash
docker-compose up -d
```

## Testing

### API Testing

You can test the API endpoints using tools like Postman or curl:

```bash
# Get AI insights
curl http://localhost:8080/api/ai/insights

# Get ZK proofs
curl http://localhost:8080/api/zk/proofs

# Get strategy by ID
curl http://localhost:8080/api/strategy/1
```

### WebSocket Testing

You can test WebSocket connections using tools like wscat:

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket server
wscat -c ws://localhost:8080

# Subscribe to a channel
{"type":"subscribe","channel":"ai_insights"}
```

## Integration with Frontend

The frontend components connect to the backend using:

1. REST API calls for data fetching
2. WebSocket connections for real-time updates

The `useAIStrategyData` hook in the frontend handles these connections and provides data to the components.