"""
Configuration module for the DeFi flash loan arbitrage backend.

Loads settings from .env via pydantic-settings, reads chain/token config
from JSON files, and provides typed helpers for the rest of the app.
"""

from __future__ import annotations

import json
import logging
import pathlib
import sys
from dataclasses import dataclass
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings
from web3 import Web3

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resolve project root (two levels up from this file: backend/src/config.py)
# ---------------------------------------------------------------------------
_THIS_DIR = pathlib.Path(__file__).resolve().parent            # backend/src
_BACKEND_DIR = _THIS_DIR.parent                                 # backend/
PROJECT_ROOT = _BACKEND_DIR.parent                              # New_Flashloan/
CONFIG_DIR = PROJECT_ROOT / "config"


# ---------------------------------------------------------------------------
# Token info dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TokenInfo:
    """Describes a single on-chain ERC-20 token."""

    symbol: str
    address: str          # checksummed
    decimals: int
    halal: bool = True


# ---------------------------------------------------------------------------
# Chain config dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ChainConfig:
    """Static, JSON-derived chain configuration."""

    chain_id: int
    chain_name: str
    explorer: str
    # Well-known contract addresses
    aave_v3_pool: str
    uniswap_v3_router: str
    uniswap_v3_quoter: str
    sushiswap_v3_router: str
    sushiswap_v3_quoter: str
    chainlink_eth_usd: str
    chainlink_btc_usd: str
    # Token registry  {symbol -> TokenInfo}
    tokens: dict[str, TokenInfo]


# ---------------------------------------------------------------------------
# pydantic-settings: .env -> typed Python
# ---------------------------------------------------------------------------
class Settings(BaseSettings):
    """
    All runtime settings.  Values are read from environment variables
    (or an ``.env`` file located at the project root).
    """

    # RPC endpoints
    ALCHEMY_ARBITRUM_URL: str = ""
    ALCHEMY_ARBITRUM_WS_URL: str = ""
    ALCHEMY_ARBITRUM_SEPOLIA_URL: str = ""

    # Wallet
    PRIVATE_KEY: str = ""

    # Deployed contract addresses (filled after deployment)
    FLASH_LOAN_ARBITRAGE_ADDRESS: str = ""
    MUDARABAH_POOL_ADDRESS: str = ""
    HALAL_REGISTRY_ADDRESS: str = ""
    PRICE_ORACLE_ADDRESS: str = ""

    # Trading parameters
    MIN_PROFIT_USD: float = 5.0
    SCAN_PAIRS: str = "WETH/USDC,WETH/USDT,WBTC/WETH,ARB/WETH"
    MONITOR_PORT: int = 8080
    CHAIN_CONFIG: str = "arbitrum"  # or "arbitrum-sepolia"

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    # -- validators --------------------------------------------------------

    @field_validator("PRIVATE_KEY")
    @classmethod
    def _validate_private_key(cls, v: str) -> str:
        if not v or v == "0x_YOUR_EXECUTOR_PRIVATE_KEY":
            logger.error(
                "PRIVATE_KEY is not set.  "
                "Set it in .env or as an environment variable."
            )
            sys.exit(1)
        # Normalise: ensure 0x prefix
        if not v.startswith("0x"):
            v = "0x" + v
        if len(v) != 66:
            logger.error("PRIVATE_KEY must be 64 hex chars (with 0x prefix = 66).")
            sys.exit(1)
        return v

    @field_validator("ALCHEMY_ARBITRUM_URL")
    @classmethod
    def _validate_rpc_url(cls, v: str) -> str:
        if not v or "YOUR_KEY" in v:
            logger.error(
                "ALCHEMY_ARBITRUM_URL is not configured.  "
                "Set it in .env or as an environment variable."
            )
            sys.exit(1)
        return v

    # -- convenience methods -----------------------------------------------

    def get_scan_pairs(self) -> list[tuple[str, str]]:
        """Parse ``SCAN_PAIRS`` CSV into a list of (tokenA, tokenB) tuples."""
        pairs: list[tuple[str, str]] = []
        for raw in self.SCAN_PAIRS.split(","):
            parts = raw.strip().split("/")
            if len(parts) == 2:
                pairs.append((parts[0].strip(), parts[1].strip()))
        return pairs

    def get_web3(self) -> Web3:
        """Return an HTTP-connected Web3 instance for Arbitrum."""
        w3 = Web3(Web3.HTTPProvider(self.ALCHEMY_ARBITRUM_URL))
        if not w3.is_connected():
            logger.error("Cannot connect to Arbitrum RPC at %s", self.ALCHEMY_ARBITRUM_URL)
            sys.exit(1)
        return w3


# ---------------------------------------------------------------------------
# JSON loaders
# ---------------------------------------------------------------------------

def _load_json(path: pathlib.Path) -> dict[str, Any]:
    """Read and parse a JSON config file, exit on failure."""
    if not path.exists():
        logger.error("Config file not found: %s", path)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_chain_config(network: str = "arbitrum") -> ChainConfig:
    """
    Load ``config/<network>.json`` and ``config/tokens.json`` and return a
    fully-typed :class:`ChainConfig`.
    """
    arb = _load_json(CONFIG_DIR / f"{network}.json")
    tokens_raw = _load_json(CONFIG_DIR / "tokens.json")

    # Build token registry from tokens.json -> "arbitrum" section
    tokens: dict[str, TokenInfo] = {}
    arb_tokens = tokens_raw.get("arbitrum", {})
    for symbol, info in arb_tokens.items():
        tokens[symbol] = TokenInfo(
            symbol=symbol,
            address=Web3.to_checksum_address(info["address"]),
            decimals=info["decimals"],
            halal=info.get("halal", True),
        )

    contracts = arb.get("contracts", {})

    _zero = "0x" + "0" * 40

    return ChainConfig(
        chain_id=arb["chain_id"],
        chain_name=arb["chain_name"],
        explorer=arb["explorer"],
        aave_v3_pool=Web3.to_checksum_address(contracts["aave_v3_pool"]),
        uniswap_v3_router=Web3.to_checksum_address(contracts["uniswap_v3_router"]),
        uniswap_v3_quoter=Web3.to_checksum_address(contracts["uniswap_v3_quoter"]),
        sushiswap_v3_router=Web3.to_checksum_address(contracts.get("sushiswap_v3_router", _zero)),
        sushiswap_v3_quoter=Web3.to_checksum_address(contracts.get("sushiswap_v3_quoter", _zero)),
        chainlink_eth_usd=Web3.to_checksum_address(contracts.get("chainlink_eth_usd", _zero)),
        chainlink_btc_usd=Web3.to_checksum_address(contracts.get("chainlink_btc_usd", _zero)),
        tokens=tokens,
    )
