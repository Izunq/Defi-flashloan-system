# Phase 2: Integration Framework

This document provides instructions for setting up and running the Phase 2 Integration Framework for the Flashloan Arbitrage System.

## Overview

Phase 2 builds on the security foundations established in Phase 1 by implementing:

1. **Event Bus Architecture**: A Redis-based pub/sub system for component communication
2. **Processing Pipeline**: A Celery-based pipeline for processing arbitrage opportunities
3. **Transaction Manager**: A secure interface to the blockchain
4. **Unified Monitoring System**: Real-time monitoring of system status and events

## Prerequisites

- Python 3.8+
- Redis server
- Node.js and npm (for contract compilation)
- Ethereum node access (Infura, Alchemy, etc.)

## Installation

1. Install Python dependencies:
   ```
   pip install -r requirements_phase2.txt
   ```

2. Set up environment variables by copying `.env.example` to `.env` and filling in your values:
   ```
   cp .env.example .env
   ```

3. Make sure Redis is running:
   ```
   redis-server
   ```

## Running the System

1. Start the Celery worker (in a separate terminal):
   ```
   celery -A pipelines.arbitrage_pipeline worker --loglevel=info
   ```

2. Start the main application:
   ```
   python main.py
   ```

3. For testing, you can run the market data simulator:
   ```
   python market_data_simulator.py
   ```

4. Open the monitoring dashboard by opening `monitoring_dashboard.html` in your web browser.

## Integration with Phase 1

This system integrates with the security-enhanced smart contracts from Phase 1:

- The Transaction Manager connects to the `MyArbitrageContract` to execute flash loans
- The system respects the role-based access control implemented in `SystemAccessControl`
- The pipeline can utilize the `SecurePriceOracle` for price validation

## Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Market Data    │     │   Processing    │     │  Transaction    │
│   Simulator     │────▶│    Pipeline     │────▶│    Manager      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                      │                       │
         │                      │                       │
         ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Event Bus                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │
                                ▼
                     ┌─────────────────────┐
                     │     Monitoring      │
                     │      Service        │
                     └─────────────────────┘
                                │
                                │
                                ▼
                     ┌─────────────────────┐
                     │     Dashboard       │
                     │       UI            │
                     └─────────────────────┘
```

## Smart Contract Integration

The Transaction Manager interacts with the `MyArbitrageContract` from Phase 1, which includes:

- Enhanced access control
- Reentrancy protection
- Secure oracle integration
- Emergency circuit breakers

## Next Steps

After successfully implementing Phase 2, you can proceed to:

1. Deploy the smart contracts to a testnet
2. Configure the system with real market data sources
3. Implement more sophisticated arbitrage strategies
4. Proceed to Phase 3: Frontend & UX Improvements