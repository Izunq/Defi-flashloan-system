"""
Scan-only mode -- prints arbitrage opportunities without executing.

    python -m src.scan_only
"""
from __future__ import annotations

import asyncio
import logging

from .config import Settings, load_chain_config
from .scanner import ArbitrageScanner, ArbitrageOpportunity
from .evaluator import TradeEvaluator

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = Settings()
    chain = load_chain_config(settings.CHAIN_CONFIG)
    w3 = settings.get_web3()
    scanner = ArbitrageScanner(w3, settings, chain)
    evaluator = TradeEvaluator(w3, settings, chain)

    async def on_opps(opps: list[ArbitrageOpportunity]) -> None:
        for opp in opps:
            decision = evaluator.evaluate(opp)
            tag = "GO" if decision.go else "SKIP"
            logger.info(
                "[%s] %s  spread=%.3f%%  net=$%.2f",
                tag, opp.pair, opp.spread_pct, decision.net_profit_usd,
            )

    await scanner.start(on_opps)


if __name__ == "__main__":
    asyncio.run(main())
