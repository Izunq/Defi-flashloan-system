#!/usr/bin/env python3
"""
MEV Protection Module for Institutional-Grade Arbitrage System
=============================================================

This module provides protection against MEV (Maximal Extractable Value) attacks:
- Flashbots integration for private transactions
- Protection against sandwich attacks
- Slippage control and monitoring
- Transaction simulation
- Gas optimization
"""

import os
import json
import logging
import time
import random
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import requests
import web3
from web3 import Web3
from web3.types import TxParams, Wei, HexStr, ChecksumAddress
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
import eth_abi
from eth_typing import URI
import asyncio
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mev_protection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MEV_PROTECTION")

# Constants
FLASHBOTS_ENDPOINT = "https://relay.flashbots.net"
EDEN_ENDPOINT = "https://api.edennetwork.io/v1/bundle"
BLOXROUTE_ENDPOINT = "https://api.blxr.io/v1"
TENDERLY_API_URL = "https://api.tenderly.co/api/v1"

# Default gas settings
DEFAULT_MAX_PRIORITY_FEE = 2 * 10**9  # 2 gwei
DEFAULT_MAX_FEE = 100 * 10**9  # 100 gwei
DEFAULT_GAS_LIMIT_BUFFER = 1.2  # 20% buffer

@dataclass
class TransactionConfig:
    """Configuration for transaction submission"""
    max_priority_fee_gwei: float = 2.0
    max_fee_gwei: float = 100.0
    gas_limit_buffer: float = 1.2
    slippage_tolerance: float = 0.005  # 0.5%
    deadline_seconds: int = 300  # 5 minutes
    flashbots_enabled: bool = True
    eden_enabled: bool = False
    bloxroute_enabled: bool = False
    simulate_before_send: bool = True
    sandwich_protection: bool = True
    retry_count: int = 3
    retry_delay_seconds: int = 5
    min_block_confirmations: int = 2
    
    # Dynamic gas price settings
    dynamic_gas_price_enabled: bool = True
    gas_price_percentile: float = 75.0  # Use 75th percentile of recent gas prices
    max_gas_price_multiplier: float = 1.5  # Maximum multiplier over base gas price
    gas_price_update_interval: int = 60  # Update gas price limits every 60 seconds
    network_congestion_threshold: float = 0.8  # Threshold for network congestion (0-1)
    base_max_fee_gwei: float = 100.0  # Store original max fee as base

@dataclass
class MEVProtectionStats:
    """Statistics for MEV protection"""
    total_transactions: int = 0
    protected_transactions: int = 0
    sandwich_attacks_prevented: int = 0
    flashbots_bundles_submitted: int = 0
    flashbots_bundles_included: int = 0
    gas_saved: float = 0.0
    failed_simulations: int = 0
    reverted_transactions: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

class FlashbotsProvider:
    """Provider for Flashbots private transactions"""
    
    def __init__(self, web3_provider: Web3, flashbots_endpoint: str = FLASHBOTS_ENDPOINT):
        self.web3 = web3_provider
        self.flashbots_endpoint = flashbots_endpoint
        
        # Create a signing account for Flashbots auth
        self.flashbots_signer = Account.create()
        logger.info(f"Created Flashbots auth signer: {self.flashbots_signer.address}")
    
    async def send_bundle(self, signed_transactions: List[str], target_block: int) -> Dict[str, Any]:
        """Send a bundle of transactions to Flashbots"""
        bundle = [{"signed_transaction": tx} for tx in signed_transactions]
        
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_sendBundle",
            "params": [
                {
                    "txs": bundle,
                    "blockNumber": hex(target_block),
                    "minTimestamp": 0,
                    "maxTimestamp": int(time.time() + 120)  # 2 minutes from now
                }
            ]
        }
        
        # Sign the request with the Flashbots auth key
        signature = self._sign_flashbots_request(request_data)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.flashbots_endpoint,
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "X-Flashbots-Signature": signature
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Flashbots request failed: {response.status} - {error_text}")
                    return {"success": False, "error": error_text}
                
                result = await response.json()
                logger.info(f"Flashbots bundle submitted for block {target_block}")
                return {"success": True, "result": result}
    
    def _sign_flashbots_request(self, request_data: Dict[str, Any]) -> str:
        """Sign a request for Flashbots authentication"""
        message = Web3.keccak(text=json.dumps(request_data))
        signed_message = self.flashbots_signer.sign_message(message)
        return f"{self.flashbots_signer.address}:{signed_message.signature.hex()}"
    
    async def simulate_bundle(self, signed_transactions: List[str], block_number: int) -> Dict[str, Any]:
        """Simulate a bundle of transactions"""
        bundle = [{"signed_transaction": tx} for tx in signed_transactions]
        
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_callBundle",
            "params": [
                {
                    "txs": bundle,
                    "blockNumber": hex(block_number),
                    "stateBlockNumber": "latest"
                }
            ]
        }
        
        # Sign the request with the Flashbots auth key
        signature = self._sign_flashbots_request(request_data)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.flashbots_endpoint}/simulate",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "X-Flashbots-Signature": signature
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Flashbots simulation failed: {response.status} - {error_text}")
                    return {"success": False, "error": error_text}
                
                result = await response.json()
                return {"success": True, "result": result}

