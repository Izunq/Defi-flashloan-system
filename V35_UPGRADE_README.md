# V35 Upgrade - ZK Proof-Aware Arbitrage System

## Overview

The V35 upgrade introduces a major advancement to our arbitrage system with ZK proof verification, dynamic capital allocation based on trust scores, and a fully integrated frontend dashboard. This document outlines the key components and integration points of the V35 system.

## Key Components

### 1. Smart Contracts

#### AIStrategyV35.sol
- ZK Proof integration with `submitZKProof()` and `verifyZKProof()` methods
- Dynamic risk parameter adjustment based on trust scores
- Performance metrics tracking with `getPerformanceMetrics()`
- Autonomous evolution through metadata updates and risk parameter adjustments

#### ProofAwareExecutorV35.sol
- Executes only verified strategies with proof-aware logic
- Enforces minimum trust score thresholds for capital allocation
- Tiered capital allocation based on strategy trust scores
- Built-in fee collection and protocol fee configuration

#### TrustCurve.sol
- Dynamic multiplier system with three tiers
- Adjusts capital allocation based on strategy's trust score
- Implements on-chain reputation to funding pipeline

### 2. Frontend Integration

#### LiveAIInsightsPanel.tsx
- Real-time AI strategy insights display
- On-chain performance metrics integration
- Strategy execution capabilities
- WebSocket/polling updates from Python agents

#### ZKProofVerifier.tsx
- ZK proof verification interface
- Historical proof tracking and display
- Detailed proof information with verification status
- Integration with on-chain verification

#### useAIStrategyData.ts Hook
- Centralized data management for AI strategies and ZK proofs
- WebSocket integration for real-time updates
- On-chain interaction for proof verification
- Performance metrics and risk parameter fetching

## Integration Points

### Frontend to Backend
- WebSocket connection for real-time AI insights and ZK proof updates
- REST API endpoints for historical data
- Python agent integration for AI model outputs

### Frontend to Blockchain
- Web3 integration for on-chain metrics and verification
- Trust score and performance data retrieval
- Strategy execution through ProofAwareExecutorV35

## Setup and Configuration

### Environment Variables
```
REACT_APP_TRUST_CURVE_ADDRESS=0x...
REACT_APP_PROOF_EXECUTOR_ADDRESS=0x...
REACT_APP_RPC_URL=https://...
REACT_APP_WS_ENDPOINT=wss://...
```

### WebSocket Channels
- `ai_insights`: Real-time AI strategy insights
- `zk_proofs`: ZK proof verification updates

## Deployment

Use the provided deployment utilities:
- `deploy_v35_contracts.py` for smart contract deployment
- `deploy_institutional_v35.py` for institutional-grade setup
- Docker configuration with `docker-compose.yml`

## Future Roadmap (V36-V41)

| Version | Title | Feature Highlights |
|---------|-------|-------------------|
| V36 | 🧭 Intent-Aware AI Kernel | Execute based on intent like "maximize Sharpe ratio" |
| V37 | 🔄 Autonomous Self-Rewriter | Agents rewrite strategy code based on performance |
| V38 | 🤝 Swarm Strategy Composers | Agents collaborate across chains to find opportunities |
| V39 | 🌀 RL Strategy Reincarnation | Strategies reborn from failed runs w/ modified params |
| V40 | 🧠 ZK-RL Verified Intelligence | Submit ZK-proofs of RL-trained strategies |
| V41 | 🔓 Public Proof Marketplace | Sell ZK-proven strategies to DAOs or users |