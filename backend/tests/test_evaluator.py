"""
Unit tests for the TradeEvaluator.

All tests use mocked Web3 responses so no live RPC is required.
"""

from __future__ import annotations

import types
from unittest.mock import MagicMock, patch

import pytest

from src.config import Settings, ChainConfig, TokenInfo
from src.evaluator import (
    AAVE_FLASH_LOAN_PREMIUM_BPS,
    GAS_ESTIMATE_FALLBACK,
    SLIPPAGE_BUFFER_BPS,
    TradeEvaluator,
)
from src.scanner import ArbitrageOpportunity


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_chain() -> ChainConfig:
    return ChainConfig(
        chain_id=42161,
        chain_name="Arbitrum One",
        explorer="https://arbiscan.io",
        aave_v3_pool="0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        uniswap_v3_router="0xE592427A0AEce92De3Edee1F18E0157C05861564",
        uniswap_v3_quoter="0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
        sushiswap_v3_router="0x8A21F6768C1f8075791D08546Dadf6daA0bE820c",
        sushiswap_v3_quoter="0x0524E833cCD057e4d7A296e3aaAb9f7675964ce1",
        chainlink_eth_usd="0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612",
        chainlink_btc_usd="0x6ce185860a4963106506C203335A2910413708e9",
        tokens={
            "WETH": TokenInfo(symbol="WETH", address="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1", decimals=18),
            "USDC": TokenInfo(symbol="USDC", address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831", decimals=6),
            "USDT": TokenInfo(symbol="USDT", address="0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9", decimals=6),
            "WBTC": TokenInfo(symbol="WBTC", address="0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f", decimals=8),
            "ARB": TokenInfo(symbol="ARB", address="0x912CE59144191C1204E64559FE8253a0e49E6548", decimals=18),
        },
    )


def _make_settings(**overrides) -> Settings:
    defaults = dict(
        ALCHEMY_ARBITRUM_URL="https://arb-mainnet.g.alchemy.com/v2/test",
        PRIVATE_KEY="0x" + "ab" * 32,
        FLASH_LOAN_ARBITRAGE_ADDRESS="0x" + "00" * 20,
        MIN_PROFIT_USD=5.0,
        SCAN_PAIRS="WETH/USDC",
    )
    defaults.update(overrides)
    return Settings(**defaults)


def _make_opportunity(
    *,
    pair: str = "WETH/USDC",
    amount_in: int = 10 ** 18,          # 1 WETH
    expected_out_a: int = 3000_000_000,  # 3000 USDC  (on cheaper DEX)
    expected_out_b: int = 3030_000_000,  # 3030 USDC  (on pricier DEX)
) -> ArbitrageOpportunity:
    return ArbitrageOpportunity(
        pair=pair,
        dex_a="sushiswap",
        dex_b="uniswap_v3",
        price_a=3000.0,
        price_b=3030.0,
        spread_pct=1.0,
        amount_in=amount_in,
        expected_out_a=expected_out_a,
        expected_out_b=expected_out_b,
        fee_tier_a=0,
        fee_tier_b=3000,
        token_in="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        token_out="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        timestamp=1700000000.0,
    )


def _mock_w3(gas_price: int = 100_000_000) -> MagicMock:
    """Return a mock Web3 instance with a deterministic gas price."""
    w3 = MagicMock()
    w3.eth.gas_price = gas_price  # 0.1 gwei
    w3.eth.contract.return_value = MagicMock()
    # Chainlink call returns 3000 USD (8 decimals)
    chainlink_mock = MagicMock()
    chainlink_mock.functions.latestRoundData.return_value.call.return_value = (
        1, 3000_0000_0000, 0, 0, 1  # answer = 3000 * 1e8
    )
    w3.eth.contract.return_value = chainlink_mock
    return w3


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTradeEvaluator:

    def test_profit_calculation_known_values(self):
        """Verify net profit arithmetic with deterministic inputs."""
        w3 = _mock_w3(gas_price=100_000_000)  # 0.1 gwei
        settings = _make_settings(MIN_PROFIT_USD=5.0)
        chain = _make_chain()
        evaluator = TradeEvaluator(w3, settings, chain)

        opp = _make_opportunity(
            amount_in=10 ** 18,
            expected_out_a=3_000_000_000,    # 3000 USDC
            expected_out_b=3_030_000_000,    # 3030 USDC
        )

        decision = evaluator.evaluate(opp)

        # Gross = |3030 - 3000| USDC in 6-decimal units = 30_000_000
        assert decision.net_profit_wei is not None

        # Premium = 1e18 * 5 / 10000 = 5e14
        expected_premium = 10 ** 18 * AAVE_FLASH_LOAN_PREMIUM_BPS // 10_000
        assert decision.premium_wei == expected_premium

        # Slippage = 1e18 * 100 / 10000 = 1e16
        expected_slippage = 10 ** 18 * SLIPPAGE_BUFFER_BPS // 10_000
        assert decision.slippage_buffer_wei == expected_slippage

    def test_go_false_when_profit_below_threshold(self):
        """When spread is tiny, go should be False."""
        w3 = _mock_w3(gas_price=100_000_000)
        settings = _make_settings(MIN_PROFIT_USD=100.0)  # high threshold
        chain = _make_chain()
        evaluator = TradeEvaluator(w3, settings, chain)

        opp = _make_opportunity(
            expected_out_a=3_000_000_000,
            expected_out_b=3_000_100_000,    # only $0.10 spread
        )

        decision = evaluator.evaluate(opp)
        assert decision.go is False

    def test_go_true_when_profit_above_threshold(self):
        """A large spread should produce go=True with a low threshold."""
        w3 = _mock_w3(gas_price=100_000)  # very cheap gas (~Arbitrum level)
        settings = _make_settings(MIN_PROFIT_USD=1.0)
        chain = _make_chain()
        evaluator = TradeEvaluator(w3, settings, chain)

        # 100 USDC spread on 1 WETH
        opp = _make_opportunity(
            expected_out_a=3_000_000_000,
            expected_out_b=3_100_000_000,
        )

        decision = evaluator.evaluate(opp)
        assert decision.go is True
        assert decision.net_profit_usd > 1.0

    def test_gas_cost_uses_fallback(self):
        """Gas estimate should use the 500k fallback constant."""
        w3 = _mock_w3(gas_price=200_000_000)  # 0.2 gwei
        settings = _make_settings()
        chain = _make_chain()
        evaluator = TradeEvaluator(w3, settings, chain)

        opp = _make_opportunity()
        decision = evaluator.evaluate(opp)

        assert decision.gas_estimate == GAS_ESTIMATE_FALLBACK
        expected_gas_cost = GAS_ESTIMATE_FALLBACK * 200_000_000
        assert decision.gas_cost_wei == expected_gas_cost

    def test_eth_price_fallback(self):
        """If Chainlink call fails, a default ETH price should be used."""
        w3 = _mock_w3()
        # Make the Chainlink call fail
        chainlink_mock = MagicMock()
        chainlink_mock.functions.latestRoundData.return_value.call.side_effect = Exception("RPC down")
        w3.eth.contract.return_value = chainlink_mock

        settings = _make_settings()
        chain = _make_chain()
        evaluator = TradeEvaluator(w3, settings, chain)

        price = evaluator.get_eth_price_usd()
        assert price == 3000.0  # hardcoded fallback