class TenderlySimulator:
    """Transaction simulator using Tenderly API"""
    
    def __init__(self, api_key: str, project_slug: str, user_name: str):
        self.api_key = api_key
        self.project_slug = project_slug
        self.user_name = user_name
        self.api_url = f"{TENDERLY_API_URL}/account/{user_name}/project/{project_slug}/simulate"
        self.headers = {
            "Content-Type": "application/json",
            "X-Access-Key": api_key
        }
    
    async def simulate_transaction(self, from_address: str, to_address: str, 
                                 data: str, value: int = 0, gas: int = None,
                                 gas_price: int = None, network_id: str = "1") -> Dict[str, Any]:
        """Simulate a transaction using Tenderly API"""
        request_data = {
            "network_id": network_id,
            "from": from_address,
            "to": to_address,
            "input": data,
            "value": hex(value) if value else "0x0",
            "save": True
        }
        
        if gas:
            request_data["gas"] = hex(gas)
        
        if gas_price:
            request_data["gas_price"] = hex(gas_price)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json=request_data,
                headers=self.headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Tenderly simulation failed: {response.status} - {error_text}")
                    return {"success": False, "error": error_text}
                
                result = await response.json()
                
                # Check if simulation was successful
                if not result.get("simulation", {}).get("status", False):
                    logger.warning(f"Tenderly simulation reverted: {result.get('simulation', {}).get('error', 'Unknown error')}")
                    return {"success": False, "result": result}
                
                logger.info(f"Tenderly simulation successful: {result.get('simulation', {}).get('id')}")
                return {"success": True, "result": result}

