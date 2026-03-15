"""
Unit tests for the ArbitrageScanner.

Uses mock web3 contract calls to verify opportunity detection and spread
calculation without requiring a live RPC connection.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.config import Settings, ChainConfig, TokenInfo
from src.scanner import ArbitrageScanner, MIN_SPREAD_PCT


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
        chainlink_eth_usd="0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612",
        chainlink_btc_usd="0x6ce185860a4963106506C203335A2910413708e9",
        tokens={
            "WETH": TokenInfo(symbol="WETH", address="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1", decimals=18),
            "USDC": TokenInfo(symbol="USDC", address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831", decimals=6),
        },
    )


def _make_settings() -> Settings:
    return Settings(
        ALCHEMY_ARBITRUM_URL="https://arb-mainnet.g.alchemy.com/v2/test",
        PRIVATE_KEY="0x" + "ab" * 32,
        SCAN_PAIRS="WETH/USDC",
    )


def _mock_w3() -> MagicMock:
    w3 = MagicMock()
    return w3


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestArbitrageScanner:

    def test_opportunity_detected_with_spread(self):
        """
        When Uniswap returns more than SushiSwap, an opportunity should
        be detected if the spread exceeds MIN_SPREAD_PCT.
        """
        w3 = _mock_w3()
        settings = _make_settings()
        chain = _make_chain()

        scanner = ArbitrageScanner(w3, settings, chain)

        # Mock Uniswap V3 -- best quote returns (amount_out, fee_tier)
        scanner._best_uniswap_quote = MagicMock(return_value=(3050_000_000, 500))

        # Mock SushiSwap V3 -- return 3000 USDC at fee tier 3000
        scanner._best_sushi_quote = MagicMock(return_value=(3000_000_000, 3000))

        opps = scanner.scan_once()

        assert len(opps) == 1
        opp = opps[0]
        assert opp.pair == "WETH/USDC"
        assert opp.spread_pct > MIN_SPREAD_PCT
        # Uniswap gives more -> buy on sushi (cheaper), sell on uni
        assert opp.dex_a == "sushiswap"
        assert opp.dex_b == "uniswap_v3"

    def test_no_opportunity_when_spread_too_small(self):
        """If spread < MIN_SPREAD_PCT, no opportunities should surface."""
        w3 = _mock_w3()
        settings = _make_settings()
        chain = _make_chain()

        scanner = ArbitrageScanner(w3, settings, chain)

        # Nearly identical prices
        scanner._best_uniswap_quote = MagicMock(return_value=(3000_000_000, 500))
        scanner._best_sushi_quote = MagicMock(return_value=(3000_010_000, 3000))  # 0.0003% spread

        opps = scanner.scan_once()
        assert len(opps) == 0

    def test_spread_calculation_accuracy(self):
        """Verify the spread percentage formula."""
        w3 = _mock_w3()
        settings = _make_settings()
        chain = _make_chain()

        scanner = ArbitrageScanner(w3, settings, chain)

        # Uniswap: 3000, SushiSwap: 3030 => spread = 30/3000 * 100 = 1.0%
        scanner._best_uniswap_quote = MagicMock(return_value=(3000_000_000, 500))
        scanner._best_sushi_quote = MagicMock(return_value=(3030_000_000, 3000))

        opps = scanner.scan_once()

        assert len(opps) == 1
        assert abs(opps[0].spread_pct - 1.0) < 0.01

    def test_handles_failed_uniswap_quote(self):
        """If Uniswap returns None for all fee tiers, skip the pair."""
        w3 = _mock_w3()
        settings = _make_settings()
        chain = _make_chain()

        scanner = ArbitrageScanner(w3, settings, chain)

        scanner._best_uniswap_quote = MagicMock(return_value=None)
        scanner._best_sushi_quote = MagicMock(return_value=(3000_000_000, 3000))

        opps = scanner.scan_once()
        assert len(opps) == 0

    def test_handles_failed_sushiswap_quote(self):
        """If SushiSwap returns None, skip the pair."""
        w3 = _mock_w3()
        settings = _make_settings()
        chain = _make_chain()

        scanner = ArbitrageScanner(w3, settings, chain)

        scanner._best_uniswap_quote = MagicMock(return_value=(3000_000_000, 500))
        scanner._best_sushi_quote = MagicMock(return_value=None)

        opps = scanner.scan_once()
        assert len(opps) == 0

    def test_unknown_token_skipped(self):
        """If a configured pair references an unknown token, skip it."""
        w3 = _mock_w3()
        settings = Settings(
            ALCHEMY_ARBITRUM_URL="https://arb-mainnet.g.alchemy.com/v2/test",
            PRIVATE_KEY="0x" + "ab" * 32,
            SCAN_PAIRS="WETH/UNKNOWN",
        )
        chain = _make_chain()

        scanner = ArbitrageScanner(w3, settings, chain)
        opps = scanner.scan_once()
        assert len(opps) == 0
