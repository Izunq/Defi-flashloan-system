"""
System monitor and REST API.

Collects events from the scanner, evaluator, and executor, exposes them
through a FastAPI server, and keeps rolling statistics.
"""

from __future__ import annotations

import asyncio
import collections
import logging
import time
from dataclasses import asdict, dataclass, field

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3

from .scanner import ArbitrageOpportunity
from .evaluator import TradeDecision, CHAINLINK_AGGREGATOR_ABI
from .executor import TradeResult

logger = logging.getLogger(__name__)

# Maximum items kept in the ring buffers
MAX_HISTORY = 1_000


# ---------------------------------------------------------------------------
# PnL snapshot
# ---------------------------------------------------------------------------

@dataclass
class PnLSnapshot:
    total_profit_wei: int = 0
    total_profit_usd: float = 0.0
    total_gas_spent: int = 0
    net_profit_wei: int = 0
    net_profit_usd: float = 0.0
    trade_count: int = 0


# ---------------------------------------------------------------------------
# SystemMonitor
# ---------------------------------------------------------------------------

class SystemMonitor:
    """
    Accumulates runtime events from the arbitrage pipeline and exposes
    them via a FastAPI application.
    """

    def __init__(self, w3: Web3, chain_id: int, chainlink_eth_usd: str = "") -> None:
        self.w3 = w3
        self.chain_id = chain_id
        self.start_time = time.time()

        # Chainlink ETH/USD feed for PnL conversion
        self._eth_usd_feed = None
        if chainlink_eth_usd:
            self._eth_usd_feed = w3.eth.contract(
                address=Web3.to_checksum_address(chainlink_eth_usd),
                abi=CHAINLINK_AGGREGATOR_ABI,
            )
        self._cached_eth_price: float = 3000.0

        # Counters
        self.opportunities_found: int = 0
        self.trades_executed: int = 0
        self.trades_successful: int = 0
        self.total_profit_wei: int = 0
        self.total_profit_usd: float = 0.0
        self.total_gas_spent_wei: int = 0

        # Ring buffers
        self.recent_opportunities: collections.deque[dict] = collections.deque(
            maxlen=MAX_HISTORY
        )
        self.recent_trades: collections.deque[dict] = collections.deque(
            maxlen=MAX_HISTORY
        )

        # Scanning / executing flags (set by orchestrator)
        self.is_scanning: bool = False
        self.is_executing: bool = False

        # Build the FastAPI app
        self.app = self._build_app()

    # ----- event recording ------------------------------------------------

    def record_opportunity(self, opp: ArbitrageOpportunity) -> None:
        self.opportunities_found += 1
        self.recent_opportunities.append(asdict(opp))

    def record_trade(self, decision: TradeDecision, result: TradeResult) -> None:
        self.trades_executed += 1
        if result.success:
            self.trades_successful += 1
            self.total_profit_wei += result.profit_actual
            # Accumulate profit in USD (already calculated by evaluator)
            self.total_profit_usd += decision.net_profit_usd
        self.total_gas_spent_wei += result.gas_used * result.gas_price
        self.recent_trades.append(
            {
                "decision": {
                    "pair": decision.opportunity.pair,
                    "dex_a": decision.opportunity.dex_a,
                    "dex_b": decision.opportunity.dex_b,
                    "spread_pct": decision.opportunity.spread_pct,
                    "net_profit_usd": decision.net_profit_usd,
                    "gas_estimate": decision.gas_estimate,
                },
                "result": {
                    "tx_hash": result.tx_hash,
                    "success": result.success,
                    "profit_actual": result.profit_actual,
                    "gas_used": result.gas_used,
                    "gas_price": result.gas_price,
                    "timestamp": result.timestamp,
                    "error": result.error,
                },
            }
        )

    # ----- FastAPI application --------------------------------------------

    def _build_app(self) -> FastAPI:
        app = FastAPI(
            title="Flash Loan Arbitrage Monitor",
            version="1.0.0",
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # -- routes --------------------------------------------------------

        @app.get("/api/status")
        async def status():
            loop = asyncio.get_running_loop()
            try:
                block_number = await loop.run_in_executor(
                    None, lambda: self.w3.eth.block_number
                )
                gas_price = await loop.run_in_executor(
                    None, lambda: self.w3.eth.gas_price
                )
            except Exception:
                block_number = 0
                gas_price = 0

            return {
                "uptime": round(time.time() - self.start_time, 1),
                "chain_id": self.chain_id,
                "block_number": block_number,
                "gas_price": gas_price,
                "gas_price_gwei": round(gas_price / 1e9, 4) if gas_price else 0,
                "is_scanning": self.is_scanning,
                "is_executing": self.is_executing,
            }

        @app.get("/api/opportunities")
        async def opportunities():
            return {
                "total_found": self.opportunities_found,
                "recent": list(self.recent_opportunities),
            }

        @app.get("/api/trades")
        async def trades():
            return {
                "total_executed": self.trades_executed,
                "total_successful": self.trades_successful,
                "recent": list(self.recent_trades),
            }

        @app.get("/api/pnl")
        async def pnl():
            # Fetch ETH/USD price for gas cost conversion
            eth_price = self._cached_eth_price
            if self._eth_usd_feed is not None:
                loop = asyncio.get_running_loop()
                try:
                    data = await loop.run_in_executor(
                        None,
                        self._eth_usd_feed.functions.latestRoundData().call,
                    )
                    answer = data[1]
                    if answer > 0:
                        eth_price = answer / 1e8
                        self._cached_eth_price = eth_price
                except Exception as exc:
                    logger.debug("PnL ETH/USD fetch failed: %s", exc)

            # Gas is always in native ETH wei
            gas_usd = (self.total_gas_spent_wei / 1e18) * eth_price
            net_usd = self.total_profit_usd - gas_usd

            return {
                "total_profit_wei": self.total_profit_wei,
                "total_profit_usd": round(self.total_profit_usd, 2),
                "total_gas_spent": self.total_gas_spent_wei,
                "net_profit_wei": self.total_profit_wei - self.total_gas_spent_wei,
                "net_profit_usd": round(net_usd, 2),
                "trade_count": self.trades_executed,
            }

        @app.get("/api/pool")
        async def pool():
            """Placeholder for MudarabahPool stats (populated after pool deployment)."""
            return {
                "status": "not_deployed",
                "total_deposits": 0,
                "total_shares": 0,
                "profit_share_ratio": 0,
            }

        return app

    # ----- server lifecycle -----------------------------------------------

    async def start(self, port: int) -> None:
        """
        Start the uvicorn server in the background.

        We use ``uvicorn.Server`` directly so it runs inside the existing
        asyncio event loop without blocking.
        """
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=False,
        )
        server = uvicorn.Server(config)
        logger.info("Monitor API starting on http://0.0.0.0:%d", port)
        await server.serve()