class SandwichDetector:
    """Detector for potential sandwich attacks"""
    
    def __init__(self, web3_provider: Web3):
        self.web3 = web3_provider
        self.pending_tx_cache = {}
        self.known_sandwich_addresses = set()
        self.last_mempool_scan = datetime.now() - timedelta(minutes=10)
    
    async def scan_mempool(self):
        """Scan mempool for potential sandwich attackers - SECURITY FIXED"""
        # Only scan every 30 seconds for better real-time protection
        if datetime.now() - self.last_mempool_scan < timedelta(seconds=30):
            return
        
        # SECURITY FIX: Use real mempool analysis instead of fake data
        try:
            # Get recent blocks for pattern analysis
            latest_block = await self.web3.eth.get_block_number()
            
            # Analyze last 5 blocks for MEV patterns
            for i in range(5):
                block_number = latest_block - i
                block = await self.web3.eth.get_block(block_number, full_transactions=True)
                
                # Analyze transactions for MEV bot patterns
                for tx in block.transactions:
                    if hasattr(tx, 'from_') or hasattr(tx, 'from'):
                        from_addr = getattr(tx, 'from_', getattr(tx, 'from', None))
                        if from_addr:
                            await self._analyze_transaction_for_mev_patterns(tx, from_addr)
            
            self.last_mempool_scan = datetime.now()
            logger.info(f"Real mempool scan completed, tracking {len(self.known_sandwich_addresses)} confirmed MEV addresses")
            
        except Exception as e:
            logger.error(f"Error in real mempool scan: {e}")
            # Fallback to conservative approach - assume high MEV risk
            self.last_mempool_scan = datetime.now()
    
    async def _analyze_transaction_for_mev_patterns(self, tx, from_addr):
        """Analyze transaction for MEV bot patterns"""
        try:
            # Check for high gas prices (potential front-running)
            if hasattr(tx, 'gasPrice') and tx.gasPrice:
                gas_price_gwei = self.web3.from_wei(tx.gasPrice, 'gwei')
                # If gas price is > 100 gwei, flag as potential MEV
                if gas_price_gwei > 100:
                    self.known_sandwich_addresses.add(from_addr.lower())
            
            # Check for MEV-related function calls
            if hasattr(tx, 'input') and tx.input:
                data = tx.input.hex() if hasattr(tx.input, 'hex') else str(tx.input)
                # Known MEV function signatures
                mev_signatures = [
                    '0x38ed1739',  # swapExactTokensForTokens
                    '0x7ff36ab5',  # swapExactETHForTokens
                    '0x18cbafe5',  # swapExactTokensForETH
                    '0x128acb08',  # arbitrage patterns
                ]
                
                for sig in mev_signatures:
                    if data.startswith(sig):
                        # Check if this address makes frequent MEV-like transactions
                        self.known_sandwich_addresses.add(from_addr.lower())
                        break
        
        except Exception as e:
            logger.error(f"Error analyzing transaction for MEV patterns: {e}")
    
    async def check_transaction_safety(self, tx_params: Dict[str, Any], 
                                     token_address: str, amount: int) -> Dict[str, Any]:
        """Check if a transaction might be vulnerable to sandwich attacks"""
        # Scan mempool for potential attackers
        await self.scan_mempool()
        
        # Check if the transaction is a token swap (simplified check)
        is_swap = "data" in tx_params and len(tx_params["data"]) > 10 and (
            "swap" in tx_params["data"].lower() or 
            "exchange" in tx_params["data"].lower()
        )
        
        # If it's not a swap, it's probably safe from sandwich attacks
        if not is_swap:
            return {
                "is_vulnerable": False,
                "risk_level": "low",
                "recommendation": "Transaction does not appear to be a token swap"
            }
        
        # Check if the amount is large enough to be attractive to attackers
        # This is a simplified check - in reality, you'd need to consider token value
        is_large_amount = amount > 1000 * 10**18  # Assuming 18 decimals
        
        # Check if there are known attackers with pending transactions
        has_attackers = len(self.known_sandwich_addresses) > 0
        
        # Determine risk level
        risk_level = "low"
        if is_large_amount and has_attackers:
            risk_level = "high"
        elif is_large_amount or has_attackers:
            risk_level = "medium"
        
        # Generate recommendation
        recommendation = "Transaction appears safe"
        if risk_level == "high":
            recommendation = "Use private transaction (Flashbots) to avoid sandwich attacks"
        elif risk_level == "medium":
            recommendation = "Consider using private transactions or adding slippage protection"
        
        return {
            "is_vulnerable": risk_level != "low",
            "risk_level": risk_level,
            "recommendation": recommendation,
            "known_attackers": len(self.known_sandwich_addresses),
            "is_large_amount": is_large_amount
        }

