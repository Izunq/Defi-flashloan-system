"""
Trade evaluator -- decides whether an arbitrage opportunity is worth executing.

Accounts for:
  * gas cost (estimated or fallback)
  * Aave V3 flash-loan premium (0.05 %)
  * slippage buffer (1 % of trade size)
  * configurable minimum USD profit threshold
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from web3 import Web3

from .config import Settings, ChainConfig
from .scanner import ArbitrageOpportunity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Chainlink AggregatorV3 (latestRoundData) -- minimal ABI
# ---------------------------------------------------------------------------

CHAINLINK_AGGREGATOR_ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"internalType": "uint80", "name": "roundId", "type": "uint80"},
            {"internalType": "int256", "name": "answer", "type": "int256"},
            {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
            {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
            {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AAVE_FLASH_LOAN_PREMIUM_BPS = 5          # 0.05 % = 5 basis-points
SLIPPAGE_BUFFER_BPS = 100                # 1 %
GAS_ESTIMATE_FALLBACK = 500_000          # gas units


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TradeDecision:
    """Result of evaluating a single :class:`ArbitrageOpportunity`."""

    opportunity: ArbitrageOpportunity
    net_profit_wei: int
    net_profit_usd: float
    gas_estimate: int
    gas_cost_wei: int
    premium_wei: int
    slippage_buffer_wei: int
    go: bool


# ---------------------------------------------------------------------------
# TradeEvaluator
# ---------------------------------------------------------------------------

class TradeEvaluator:
    """
    Receives an :class:`ArbitrageOpportunity` and decides whether to execute.
    """

    def __init__(self, w3: Web3, settings: Settings, chain: ChainConfig) -> None:
        self.w3 = w3
        self.settings = settings
        self.chain = chain

        # Chainlink price feed for ETH/USD
        self._eth_usd_feed = w3.eth.contract(
            address=Web3.to_checksum_address(chain.chainlink_eth_usd),
            abi=CHAINLINK_AGGREGATOR_ABI,
        )

        # Chainlink price feed for BTC/USD (cached)
        self._btc_usd_feed = w3.eth.contract(
            address=Web3.to_checksum_address(chain.chainlink_btc_usd),
            abi=CHAINLINK_AGGREGATOR_ABI,
        )

        # Cached ETH price (refreshed each evaluation)
        self._eth_price_usd: float = 0.0

    # ----- ETH price ------------------------------------------------------

    def get_eth_price_usd(self) -> float:
        """
        Fetch the latest ETH/USD price from the Chainlink on-chain oracle.
        Falls back to a hardcoded estimate on failure.
        """
        try:
            (_round_id, answer, _started, _updated, _answered) = (
                self._eth_usd_feed.functions.latestRoundData().call()
            )
            # Chainlink ETH/USD feed uses 8 decimals
            price = answer / 1e8
            if price > 0:
                self._eth_price_usd = price
                return price
        except Exception as exc:
            logger.warning("Chainlink ETH/USD query failed: %s", exc)

        # Fallback: use last-known or a reasonable default
        if self._eth_price_usd > 0:
            return self._eth_price_usd
        self._eth_price_usd = 3000.0
        return self._eth_price_usd

    # ----- gas estimation -------------------------------------------------

    def _estimate_gas_cost(self) -> tuple[int, int]:
        """
        Return ``(gas_units, gas_cost_wei)``.

        Tries to read the current gas price from the node; falls back to
        the constant estimate if the RPC call fails.
        """
        try:
            gas_price = self.w3.eth.gas_price
        except Exception:
            gas_price = Web3.to_wei(0.1, "gwei")  # Arbitrum typical

        return GAS_ESTIMATE_FALLBACK, GAS_ESTIMATE_FALLBACK * gas_price

    # ----- core evaluation ------------------------------------------------

    def evaluate(self, opp: ArbitrageOpportunity) -> TradeDecision:
        """
        Evaluate whether *opp* produces a net profit worth executing.

        All costs are converted to USD before computing the net figure,
        since the input token (e.g. WETH, 18 decimals) and output token
        (e.g. USDC, 6 decimals) are generally in different unit scales.
        """
        eth_price = self.get_eth_price_usd()

        # Resolve token info
        input_symbol = opp.pair.split("/")[0]
        output_symbol = opp.pair.split("/")[1]
        input_decimals = self.chain.tokens[input_symbol].decimals
        output_decimals = self.chain.tokens[output_symbol].decimals
        usd_per_input = self._usd_per_unit(input_symbol, eth_price)
        usd_per_output = self._usd_per_unit(output_symbol, eth_price)

        # Gross profit in the *output* token's smallest unit
        gross_wei = abs(opp.expected_out_a - opp.expected_out_b)
        gross_usd = (gross_wei / (10 ** output_decimals)) * usd_per_output

        # Aave premium on the borrowed amount (input token units)
        premium_wei = opp.amount_in * AAVE_FLASH_LOAN_PREMIUM_BPS // 10_000
        premium_usd = (premium_wei / (10 ** input_decimals)) * usd_per_input

        # Slippage buffer (input token units)
        slippage_buffer_wei = opp.amount_in * SLIPPAGE_BUFFER_BPS // 10_000
        slippage_usd = (slippage_buffer_wei / (10 ** input_decimals)) * usd_per_input

        # Gas cost (in native ETH wei)
        gas_units, gas_cost_wei = self._estimate_gas_cost()
        gas_usd = (gas_cost_wei / 1e18) * eth_price

        # Net profit in USD
        net_profit_usd = gross_usd - premium_usd - slippage_usd - gas_usd

        # Approximate net in output-token units (convert all costs to output units)
        if usd_per_output > 0:
            costs_in_output = int(
                ((premium_usd + slippage_usd + gas_usd) / usd_per_output)
                * (10 ** output_decimals)
            )
        else:
            costs_in_output = 0
        net_profit_wei = gross_wei - costs_in_output

        go = net_profit_usd > self.settings.MIN_PROFIT_USD

        logger.info(
            "%s  gross=$%.2f  premium=$%.2f  slip=$%.2f  gas=$%.4f  net=$%.2f  go=%s",
            opp.pair,
            gross_usd,
            premium_usd,
            slippage_usd,
            gas_usd,
            net_profit_usd,
            go,
        )

        return TradeDecision(
            opportunity=opp,
            net_profit_wei=net_profit_wei,
            net_profit_usd=net_profit_usd,
            gas_estimate=gas_units,
            gas_cost_wei=gas_cost_wei,
            premium_wei=premium_wei,
            slippage_buffer_wei=slippage_buffer_wei,
            go=go,
        )

    # ----- helpers --------------------------------------------------------

    def _usd_per_unit(self, symbol: str, eth_price: float) -> float:
        """Rough USD value of one whole unit of the given token."""
        mapping: dict[str, float] = {
            "WETH": eth_price,
            "WBTC": eth_price * 20,   # BTC ~ 20x ETH, updated at runtime below
            "USDC": 1.0,
            "USDT": 1.0,
            "ARB": 1.0,
        }
        # Try to get a more accurate BTC price from Chainlink
        if symbol == "WBTC":
            try:
                (_, answer, *_rest) = self._btc_usd_feed.functions.latestRoundData().call()
                if answer > 0:
                    mapping["WBTC"] = answer / 1e8
            except Exception:
                pass  # keep the estimate

        return mapping.get(symbol, 1.0)
