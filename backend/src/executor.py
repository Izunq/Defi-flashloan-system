"""
Trade executor -- signs and sends flash-loan arbitrage transactions.

Builds calldata for ``FlashLoanArbitrage.executeFlashLoan``, manages the
nonce, and waits for transaction receipts.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from web3 import Web3
from web3.contract import Contract
from web3.types import TxReceipt

from .config import Settings, ChainConfig
from .evaluator import TradeDecision

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Minimal ABI for FlashLoanArbitrage
# ---------------------------------------------------------------------------

FLASH_LOAN_ARBITRAGE_ABI = [
    # executeFlashLoan(address asset, uint256 amount, bytes params)
    {
        "inputs": [
            {"internalType": "address", "name": "asset", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "bytes", "name": "params", "type": "bytes"},
        ],
        "name": "executeFlashLoan",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # FlashLoanExecuted(address indexed asset, uint256 amount, uint256 profit)
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "asset", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "profit", "type": "uint256"},
        ],
        "name": "FlashLoanExecuted",
        "type": "event",
    },
]

# ---------------------------------------------------------------------------
# DEX name -> Arbitrum router address mapping
# ---------------------------------------------------------------------------


def _router_address(chain: ChainConfig, dex_name: str) -> str:
    """Resolve a human-friendly DEX label to its on-chain router address."""
    if dex_name == "uniswap_v3":
        return chain.uniswap_v3_router
    if dex_name == "sushiswap":
        return chain.sushiswap_v3_router
    raise ValueError(f"Unknown DEX: {dex_name}")


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class TradeResult:
    """Outcome of a submitted flash-loan transaction."""

    tx_hash: str
    success: bool
    profit_actual: int       # profit in asset-token smallest units
    gas_used: int
    gas_price: int
    timestamp: float
    error: str | None = None


# ---------------------------------------------------------------------------
# TradeExecutor
# ---------------------------------------------------------------------------

class TradeExecutor:
    """
    Builds, signs, and sends ``executeFlashLoan`` transactions.

    Maintains a local nonce counter to avoid conflicts when submitting
    multiple transactions in quick succession.
    """

    def __init__(self, w3: Web3, settings: Settings, chain: ChainConfig) -> None:
        self.w3 = w3
        self.settings = settings
        self.chain = chain

        if not settings.FLASH_LOAN_ARBITRAGE_ADDRESS:
            raise ValueError(
                "FLASH_LOAN_ARBITRAGE_ADDRESS is not set.  "
                "Deploy the contract first and update .env."
            )

        self.contract: Contract = w3.eth.contract(
            address=Web3.to_checksum_address(settings.FLASH_LOAN_ARBITRAGE_ADDRESS),
            abi=FLASH_LOAN_ARBITRAGE_ABI,
        )

        self.account = w3.eth.account.from_key(settings.PRIVATE_KEY)
        self._nonce: int | None = None

    # ----- nonce management -----------------------------------------------

    def _next_nonce(self) -> int:
        """Return the next nonce, refreshing from on-chain if needed."""
        if self._nonce is None:
            self._nonce = self.w3.eth.get_transaction_count(self.account.address)
        else:
            self._nonce += 1
        return self._nonce

    def _reset_nonce(self) -> None:
        """Force a nonce refresh from the network."""
        self._nonce = None

    # ----- calldata encoding ----------------------------------------------

    @staticmethod
    def encode_swap_route(
        dex_a: str,
        dex_b: str,
        token_out: str,
        fee_a: int,
        fee_b: int,
        amount_out_min_a: int,
        amount_out_min_b: int,
    ) -> bytes:
        """
        ABI-encode the ``SwapRoute`` struct that the contract decodes in
        ``executeOperation``.

        Solidity struct layout (abi.decode):
            (address dexA, address dexB, address tokenOut,
             uint24 feeA, uint24 feeB,
             uint256 amountOutMinA, uint256 amountOutMinB)
        """
        return Web3().codec.encode(
            ["address", "address", "address", "uint24", "uint24", "uint256", "uint256"],
            [
                Web3.to_checksum_address(dex_a),
                Web3.to_checksum_address(dex_b),
                Web3.to_checksum_address(token_out),
                fee_a,
                fee_b,
                amount_out_min_a,
                amount_out_min_b,
            ],
        )

    # ----- execution ------------------------------------------------------

    def execute(self, decision: TradeDecision) -> TradeResult:
        """
        Build, sign, send, and await the flash-loan transaction.

        Returns a :class:`TradeResult` regardless of on-chain success or
        failure so the caller can always log the outcome.
        """
        opp = decision.opportunity
        now = time.time()

        try:
            # -- resolve router addresses ----------------------------------
            router_a = _router_address(self.chain, opp.dex_a)
            router_b = _router_address(self.chain, opp.dex_b)

            # -- compute minimum output with slippage tolerance (2 %) ------
            amount_out_min_a = opp.expected_out_a * 98 // 100
            amount_out_min_b = opp.expected_out_b * 98 // 100

            # -- encode params ---------------------------------------------
            params = self.encode_swap_route(
                dex_a=router_a,
                dex_b=router_b,
                token_out=opp.token_out,
                fee_a=opp.fee_tier_a if opp.fee_tier_a else 3000,
                fee_b=opp.fee_tier_b if opp.fee_tier_b else 3000,
                amount_out_min_a=amount_out_min_a,
                amount_out_min_b=amount_out_min_b,
            )

            # -- build transaction -----------------------------------------
            gas_price = self.w3.eth.gas_price
            nonce = self._next_nonce()

            tx = self.contract.functions.executeFlashLoan(
                Web3.to_checksum_address(opp.token_in),
                opp.amount_in,
                params,
            ).build_transaction(
                {
                    "from": self.account.address,
                    "nonce": nonce,
                    "gas": decision.gas_estimate,
                    "gasPrice": gas_price,
                    "chainId": self.chain.chain_id,
                }
            )

            # -- sign & send -----------------------------------------------
            signed = self.w3.eth.account.sign_transaction(tx, self.settings.PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            logger.info("TX sent: %s", tx_hash.hex())

            # -- wait for receipt ------------------------------------------
            receipt: TxReceipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=60
            )

            success = receipt["status"] == 1
            profit_actual = 0

            if success:
                # Try to decode FlashLoanExecuted event for actual profit
                profit_actual = self._decode_profit(receipt)
                logger.info(
                    "TX confirmed  hash=%s  profit=%d  gas=%d",
                    tx_hash.hex(),
                    profit_actual,
                    receipt["gasUsed"],
                )
            else:
                revert_reason = self._decode_revert(tx_hash)
                logger.warning(
                    "TX reverted  hash=%s  reason=%s", tx_hash.hex(), revert_reason
                )
                return TradeResult(
                    tx_hash=tx_hash.hex(),
                    success=False,
                    profit_actual=0,
                    gas_used=receipt["gasUsed"],
                    gas_price=gas_price,
                    timestamp=now,
                    error=revert_reason,
                )

            return TradeResult(
                tx_hash=tx_hash.hex(),
                success=True,
                profit_actual=profit_actual,
                gas_used=receipt["gasUsed"],
                gas_price=gas_price,
                timestamp=now,
            )

        except Exception as exc:
            logger.exception("Execution failed: %s", exc)
            self._reset_nonce()
            return TradeResult(
                tx_hash="",
                success=False,
                profit_actual=0,
                gas_used=0,
                gas_price=0,
                timestamp=now,
                error=str(exc),
            )

    # ----- receipt helpers ------------------------------------------------

    def _decode_profit(self, receipt: TxReceipt) -> int:
        """Extract the profit value from a FlashLoanExecuted event log."""
        try:
            logs = self.contract.events.FlashLoanExecuted().process_receipt(receipt)
            if logs:
                return logs[0]["args"]["profit"]
        except Exception:
            pass
        return 0

    def _decode_revert(self, tx_hash: bytes) -> str:
        """Attempt to extract the revert reason from a failed transaction."""
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            # Replay the call to surface the revert reason
            self.w3.eth.call(
                {
                    "to": tx["to"],
                    "from": tx["from"],
                    "data": tx["input"],
                    "value": tx["value"],
                    "gas": tx["gas"],
                },
                tx["blockNumber"],
            )
        except Exception as exc:
            # The exception message usually contains the revert string
            return str(exc)
        return "unknown revert"
