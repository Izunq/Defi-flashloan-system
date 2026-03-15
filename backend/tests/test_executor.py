"""
Unit tests for the TradeExecutor.

Verifies calldata encoding and transaction construction without requiring
an RPC connection or deployed contracts.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from web3 import Web3

from src.config import Settings, ChainConfig, TokenInfo
from src.executor import TradeExecutor, FLASH_LOAN_ARBITRAGE_ABI
from src.evaluator import TradeDecision
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
        FLASH_LOAN_ARBITRAGE_ADDRESS="0x" + "11" * 20,
    )


def _make_opportunity() -> ArbitrageOpportunity:
    return ArbitrageOpportunity(
        pair="WETH/USDC",
        dex_a="sushiswap",
        dex_b="uniswap_v3",
        price_a=3000.0,
        price_b=3030.0,
        spread_pct=1.0,
        amount_in=10 ** 18,
        expected_out_a=3_000_000_000,
        expected_out_b=3_030_000_000,
        fee_tier_a=0,
        fee_tier_b=3000,
        token_in="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        token_out="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        timestamp=1700000000.0,
    )


def _make_decision() -> TradeDecision:
    return TradeDecision(
        opportunity=_make_opportunity(),
        net_profit_wei=1_000_000,
        net_profit_usd=10.0,
        gas_estimate=500_000,
        gas_cost_wei=50_000_000_000_000,
        premium_wei=500_000_000_000_000,
        slippage_buffer_wei=10_000_000_000_000_000,
        go=True,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSwapRouteEncoding:

    def test_encode_swap_route_returns_bytes(self):
        """encode_swap_route should return a non-empty bytes object."""
        result = TradeExecutor.encode_swap_route(
            dex_a="0xE592427A0AEce92De3Edee1F18E0157C05861564",
            dex_b="0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
            token_out="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            fee_a=3000,
            fee_b=3000,
            amount_out_min_a=1_000_000,
            amount_out_min_b=900_000_000_000_000_000,
        )
        assert isinstance(result, bytes)
        # ABI encoding of 7 values: 7 * 32 = 224 bytes
        assert len(result) == 224

    def test_encode_swap_route_is_decodable(self):
        """The encoded bytes should be decodable back to the original values."""
        dex_a = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
        dex_b = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
        token_out = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
        fee_a = 3000
        fee_b = 500
        min_a = 2_900_000_000
        min_b = 980_000_000_000_000_000

        encoded = TradeExecutor.encode_swap_route(
            dex_a=dex_a,
            dex_b=dex_b,
            token_out=token_out,
            fee_a=fee_a,
            fee_b=fee_b,
            amount_out_min_a=min_a,
            amount_out_min_b=min_b,
        )

        # Decode using web3 codec
        w3 = Web3()
        decoded = w3.codec.decode(
            ["address", "address", "address", "uint24", "uint24", "uint256", "uint256"],
            encoded,
        )

        assert decoded[0].lower() == dex_a.lower()
        assert decoded[1].lower() == dex_b.lower()
        assert decoded[2].lower() == token_out.lower()
        assert decoded[3] == fee_a
        assert decoded[4] == fee_b
        assert decoded[5] == min_a
        assert decoded[6] == min_b


class TestTradeExecutor:

    def test_execute_builds_correct_transaction(self):
        """
        Verify that execute() calls build_transaction with the expected
        parameters.  We mock out the actual send.
        """
        w3 = MagicMock()
        w3.eth.gas_price = 100_000_000
        w3.eth.chain_id = 42161
        w3.eth.get_transaction_count.return_value = 42

        # Mock account
        account_mock = MagicMock()
        account_mock.address = "0x" + "aa" * 20
        w3.eth.account.from_key.return_value = account_mock

        # Mock contract
        contract_mock = MagicMock()
        tx_builder = MagicMock()
        tx_builder.build_transaction.return_value = {"raw": "tx_data"}
        contract_mock.functions.executeFlashLoan.return_value = tx_builder
        w3.eth.contract.return_value = contract_mock

        # Mock sign and send
        signed_mock = MagicMock()
        signed_mock.raw_transaction = b"\x00" * 32
        w3.eth.account.sign_transaction.return_value = signed_mock
        w3.eth.send_raw_transaction.return_value = b"\x01" * 32

        receipt_mock = {
            "status": 1,
            "gasUsed": 300_000,
            "logs": [],
        }
        w3.eth.wait_for_transaction_receipt.return_value = receipt_mock

        settings = _make_settings()
        chain = _make_chain()

        executor = TradeExecutor(w3, settings, chain)
        decision = _make_decision()

        result = executor.execute(decision)

        # Verify the contract function was called
        contract_mock.functions.executeFlashLoan.assert_called_once()

        # build_transaction should receive the correct chain ID and nonce
        call_kwargs = tx_builder.build_transaction.call_args[0][0]
        assert call_kwargs["chainId"] == 42161

    def test_execute_handles_revert(self):
        """When the receipt status is 0, the result should have success=False."""
        w3 = MagicMock()
        w3.eth.gas_price = 100_000_000
        w3.eth.chain_id = 42161
        w3.eth.get_transaction_count.return_value = 0

        account_mock = MagicMock()
        account_mock.address = "0x" + "aa" * 20
        w3.eth.account.from_key.return_value = account_mock

        contract_mock = MagicMock()
        tx_builder = MagicMock()
        tx_builder.build_transaction.return_value = {"raw": "tx_data"}
        contract_mock.functions.executeFlashLoan.return_value = tx_builder
        w3.eth.contract.return_value = contract_mock

        signed_mock = MagicMock()
        signed_mock.raw_transaction = b"\x00" * 32
        w3.eth.account.sign_transaction.return_value = signed_mock
        w3.eth.send_raw_transaction.return_value = b"\x02" * 32

        # Reverted receipt
        receipt_mock = {
            "status": 0,
            "gasUsed": 100_000,
            "logs": [],
        }
        w3.eth.wait_for_transaction_receipt.return_value = receipt_mock

        # Make _decode_revert return a reason
        w3.eth.get_transaction.return_value = {
            "to": "0x" + "11" * 20,
            "from": "0x" + "aa" * 20,
            "input": "0x",
            "value": 0,
            "gas": 500_000,
            "blockNumber": 100,
        }
        w3.eth.call.side_effect = Exception("execution reverted: InsufficientBalanceToRepay")

        settings = _make_settings()
        chain = _make_chain()

        executor = TradeExecutor(w3, settings, chain)
        decision = _make_decision()
        result = executor.execute(decision)

        assert result.success is False
        assert result.error is not None
        assert "InsufficientBalanceToRepay" in result.error

    def test_execute_handles_send_failure(self):
        """If send_raw_transaction raises, the result should capture the error."""
        w3 = MagicMock()
        w3.eth.gas_price = 100_000_000
        w3.eth.chain_id = 42161
        w3.eth.get_transaction_count.return_value = 0

        account_mock = MagicMock()
        account_mock.address = "0x" + "aa" * 20
        w3.eth.account.from_key.return_value = account_mock

        contract_mock = MagicMock()
        tx_builder = MagicMock()
        tx_builder.build_transaction.return_value = {"raw": "tx_data"}
        contract_mock.functions.executeFlashLoan.return_value = tx_builder
        w3.eth.contract.return_value = contract_mock

        signed_mock = MagicMock()
        signed_mock.raw_transaction = b"\x00" * 32
        w3.eth.account.sign_transaction.return_value = signed_mock
        w3.eth.send_raw_transaction.side_effect = Exception("nonce too low")

        settings = _make_settings()
        chain = _make_chain()

        executor = TradeExecutor(w3, settings, chain)
        decision = _make_decision()
        result = executor.execute(decision)

        assert result.success is False
        assert "nonce too low" in result.error
