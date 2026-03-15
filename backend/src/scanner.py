"""
Async price scanner that queries Uniswap V3 and SushiSwap on Arbitrum
to detect cross-DEX arbitrage opportunities.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Callable, Awaitable

from web3 import Web3
from web3.contract import Contract

from .config import Settings, ChainConfig, TokenInfo

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Minimal ABIs (only the functions we call)
# ---------------------------------------------------------------------------

UNISWAP_V3_QUOTER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenIn", "type": "address"},
            {"internalType": "address", "name": "tokenOut", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

SUSHISWAP_V3_QUOTER_ABI = UNISWAP_V3_QUOTER_ABI  # Same interface (SushiSwap V3)

# SushiSwap V3 fee tiers (often different pool availability than Uniswap)
SUSHI_FEE_TIERS: list[int] = [500, 3000, 10000]

# Common Uniswap V3 fee tiers to try (in hundredths of a basis point)
FEE_TIERS: list[int] = [500, 3000, 10000]

# Minimum spread percentage to qualify as an opportunity
MIN_SPREAD_PCT = 0.1


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ArbitrageOpportunity:
    """Represents a detected price discrepancy across two DEXes."""

    pair: str                # e.g. "WETH/USDC"
    dex_a: str               # e.g. "uniswap_v3"
    dex_b: str               # e.g. "sushiswap"
    price_a: float           # price on dex_a (tokenOut per tokenIn)
    price_b: float           # price on dex_b
    spread_pct: float        # |price_a - price_b| / min(price_a, price_b) * 100
    amount_in: int           # wei amount used for the quote
    expected_out_a: int      # amountOut from dex_a
    expected_out_b: int      # amountOut from dex_b
    fee_tier_a: int          # fee tier used on dex_a (Uniswap V3)
    fee_tier_b: int          # fee tier used on dex_b (0 for SushiSwap)
    token_in: str            # address of input token
    token_out: str           # address of output token
    timestamp: float         # unix epoch


# ---------------------------------------------------------------------------
# ArbitrageScanner
# ---------------------------------------------------------------------------

class ArbitrageScanner:
    """
    Periodically queries Uniswap V3 Quoter and SushiSwap Router for price
    quotes across configured pairs and surfaces arbitrage opportunities.
    """

    def __init__(self, w3: Web3, settings: Settings, chain: ChainConfig) -> None:
        self.w3 = w3
        self.settings = settings
        self.chain = chain

        # Instantiate on-chain contract helpers
        self.quoter: Contract = w3.eth.contract(
            address=Web3.to_checksum_address(chain.uniswap_v3_quoter),
            abi=UNISWAP_V3_QUOTER_ABI,
        )
        # SushiSwap V3 Quoter (same interface as Uniswap V3 Quoter)
        self.sushi_quoter: Contract = w3.eth.contract(
            address=Web3.to_checksum_address(chain.sushiswap_v3_quoter),
            abi=SUSHISWAP_V3_QUOTER_ABI,
        )

        self._running = False

    # ----- helpers --------------------------------------------------------

    def _resolve_token(self, symbol: str) -> TokenInfo:
        """Look up a token by symbol; raise KeyError if unknown."""
        token = self.chain.tokens.get(symbol)
        if token is None:
            raise KeyError(f"Unknown token symbol: {symbol}")
        return token

    def _default_amount_in(self, token: TokenInfo) -> int:
        """Return a sensible default quote amount for the given token."""
        amounts: dict[str, float] = {
            "WETH": 1.0,
            "WBTC": 0.1,
            "USDC": 2000.0,
            "USDT": 2000.0,
            "ARB": 2000.0,
        }
        human = amounts.get(token.symbol, 1.0)
        return int(human * (10 ** token.decimals))

    # ----- Uniswap V3 quote (via eth_call) --------------------------------

    def _quote_uniswap_v3(
        self,
        token_in: str,
        token_out: str,
        fee: int,
        amount_in: int,
    ) -> int | None:
        """
        Call Quoter.quoteExactInputSingle via eth_call (static).
        Returns amountOut or None on failure.
        """
        try:
            amount_out: int = self.quoter.functions.quoteExactInputSingle(
                Web3.to_checksum_address(token_in),
                Web3.to_checksum_address(token_out),
                fee,
                amount_in,
                0,  # sqrtPriceLimitX96 = 0 means no limit
            ).call()
            return amount_out
        except Exception as exc:
            logger.debug(
                "Uniswap V3 quote failed (fee=%d): %s", fee, exc
            )
            return None

    # ----- SushiSwap V3 quote ------------------------------------------------

    def _quote_sushiswap_v3(
        self,
        token_in: str,
        token_out: str,
        fee: int,
        amount_in: int,
    ) -> int | None:
        """
        Call SushiSwap V3 Quoter.quoteExactInputSingle via eth_call.
        Returns amountOut or None on failure.
        """
        try:
            amount_out: int = self.sushi_quoter.functions.quoteExactInputSingle(
                Web3.to_checksum_address(token_in),
                Web3.to_checksum_address(token_out),
                fee,
                amount_in,
                0,
            ).call()
            return amount_out
        except Exception as exc:
            logger.debug("SushiSwap V3 quote failed (fee=%d): %s", fee, exc)
            return None

    def _best_sushi_quote(
        self, token_in: str, token_out: str, amount_in: int
    ) -> tuple[int, int] | None:
        """Return (best_amount_out, fee_tier) across SushiSwap V3 fee tiers, or None."""
        best: tuple[int, int] | None = None
        for fee in SUSHI_FEE_TIERS:
            out = self._quote_sushiswap_v3(token_in, token_out, fee, amount_in)
            if out is not None and (best is None or out > best[0]):
                best = (out, fee)
        return best

    # ----- best Uniswap V3 quote across fee tiers -------------------------

    def _best_uniswap_quote(
        self, token_in: str, token_out: str, amount_in: int
    ) -> tuple[int, int] | None:
        """Return (best_amount_out, fee_tier) across all fee tiers, or None."""
        best: tuple[int, int] | None = None
        for fee in FEE_TIERS:
            out = self._quote_uniswap_v3(token_in, token_out, fee, amount_in)
            if out is not None and (best is None or out > best[0]):
                best = (out, fee)
        return best

    # ----- single scan round ----------------------------------------------

    def scan_once(self) -> list[ArbitrageOpportunity]:
        """
        Scan all configured pairs across Uniswap V3 and SushiSwap.
        Returns a list of opportunities whose spread exceeds MIN_SPREAD_PCT.
        """
        pairs = self.settings.get_scan_pairs()
        opportunities: list[ArbitrageOpportunity] = []
        now = time.time()

        for symbol_a, symbol_b in pairs:
            try:
                token_a = self._resolve_token(symbol_a)
                token_b = self._resolve_token(symbol_b)
            except KeyError as exc:
                logger.warning("Skipping pair %s/%s: %s", symbol_a, symbol_b, exc)
                continue

            amount_in = self._default_amount_in(token_a)

            # --- Uniswap V3 price ------------------------------------------
            uni_result = self._best_uniswap_quote(
                token_a.address, token_b.address, amount_in
            )
            if uni_result is None:
                logger.debug("No Uniswap V3 quote for %s/%s", symbol_a, symbol_b)
                continue
            uni_out, uni_fee = uni_result

            # --- SushiSwap V3 price -------------------------------------------
            sushi_result = self._best_sushi_quote(
                token_a.address, token_b.address, amount_in
            )
            if sushi_result is None:
                logger.debug("No SushiSwap V3 quote for %s/%s", symbol_a, symbol_b)
                continue
            sushi_out, sushi_fee = sushi_result

            # --- compute spread -------------------------------------------
            price_uni = uni_out / (10 ** token_b.decimals)
            price_sushi = sushi_out / (10 ** token_b.decimals)
            min_price = min(price_uni, price_sushi)

            if min_price == 0:
                continue

            spread_pct = abs(price_uni - price_sushi) / min_price * 100.0

            logger.info(
                "%-10s  Uni=%.6f  Sushi=%.6f  spread=%.4f%%",
                f"{symbol_a}/{symbol_b}",
                price_uni,
                price_sushi,
                spread_pct,
            )

            if spread_pct < MIN_SPREAD_PCT:
                continue

            # Determine direction: buy on cheaper DEX, sell on pricier one
            if uni_out > sushi_out:
                # Uniswap gives more output -> buy on sushi (cheaper), sell on uni
                dex_a, dex_b = "sushiswap", "uniswap_v3"
                out_a, out_b = sushi_out, uni_out
                fee_a, fee_b = sushi_fee, uni_fee
                pa, pb = price_sushi, price_uni
            else:
                dex_a, dex_b = "uniswap_v3", "sushiswap"
                out_a, out_b = uni_out, sushi_out
                fee_a, fee_b = uni_fee, sushi_fee
                pa, pb = price_uni, price_sushi

            opp = ArbitrageOpportunity(
                pair=f"{symbol_a}/{symbol_b}",
                dex_a=dex_a,
                dex_b=dex_b,
                price_a=pa,
                price_b=pb,
                spread_pct=spread_pct,
                amount_in=amount_in,
                expected_out_a=out_a,
                expected_out_b=out_b,
                fee_tier_a=fee_a,
                fee_tier_b=fee_b,
                token_in=token_a.address,
                token_out=token_b.address,
                timestamp=now,
            )
            opportunities.append(opp)

        return opportunities

    # ----- continuous scanning loop ----------------------------------------

    async def start(
        self,
        callback: Callable[[list[ArbitrageOpportunity]], Awaitable[None]],
    ) -> None:
        """
        Run :meth:`scan_once` in a loop (~250 ms cadence, roughly per-block
        on Arbitrum) and invoke *callback* with any opportunities found.

        Stops when :attr:`_running` is set to ``False``.
        """
        self._running = True
        logger.info("Scanner started  --  polling every ~250 ms")

        loop = asyncio.get_running_loop()

        while self._running:
            try:
                # Run the synchronous web3 calls in a thread so we don't
                # block the event loop.
                opps = await loop.run_in_executor(None, self.scan_once)

                if opps:
                    logger.info("Found %d opportunity(ies)", len(opps))
                    await callback(opps)

            except Exception:
                logger.exception("Scanner error (will retry next cycle)")

            await asyncio.sleep(0.25)

    def stop(self) -> None:
        """Signal the scanning loop to exit after the current cycle."""
        self._running = False
        logger.info("Scanner stop requested")
