# DeFi Flash Loan Arbitrage System

Production-grade flash loan arbitrage bot on Arbitrum One with Sharia-compliant Mudarabah profit-sharing pool.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SMART CONTRACTS (Solidity)            │
│                                                         │
│  FlashLoanArbitrage.sol  — Aave V3 flash loan + DEX     │
│                            swap execution                │
│  MudarabahPool.sol       — Sharia-compliant profit-     │
│                            sharing pool (no fixed fee)   │
│  HalalAssetRegistry.sol  — Allowlist of compliant tokens│
│  PriceOracle.sol         — Multi-source Chainlink       │
│                            aggregation w/ manipulation   │
│                            resistance                    │
└──────────────────────┬──────────────────────────────────┘
                       │ ethers.js / web3.py
┌──────────────────────▼──────────────────────────────────┐
│                    BACKEND (Python)                      │
│                                                         │
│  scanner.py      — Monitors DEX prices on-chain         │
│  evaluator.py    — Calculates net profit after gas      │
│  executor.py     — Signs & submits flash loan tx        │
│  monitor.py      — HTTP API for frontend + logging      │
│  main.py         — Async orchestrator                   │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────┐
│                    FRONTEND (React + Vite)               │
│                                                         │
│  Dashboard: live opportunities, trade history, P&L,     │
│  pool status, system health                             │
└─────────────────────────────────────────────────────────┘
```

## Target Chain

- **Primary**: Arbitrum One (low gas, Aave V3, Uniswap V3 + SushiSwap)
- **Testnet**: Arbitrum Sepolia

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- An Alchemy API key (Arbitrum endpoints)

### 1. Install Dependencies

```bash
# Smart contracts
npm install

# Python backend
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys:
#   ALCHEMY_ARBITRUM_URL, ALCHEMY_ARBITRUM_SEPOLIA_URL
#   PRIVATE_KEY (executor wallet)
#   ARBISCAN_API_KEY
```

### 3. Compile & Test Contracts

```bash
npx hardhat compile
npx hardhat test
```

### 4. Deploy to Testnet

```bash
npx hardhat run scripts/deploy-testnet.js --network arbitrumSepolia
npx hardhat run scripts/verify.js --network arbitrumSepolia
```

### 5. Run Backend

```bash
cd backend
python -m src.main
```

### 6. Run Frontend

```bash
cd frontend
npm run dev
```

## Project Structure

```
├── contracts/
│   ├── core/           # FlashLoanArbitrage, MudarabahPool
│   ├── compliance/     # HalalAssetRegistry
│   ├── oracle/         # PriceOracle
│   ├── interfaces/     # IAaveV3Pool, ISwapRouter, etc.
│   └── libraries/      # SwapHelper
├── test/               # Hardhat tests
├── scripts/            # Deploy & verify scripts
├── backend/
│   ├── src/            # Python arbitrage bot
│   └── tests/          # pytest unit tests
├── frontend/
│   └── src/            # React dashboard
└── config/             # Chain configs, token lists
```

## Smart Contracts

| Contract | Purpose |
|----------|---------|
| `FlashLoanArbitrage` | Takes Aave V3 flash loan, swaps across two DEXes, repays + keeps profit |
| `MudarabahPool` | Sharia-compliant lending pool with profit-sharing (70/30 split) |
| `HalalAssetRegistry` | On-chain allowlist for Sharia-compliant tokens |
| `PriceOracle` | Multi-feed Chainlink aggregation with staleness & deviation checks |

## Sharia Compliance

The Mudarabah model replaces traditional flash loan fees:
- No fixed interest (riba) — profit-sharing only
- Capital providers deposit tokens (rab al-mal)
- Traders (mudaribs) borrow within a single transaction
- Profit: 70% to providers, 30% to mudarib (configurable with 24h timelock)
- Zero-profit trades incur no fee

## Security

- OpenZeppelin 5.x AccessControl (not Ownable)
- ReentrancyGuard on all state-changing external calls
- Pausable for emergency stops
- Slippage protection on all swaps (never amountOutMinimum = 0)
- Oracle manipulation resistance via median pricing + deviation bounds
- Role-based access: ADMIN_ROLE, EXECUTOR_ROLE, MUDARIB_ROLE, SHARIAH_COMMITTEE_ROLE

## Mainnet Deployment Checklist

- [ ] All tests passing
- [ ] Contracts verified on Arbiscan
- [ ] Backend stable for 24h+ on testnet
- [ ] Start with small trade sizes ($100-$500)
- [ ] Conservative profit threshold ($10+)
- [ ] Monitor-only mode for first 24-48h
- [ ] Fund executor wallet with 0.05 ETH for gas

## License

MIT