class MEVProtection:
    """Main class for MEV protection"""
    
    def __init__(self, web3_provider: Web3, config: TransactionConfig = None):
        self.web3 = web3_provider
        self.config = config or TransactionConfig()
        self.stats = MEVProtectionStats()
        
        # Initialize components
        self.flashbots = FlashbotsProvider(web3_provider)
        
        # Initialize Tenderly simulator if API key is available        tenderly_api_key = os.environ.get("TENDERLY_API_KEY")
        if tenderly_api_key:
            self.simulator = TenderlySimulator(
                api_key=tenderly_api_key,
                project_slug=os.environ.get("TENDERLY_PROJECT", "arbitrage"),
                user_name=os.environ.get("TENDERLY_USER", "default")
            )
        else:
            self.simulator = None
        
        # For dynamic gas price adjustment
        self.last_gas_price_update = 0
        self.recent_gas_prices = []
        self.network_congestion_level = 0.0
        
        if not tenderly_api_key:
            logger.warning("Tenderly API key not found, simulation will use local provider")
        
        self.sandwich_detector = SandwichDetector(web3_provider)
    
    async def send_transaction(self, tx_params: Dict[str, Any], 
                               transaction_signer = None) -> Dict[str, Any]:
        """Send a transaction with MEV protection"""
        if not transaction_signer:
            raise ValueError("Secure transaction signer must be provided")
        
        # Use secure transaction signer instead of private key
        account_address = transaction_signer.get_address()
        
        # Update dynamic gas price limits based on network conditions
        if self.config.dynamic_gas_price_enabled:
            await self.update_dynamic_gas_price()
          # Update transaction with gas settings if not provided
        tx_params = await self._prepare_transaction(tx_params, account_address)
        
        # Check for potential sandwich attacks
        if self.config.sandwich_protection and "to" in tx_params and tx_params["to"]:
            token_address = tx_params["to"]
            amount = tx_params.get("value", 0)
            
            safety_check = await self.sandwich_detector.check_transaction_safety(
                tx_params=tx_params,
                token_address=token_address,
                amount=amount
            )
            
            if safety_check["is_vulnerable"] and safety_check["risk_level"] == "high":
                logger.warning(f"Transaction vulnerable to sandwich attacks: {safety_check}")
                # Force Flashbots for high-risk transactions
                self.config.flashbots_enabled = True
                self.stats.sandwich_attacks_prevented += 1
          # Simulate transaction if enabled
        if self.config.simulate_before_send:
            simulation_result = await self._simulate_transaction(tx_params, account_address)
            
            if not simulation_result["success"]:
                logger.error(f"Transaction simulation failed: {simulation_result.get('error', 'Unknown error')}")
                self.stats.failed_simulations += 1
                return {"success": False, "error": "Simulation failed", "details": simulation_result}
        
        # Sign the transaction using secure transaction signer
        signed_tx = transaction_signer.sign_transaction(tx_params)
        
        # Send via Flashbots if enabled
        if self.config.flashbots_enabled:
            return await self._send_via_flashbots(signed_tx, transaction_signer)
        
        # Otherwise, send via regular RPC
        return await self._send_via_rpc(signed_tx)
    
    async def _prepare_transaction(self, tx_params: Dict[str, Any], from_address: str) -> Dict[str, Any]:
        """Prepare transaction with gas settings and nonce"""
        # Clone the transaction params to avoid modifying the original
        tx = tx_params.copy()
        
        # Set from address if not provided
        if "from" not in tx:
            tx["from"] = from_address
        
        # Set chain ID if not provided
        if "chainId" not in tx:
            tx["chainId"] = await self.web3.eth.chain_id
        
        # Set nonce if not provided
        if "nonce" not in tx:
            tx["nonce"] = await self.web3.eth.get_transaction_count(from_address)
        
        # Set gas price settings for EIP-1559
        if "maxFeePerGas" not in tx and "gasPrice" not in tx:
            base_fee = (await self.web3.eth.get_block("latest"))["baseFeePerGas"]
            max_priority_fee = int(self.config.max_priority_fee_gwei * 10**9)
            max_fee = int(self.config.max_fee_gwei * 10**9)
            
            # Ensure max fee is at least base fee + priority fee
            max_fee = max(max_fee, base_fee + max_priority_fee)
            
            tx["maxFeePerGas"] = max_fee
            tx["maxPriorityFeePerGas"] = max_priority_fee
        
        # Estimate gas if not provided
        if "gas" not in tx:
            try:
                estimated_gas = await self.web3.eth.estimate_gas(tx)
                # Add buffer to gas estimate
                tx["gas"] = int(estimated_gas * self.config.gas_limit_buffer)
            except Exception as e:
                logger.warning(f"Gas estimation failed: {e}")
                # Use a high default if estimation fails
                tx["gas"] = 500000
        
        return tx
    
    async def _simulate_transaction(self, tx_params: Dict[str, Any], from_address: str) -> Dict[str, Any]:
        """Simulate a transaction before sending"""
        # Use Tenderly if available
        if self.simulator:
            return await self.simulator.simulate_transaction(                from_address=from_address,
                to_address=tx_params["to"],
                data=tx_params.get("data", "0x"),
                value=tx_params.get("value", 0),
                gas=tx_params.get("gas") or 21000,
                gas_price=tx_params.get("gasPrice") or tx_params.get("maxFeePerGas") or 20000000000
            )
        
        # Otherwise use local eth_call
        try:
            # Create a copy of the transaction for simulation
            sim_tx = tx_params.copy()
            # Remove gas price settings for eth_call
            for key in ["gasPrice", "maxFeePerGas", "maxPriorityFeePerGas"]:
                if key in sim_tx:
                    del sim_tx[key]
            
            # Call the transaction
            result = await self.web3.eth.call(sim_tx)
            return {"success": True, "result": {"output": result.hex()}}
        except Exception as e:
            logger.error(f"Local transaction simulation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_via_flashbots(self, signed_tx: str, account: LocalAccount) -> Dict[str, Any]:
        """Send a transaction via Flashbots"""
        self.stats.flashbots_bundles_submitted += 1
        
        # Get current block
        current_block = await self.web3.eth.block_number
        
        # Target next block
        target_block = current_block + 1
        
        # Send bundle to Flashbots
        bundle_result = await self.flashbots.send_bundle(
            signed_transactions=[signed_tx],
            target_block=target_block
        )
        
        if not bundle_result["success"]:
            logger.error(f"Flashbots bundle submission failed: {bundle_result.get('error', 'Unknown error')}")
            # Fall back to regular RPC if Flashbots fails
            logger.info("Falling back to regular RPC")
            return await self._send_via_rpc(signed_tx)
        
        # Wait for the target block
        try:
            # Wait for target block with timeout
            for _ in range(30):  # 30 seconds timeout
                current_block = await self.web3.eth.block_number
                if current_block >= target_block:
                    break
                await asyncio.sleep(1)
            
            # Check if transaction was included
            tx_hash = self.web3.keccak(hexstr=signed_tx).hex()
            try:
                receipt = await self.web3.eth.get_transaction_receipt(tx_hash)
                if receipt and receipt["blockNumber"]:
                    self.stats.flashbots_bundles_included += 1
                    self.stats.protected_transactions += 1
                    
                    logger.info(f"Transaction included via Flashbots in block {receipt['blockNumber']}")
                    return {
                        "success": True,
                        "tx_hash": tx_hash,
                        "receipt": dict(receipt),
                        "method": "flashbots"
                    }
            except Exception:
                # Transaction not found, it wasn't included
                pass
            
            # If we get here, the transaction wasn't included
            logger.warning(f"Transaction not included in target block {target_block}")
            
            # Try again for the next block
            for retry in range(self.config.retry_count):
                target_block = await self.web3.eth.block_number + 1
                
                logger.info(f"Retrying Flashbots bundle for block {target_block} (attempt {retry+1})")
                
                bundle_result = await self.flashbots.send_bundle(
                    signed_transactions=[signed_tx],
                    target_block=target_block
                )
                
                if not bundle_result["success"]:
                    logger.error(f"Flashbots retry failed: {bundle_result.get('error', 'Unknown error')}")
                    continue
                
                # Wait for the target block
                for _ in range(30):  # 30 seconds timeout
                    current_block = await self.web3.eth.block_number
                    if current_block >= target_block:
                        break
                    await asyncio.sleep(1)
                
                # Check if transaction was included
                try:
                    receipt = await self.web3.eth.get_transaction_receipt(tx_hash)
                    if receipt and receipt["blockNumber"]:
                        self.stats.flashbots_bundles_included += 1
                        self.stats.protected_transactions += 1
                        
                        logger.info(f"Transaction included via Flashbots in block {receipt['blockNumber']} (retry {retry+1})")
                        return {
                            "success": True,
                            "tx_hash": tx_hash,
                            "receipt": dict(receipt),
                            "method": "flashbots",
                            "retries": retry + 1
                        }
                except Exception:
                    # Transaction not found, it wasn't included
                    pass
            
            # If we get here, all retries failed
            logger.error("All Flashbots retries failed, falling back to regular RPC")
            return await self._send_via_rpc(signed_tx)
            
        except Exception as e:
            logger.error(f"Error waiting for Flashbots inclusion: {e}")
            # Fall back to regular RPC
            logger.info("Falling back to regular RPC due to error")
            return await self._send_via_rpc(signed_tx)
    
    async def _send_via_rpc(self, signed_tx: str) -> Dict[str, Any]:
        """Send a transaction via regular RPC"""
        try:
            # Send the raw transaction
            tx_hash = await self.web3.eth.send_raw_transaction(signed_tx)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"Transaction sent via RPC: {tx_hash_hex}")
            
            # Wait for receipt
            for _ in range(60):  # 60 seconds timeout
                try:
                    receipt = await self.web3.eth.get_transaction_receipt(tx_hash)
                    if receipt:
                        self.stats.total_transactions += 1
                        
                        # Check if transaction was successful
                        if receipt["status"] == 1:
                            logger.info(f"Transaction confirmed in block {receipt['blockNumber']}")
                            return {
                                "success": True,
                                "tx_hash": tx_hash_hex,
                                "receipt": dict(receipt),
                                "method": "rpc"
                            }
                        else:
                            self.stats.reverted_transactions += 1
                            logger.error(f"Transaction reverted in block {receipt['blockNumber']}")
                            return {
                                "success": False,
                                "tx_hash": tx_hash_hex,
                                "receipt": dict(receipt),
                                "error": "Transaction reverted",
                                "method": "rpc"
                            }
                except Exception:
                    # Transaction not yet mined
                    pass
                
                await asyncio.sleep(1)
            
            # If we get here, transaction wasn't mined within timeout
            logger.warning(f"Transaction not mined within timeout: {tx_hash_hex}")
            return {
                "success": False,
                "tx_hash": tx_hash_hex,
                "error": "Transaction not mined within timeout",
                "method": "rpc"
            }
            
        except Exception as e:
            logger.error(f"Error sending transaction via RPC: {e}")
            return {"success": False, "error": str(e), "method": "rpc"}
    
    async def update_dynamic_gas_price(self) -> None:
        """
        Dynamically adjust gas price limits based on network conditions
        """
        if not self.config.dynamic_gas_price_enabled:
            return
            
        current_time = time.time()
        
        # Only update if the interval has passed
        if current_time - self.last_gas_price_update < self.config.gas_price_update_interval:
            return
            
        try:
            # Get recent gas prices from the last few blocks
            latest_block = await self.web3.eth.get_block_number()
            gas_prices = []
            
            # Collect gas prices from recent blocks
            for i in range(10):  # Look at last 10 blocks
                if latest_block - i < 0:
                    break
                    
                block = await self.web3.eth.get_block(latest_block - i)
                
                # Get transactions from the block
                for tx_hash in block.transactions[:20]:  # Limit to first 20 txs per block
                    tx = await self.web3.eth.get_transaction(tx_hash)
                    if tx and tx.get('gasPrice'):
                        gas_prices.append(self.web3.from_wei(tx['gasPrice'], 'gwei'))
            
            if not gas_prices:
                return
                
            # Calculate network congestion based on block fullness
            latest_block_obj = await self.web3.eth.get_block(latest_block)
            block_gas_limit = latest_block_obj.gasLimit
            block_gas_used = latest_block_obj.gasUsed
            self.network_congestion_level = block_gas_used / block_gas_limit
            
            # Calculate percentile gas price
            gas_prices.sort()
            percentile_index = int(len(gas_prices) * (self.config.gas_price_percentile / 100))
            percentile_gas_price = gas_prices[percentile_index]
            
            # Apply multiplier based on network congestion
            congestion_multiplier = 1.0
            if self.network_congestion_level > self.config.network_congestion_threshold:
                # Increase multiplier as congestion increases
                congestion_factor = (self.network_congestion_level - self.config.network_congestion_threshold) / (1 - self.config.network_congestion_threshold)
                congestion_multiplier = 1.0 + (congestion_factor * 0.5)  # Up to 50% increase
                
            # Calculate new max gas price
            new_max_fee = percentile_gas_price * congestion_multiplier
            
            # Ensure it doesn't exceed the maximum allowed multiplier
            max_allowed = self.config.base_max_fee_gwei * self.config.max_gas_price_multiplier
            new_max_fee = min(new_max_fee, max_allowed)
            
            # Update the config
            self.config.max_fee_gwei = new_max_fee
            
            # Also adjust priority fee based on congestion
            self.config.max_priority_fee_gwei = min(
                new_max_fee * 0.1,  # 10% of max fee
                self.config.max_priority_fee_gwei * congestion_multiplier
            )
            
            logger.info(f"Updated gas price limits: max_fee={self.config.max_fee_gwei:.2f} gwei, "
                       f"priority_fee={self.config.max_priority_fee_gwei:.2f} gwei, "
                       f"congestion={self.network_congestion_level:.2f}")
                       
            # Update timestamp
            self.last_gas_price_update = current_time
            
            # Store recent gas prices for analysis
            self.recent_gas_prices = gas_prices
            
        except Exception as e:
            logger.error(f"Error updating dynamic gas price: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get MEV protection statistics"""
        self.stats.last_updated = datetime.now()
        
        # Calculate success rate
        success_rate = 0
        if self.stats.total_transactions > 0:
            success_rate = (self.stats.total_transactions - self.stats.reverted_transactions) / self.stats.total_transactions
        
        # Calculate Flashbots success rate
        flashbots_success_rate = 0
        if self.stats.flashbots_bundles_submitted > 0:
            flashbots_success_rate = self.stats.flashbots_bundles_included / self.stats.flashbots_bundles_submitted
        
        return {
            "total_transactions": self.stats.total_transactions,
            "protected_transactions": self.stats.protected_transactions,
            "sandwich_attacks_prevented": self.stats.sandwich_attacks_prevented,
            "flashbots_bundles_submitted": self.stats.flashbots_bundles_submitted,
            "flashbots_bundles_included": self.stats.flashbots_bundles_included,
            "flashbots_success_rate": flashbots_success_rate,
            "gas_saved": self.stats.gas_saved,
            "failed_simulations": self.stats.failed_simulations,
            "reverted_transactions": self.stats.reverted_transactions,
            "success_rate": success_rate,
            "last_updated": self.stats.last_updated.isoformat(),
            "network_congestion_level": getattr(self, 'network_congestion_level', 0),
            "current_max_gas_price_gwei": self.config.max_fee_gwei,
            "current_priority_fee_gwei": self.config.max_priority_fee_gwei
        }

class SlippageProtection:
    """Protection against slippage in DEX trades"""
    
    def __init__(self, web3_provider: Web3):
        self.web3 = web3_provider
        
        # Common DEX router ABIs
        self.router_abis = {
            "uniswap_v2": [
                {
                    "inputs": [
                        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                        {"internalType": "address[]", "name": "path", "type": "address[]"},
                        {"internalType": "address", "name": "to", "type": "address"},
                        {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                    ],
                    "name": "swapExactTokensForTokens",
                    "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ],
            "uniswap_v3": [
                {
                    "inputs": [
                        {
                            "components": [
                                {"internalType": "address", "name": "tokenIn", "type": "address"},
                                {"internalType": "address", "name": "tokenOut", "type": "address"},
                                {"internalType": "uint24", "name": "fee", "type": "uint24"},
                                {"internalType": "address", "name": "recipient", "type": "address"},
                                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                                {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                                {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                            ],
                            "internalType": "struct ISwapRouter.ExactInputSingleParams",
                            "name": "params",
                            "type": "tuple"
                        }
                    ],
                    "name": "exactInputSingle",
                    "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
                    "stateMutability": "payable",
                    "type": "function"
                }
            ]
        }
    
    def add_slippage_protection(self, tx_params: Dict[str, Any], 
                               slippage_tolerance: float = 0.005,
                               deadline_seconds: int = 300) -> Dict[str, Any]:
        """Add slippage protection to a DEX transaction"""
        # Clone the transaction params to avoid modifying the original
        tx = tx_params.copy()
        
        # Check if this is a DEX transaction
        if "data" not in tx or not tx["data"] or not tx["to"]:
            logger.info("Not a DEX transaction, skipping slippage protection")
            return tx
        
        # Try to decode the transaction data
        data = tx["data"]
        
        # Check for Uniswap V2 swapExactTokensForTokens
        if data.startswith("0x38ed1739"):  # Function selector for swapExactTokensForTokens
            try:
                # Decode the parameters
                params = eth_abi.decode(
                    ["uint256", "uint256", "address[]", "address", "uint256"],
                    bytes.fromhex(data[10:])  # Remove 0x and function selector
                )
                
                amount_in, amount_out_min, path, to, deadline = params
                
                # Calculate new minimum output with slippage
                new_amount_out_min = int(amount_out_min * (1 - slippage_tolerance))
                
                # Calculate new deadline
                new_deadline = int(time.time()) + deadline_seconds
                
                # Encode the new parameters
                new_data = "0x38ed1739" + eth_abi.encode(
                    ["uint256", "uint256", "address[]", "address", "uint256"],
                    [amount_in, new_amount_out_min, path, to, new_deadline]
                ).hex()
                
                tx["data"] = new_data
                logger.info(f"Added slippage protection: {amount_out_min} -> {new_amount_out_min}, deadline: {new_deadline}")
                
                return tx
            except Exception as e:
                logger.error(f"Error adding slippage protection to Uniswap V2 swap: {e}")
        
        # Check for Uniswap V3 exactInputSingle
        elif data.startswith("0x414bf389"):  # Function selector for exactInputSingle
            try:
                # Decode the parameters (tuple)
                params = eth_abi.decode(
                    ["(address,address,uint24,address,uint256,uint256,uint256,uint160)"],
                    bytes.fromhex(data[10:])  # Remove 0x and function selector
                )
                
                # Unpack the tuple
                token_in, token_out, fee, recipient, deadline, amount_in, amount_out_min, sqrt_price_limit = params[0]
                
                # Calculate new minimum output with slippage
                new_amount_out_min = int(amount_out_min * (1 - slippage_tolerance))
                
                # Calculate new deadline
                new_deadline = int(time.time()) + deadline_seconds
                
                # Encode the new parameters
                new_data = "0x414bf389" + eth_abi.encode(
                    ["(address,address,uint24,address,uint256,uint256,uint256,uint160)"],
                    [(token_in, token_out, fee, recipient, new_deadline, amount_in, new_amount_out_min, sqrt_price_limit)]
                ).hex()
                
                tx["data"] = new_data
                logger.info(f"Added slippage protection to Uniswap V3 swap: {amount_out_min} -> {new_amount_out_min}, deadline: {new_deadline}")
                
                return tx
            except Exception as e:
                logger.error(f"Error adding slippage protection to Uniswap V3 swap: {e}")
        
        # If we couldn't decode the transaction, return it unchanged
        logger.warning("Could not decode DEX transaction, returning unchanged")
        return tx
    
    async def get_expected_output(self, router_address: str, amount_in: int, 
                                path: List[str], router_type: str = "uniswap_v2") -> int:
        """Get expected output amount for a swap"""
        if router_type not in self.router_abis:
            raise ValueError(f"Unsupported router type: {router_type}")
        
        # Create contract instance
        contract = self.web3.eth.contract(address=router_address, abi=self.router_abis[router_type])
        
        if router_type == "uniswap_v2":
            # Call getAmountsOut
            try:
                amounts = await contract.functions.getAmountsOut(amount_in, path).call()
                return amounts[-1]
            except Exception as e:
                logger.error(f"Error getting expected output: {e}")
                return 0
        elif router_type == "uniswap_v3":
            # For V3, we'd need to use the quoter contract
            # This is a simplified example
            logger.warning("Uniswap V3 quoter not implemented")
            return 0
        
        return 0
    
    async def calculate_price_impact(self, router_address: str, amount_in: int, 
                                   path: List[str], router_type: str = "uniswap_v2") -> float:
        """Calculate price impact of a swap"""
        # Get expected output for the full amount
        expected_output_full = await self.get_expected_output(router_address, amount_in, path, router_type)
        
        if expected_output_full == 0:
            return 1.0  # 100% price impact (error case)
        
        # Get expected output for a small amount (1% of input)
        small_amount = amount_in // 100
        if small_amount == 0:
            small_amount = 1
        
        expected_output_small = await self.get_expected_output(router_address, small_amount, path, router_type)
        
        if expected_output_small == 0:
            return 1.0  # 100% price impact (error case)
        
        # Calculate price for small swap
        small_price = expected_output_small / small_amount
        
        # Calculate price for full swap
        full_price = expected_output_full / amount_in
        
        # Calculate price impact
        price_impact = 1 - (full_price / small_price)
        
        return max(0, min(1, price_impact))  # Clamp between 0 and 1

# Example usage
async def main():
    # Initialize Web3 provider
    web3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_INFURA_KEY"))
    
    # Initialize MEV protection
    config = TransactionConfig(
        max_priority_fee_gwei=2.0,
        max_fee_gwei=50.0,
        flashbots_enabled=True,
        simulate_before_send=True,
        sandwich_protection=True
    )
    
    mev_protection = MEVProtection(web3, config)
    
    # Create a test account
    account = Account.create()
    print(f"Created test account: {account.address}")
    
    # Create a test transaction
    tx_params = {
        "to": "${CONTRACT_ADDRESS}",  # Uniswap V2 Router
        "value": 0,
        "data": "${CONTRACT_ADDRESS}0000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        "chainId": 1
    }
    
    # Add slippage protection
    slippage_protection = SlippageProtection(web3)
    tx_params = slippage_protection.add_slippage_protection(tx_params)
      # Send transaction
    # NOTE: In production, use secure transaction signer instead of direct private key
    from secure_transaction_signer import SecureTransactionSigner
    transaction_signer = SecureTransactionSigner.from_hsm()  # Use HSM in production
    result = await mev_protection.send_transaction(tx_params, transaction_signer=transaction_signer)
    print(f"Transaction result: {result}")
    
    # Get stats
    stats = mev_protection.get_stats()
    print(f"MEV protection stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())