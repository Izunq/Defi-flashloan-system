"""
Main orchestrator -- ties together scanner, evaluator, executor, and monitor.

    python -m src.main

Pure asyncio, no Redis, no Celery.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from web3 import Web3

from .config import Settings, load_chain_config, ChainConfig
from .scanner import ArbitrageScanner, ArbitrageOpportunity
from .evaluator import TradeEvaluator
from .executor import TradeExecutor
from .monitor import SystemMonitor

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def _print_banner(settings: Settings, chain: ChainConfig, wallet: str) -> None:
    pairs = settings.get_scan_pairs()
    print()
    print("=" * 62)
    print("  Flash Loan Arbitrage Bot  --  Arbitrum One")
    print("=" * 62)
    print(f"  Chain      : {chain.chain_name} (id={chain.chain_id})")
    print(f"  RPC        : {settings.ALCHEMY_ARBITRUM_URL[:40]}...")
    print(f"  Wallet     : {wallet}")
    print(f"  Contract   : {settings.FLASH_LOAN_ARBITRAGE_ADDRESS or 'NOT SET'}")
    print(f"  Pairs      : {', '.join(f'{a}/{b}' for a, b in pairs)}")
    print(f"  Min profit : ${settings.MIN_PROFIT_USD}")
    print(f"  Monitor    : http://0.0.0.0:{settings.MONITOR_PORT}")
    print("=" * 62)
    print()


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

def _health_checks(w3: Web3, settings: Settings, chain: ChainConfig) -> None:
    """Run startup health checks; exit on critical failure."""

    # 1. RPC connectivity
    if not w3.is_connected():
        logger.critical("Cannot connect to RPC endpoint")
        sys.exit(1)

    chain_id = w3.eth.chain_id
    if chain_id != chain.chain_id:
        logger.critical(
            "Chain ID mismatch: expected %d, got %d", chain.chain_id, chain_id
        )
        sys.exit(1)
    logger.info("RPC connected  --  chain_id=%d  latest_block=%d", chain_id, w3.eth.block_number)

    # 2. Wallet balance
    account = w3.eth.account.from_key(settings.PRIVATE_KEY)
    balance = w3.eth.get_balance(account.address)
    eth_balance = balance / 1e18
    if eth_balance < 0.001:
        logger.warning(
            "Wallet %s has very low ETH balance: %.6f  --  "
            "transactions may fail due to insufficient gas",
            account.address,
            eth_balance,
        )
    else:
        logger.info("Wallet %s  balance=%.4f ETH", account.address, eth_balance)

    # 3. Contract address (warn, don't exit -- scanning still works)
    if not settings.FLASH_LOAN_ARBITRAGE_ADDRESS:
        logger.warning(
            "FLASH_LOAN_ARBITRAGE_ADDRESS is not set.  "
            "Scanning will work, but execution is disabled."
        )
    else:
        code = w3.eth.get_code(
            Web3.to_checksum_address(settings.FLASH_LOAN_ARBITRAGE_ADDRESS)
        )
        if code == b"" or code == b"0x":
            logger.warning(
                "No contract code at %s  --  is it deployed?",
                settings.FLASH_LOAN_ARBITRAGE_ADDRESS,
            )
        else:
            logger.info(
                "FlashLoanArbitrage contract verified at %s",
                settings.FLASH_LOAN_ARBITRAGE_ADDRESS,
            )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run() -> None:
    """Async entry-point for the arbitrage bot."""

    # -- Load config -------------------------------------------------------
    settings = Settings()
    chain = load_chain_config(settings.CHAIN_CONFIG)
    w3 = settings.get_web3()

    account = w3.eth.account.from_key(settings.PRIVATE_KEY)
    _print_banner(settings, chain, account.address)

    # -- Health checks -----------------------------------------------------
    _health_checks(w3, settings, chain)

    # -- Create components -------------------------------------------------
    scanner = ArbitrageScanner(w3, settings, chain)
    evaluator = TradeEvaluator(w3, settings, chain)
    monitor = SystemMonitor(w3, chain.chain_id, chain.chainlink_eth_usd)

    # Executor is optional (requires deployed contract address)
    executor: TradeExecutor | None = None
    if settings.FLASH_LOAN_ARBITRAGE_ADDRESS:
        try:
            executor = TradeExecutor(w3, settings, chain)
            logger.info("Executor ready  --  execution enabled")
        except ValueError as exc:
            logger.warning("Executor disabled: %s", exc)
    else:
        logger.info("Executor disabled  --  scan-only mode")

    # -- Opportunity callback ----------------------------------------------

    async def on_opportunities(opps: list[ArbitrageOpportunity]) -> None:
        for opp in opps:
            monitor.record_opportunity(opp)

            decision = evaluator.evaluate(opp)

            if not decision.go:
                logger.debug("Skipping %s  --  profit too low", opp.pair)
                continue

            if executor is None:
                logger.info(
                    "Would execute %s (profit ~$%.2f) but executor is disabled",
                    opp.pair,
                    decision.net_profit_usd,
                )
                continue

            logger.info(
                "Executing %s  --  expected profit $%.2f",
                opp.pair,
                decision.net_profit_usd,
            )
            monitor.is_executing = True
            try:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None, executor.execute, decision
                )
                monitor.record_trade(decision, result)
            finally:
                monitor.is_executing = False

    # -- Graceful shutdown -------------------------------------------------

    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Shutdown signal received")
        scanner.stop()
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler; fall back to
            # signal.signal (only SIGINT is catchable on Windows).
            if sig == signal.SIGINT:
                signal.signal(sig, lambda *_: _signal_handler())

    # -- Start tasks -------------------------------------------------------

    monitor.is_scanning = True

    monitor_task = asyncio.create_task(monitor.start(settings.MONITOR_PORT))
    scanner_task = asyncio.create_task(scanner.start(on_opportunities))

    # Wait until stop is requested
    await stop_event.wait()

    # Cancel background tasks
    scanner_task.cancel()
    monitor_task.cancel()

    try:
        await asyncio.gather(scanner_task, monitor_task, return_exceptions=True)
    except asyncio.CancelledError:
        pass

    logger.info("Shutdown complete")


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    """Synchronous wrapper so ``python -m src.main`` works."""
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
