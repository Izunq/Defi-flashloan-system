#!/usr/bin/env python3
"""
Security Integration Module for Institutional-Grade Arbitrage System
===================================================================

This module integrates all security components into a unified security framework:
- Secure transaction signing (HSM/Multi-sig)
- AI/ML model security
- Compliance framework
- MEV protection
- Risk management
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from web3 import Web3
from web3.types import TxParams, Wei, HexStr, ChecksumAddress
from eth_account.account import Account
from eth_account.signers.local import LocalAccount

# Import security modules
from secure_transaction_signer import get_transaction_signer, TransactionSigner
from ai_model_security import AISecurityManager
from compliance_framework import ComplianceFramework
from mev_protection import MEVProtection, TransactionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("security.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SECURITY_INTEGRATION")

@dataclass
class SecurityConfig:
    """Configuration for security integration"""
    # Transaction signing
    use_hsm: bool = True
    use_multisig: bool = False
    hsm_provider: str = "aws"
    
    # MEV protection
    use_flashbots: bool = True
    max_priority_fee_gwei: float = 2.0
    max_fee_gwei: float = 100.0
    slippage_tolerance: float = 0.005  # 0.5%
    
    # Compliance
    kyc_required: bool = True
    aml_checks: bool = True
    halal_compliance: bool = False
    
    # AI/ML security
    model_verification: bool = True
    adversarial_protection: bool = True
    
    # Risk management
    max_position_size_usd: float = 50000.0
    max_daily_transactions: int = 20
    max_hourly_transactions: int = 5
    max_gas_price_gwei: float = 500.0

class SecurityIntegration:
    """Main class for integrating all security components"""
    
    def __init__(self, web3_provider: Web3, config: SecurityConfig = None):
        self.web3 = web3_provider
        self.config = config or SecurityConfig()
        
        # Initialize security components
        self._init_components()
        
        # Transaction counters
        self.daily_transactions = 0
        self.hourly_transactions = 0
        self.last_day_reset = datetime.now()
        self.last_hour_reset = datetime.now()
        
        logger.info("Security integration initialized")
    
    def _init_components(self):
        """Initialize all security components"""
        # Transaction signer
        try:
            self.signer = get_transaction_signer()
            logger.info(f"Transaction signer initialized: {type(self.signer).__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize transaction signer: {e}")
            raise
        
        # MEV protection
        try:
            mev_config = TransactionConfig(
                max_priority_fee_gwei=self.config.max_priority_fee_gwei,
                max_fee_gwei=self.config.max_fee_gwei,
                slippage_tolerance=self.config.slippage_tolerance,
                flashbots_enabled=self.config.use_flashbots
            )
            self.mev_protection = MEVProtection(self.web3, mev_config)
            logger.info("MEV protection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MEV protection: {e}")
            self.mev_protection = None
        
        # Compliance framework
        try:
            self.compliance = ComplianceFramework()
            logger.info("Compliance framework initialized")
        except Exception as e:
            logger.error(f"Failed to initialize compliance framework: {e}")
            self.compliance = None
        
        # AI security manager
        try:
            self.ai_security = AISecurityManager()
            logger.info("AI security manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AI security manager: {e}")
            self.ai_security = None
    
    def _update_transaction_counters(self):
        """Update transaction counters and check limits"""
        # Reset daily counter if needed
        if datetime.now() - self.last_day_reset > timedelta(days=1):
            self.daily_transactions = 0
            self.last_day_reset = datetime.now()
        
        # Reset hourly counter if needed
        if datetime.now() - self.last_hour_reset > timedelta(hours=1):
            self.hourly_transactions = 0
            self.last_hour_reset = datetime.now()
        
        # Increment counters
        self.daily_transactions += 1
        self.hourly_transactions += 1
        
        # Check limits
        if self.daily_transactions > self.config.max_daily_transactions:
            raise ValueError(f"Daily transaction limit exceeded: {self.daily_transactions}/{self.config.max_daily_transactions}")
        
        if self.hourly_transactions > self.config.max_hourly_transactions:
            raise ValueError(f"Hourly transaction limit exceeded: {self.hourly_transactions}/{self.config.max_hourly_transactions}")
    
    async def secure_transaction(self, tx_params: Dict[str, Any], 
                               user_id: str = None,
                               strategy_id: str = None) -> Dict[str, Any]:
        """Send a transaction with all security measures"""
        # Update transaction counters
        self._update_transaction_counters()
        
        # Get the account address
        account_address = self.signer.get_address()
        
        # Check compliance if enabled
        if self.compliance and (self.config.kyc_required or self.config.aml_checks):
            if not tx_params.get("to"):
                logger.warning("No 'to' address in transaction, skipping compliance check")
            else:
                # Check if this is a token transfer or contract interaction
                is_token_transfer = "data" in tx_params and tx_params["data"].startswith("0xa9059cbb")
                
                # For token transfers, extract the recipient and amount
                if is_token_transfer:
                    # Extract recipient (skip function selector and padding)
                    recipient = "0x" + tx_params["data"][34:74]
                    # Extract amount (skip function selector, padding, and recipient)
                    amount_hex = tx_params["data"][74:138]
                    amount = int(amount_hex, 16)
                else:
                    # For contract interactions, use the contract address as recipient
                    recipient = tx_params["to"]
                    amount = tx_params.get("value", 0)
                
                # Perform compliance check
                compliance_result = self.compliance.check_transaction_compliance(
                    tx_hash="0x0000000000000000000000000000000000000000000000000000000000000000",  # Placeholder
                    from_address=account_address,
                    to_address=recipient,
                    amount=amount,
                    currency="ETH",  # Simplified, should be determined based on the token
                    user_id=user_id,
                    strategy_id=strategy_id
                )
                
                if not compliance_result["is_compliant"]:
                    logger.error(f"Transaction failed compliance check: {compliance_result['reasons']}")
                    return {
                        "success": False,
                        "error": "Compliance check failed",
                        "details": compliance_result
                    }
                
                logger.info(f"Transaction passed compliance check")
        
        # Check strategy if provided
        if strategy_id and self.compliance and self.config.halal_compliance:
            # This is a simplified check - in a real implementation, you'd get the strategy details
            is_halal = self.compliance.db_manager.is_strategy_halal(strategy_id)
            
            if not is_halal and self.config.halal_compliance:
                logger.error(f"Strategy {strategy_id} is not Halal compliant")
                return {
                    "success": False,
                    "error": "Strategy is not Halal compliant",
                    "details": {"strategy_id": strategy_id}
                }
            
            logger.info(f"Strategy {strategy_id} passed Halal compliance check")
        
        # Check gas price
        if "gasPrice" in tx_params:
            gas_price_gwei = tx_params["gasPrice"] / 10**9
            if gas_price_gwei > self.config.max_gas_price_gwei:
                logger.error(f"Gas price too high: {gas_price_gwei} gwei > {self.config.max_gas_price_gwei} gwei")
                return {
                    "success": False,
                    "error": "Gas price too high",
                    "details": {"gas_price_gwei": gas_price_gwei, "max_gas_price_gwei": self.config.max_gas_price_gwei}
                }
        elif "maxFeePerGas" in tx_params:
            max_fee_gwei = tx_params["maxFeePerGas"] / 10**9
            if max_fee_gwei > self.config.max_gas_price_gwei:
                logger.error(f"Max fee too high: {max_fee_gwei} gwei > {self.config.max_gas_price_gwei} gwei")
                return {
                    "success": False,
                    "error": "Max fee too high",
                    "details": {"max_fee_gwei": max_fee_gwei, "max_gas_price_gwei": self.config.max_gas_price_gwei}
                }
        
        # Use MEV protection if enabled
        if self.mev_protection:
            try:
                # Sign and send transaction
                result = await self.mev_protection.send_transaction(tx_params, account=self.signer)
                
                if result["success"]:
                    logger.info(f"Transaction sent successfully: {result['tx_hash']}")
                else:
                    logger.error(f"Transaction failed: {result.get('error', 'Unknown error')}")
                
                return result
            except Exception as e:
                logger.error(f"Error sending transaction with MEV protection: {e}")
                return {"success": False, "error": str(e)}
        else:
            # Fall back to regular transaction signing
            try:
                # Prepare transaction
                if "from" not in tx_params:
                    tx_params["from"] = account_address
                
                if "nonce" not in tx_params:
                    tx_params["nonce"] = self.web3.eth.get_transaction_count(account_address)
                
                # Sign transaction
                signed_tx = self.signer.sign_transaction(tx_params)
                
                # Send transaction
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx)
                
                logger.info(f"Transaction sent: {tx_hash.hex()}")
                
                return {
                    "success": True,
                    "tx_hash": tx_hash.hex(),
                    "method": "regular"
                }
            except Exception as e:
                logger.error(f"Error sending transaction: {e}")
                return {"success": False, "error": str(e)}
    
    async def verify_ai_model(self, model_id: str, version: str, 
                            test_data: Any, test_labels: Any) -> Dict[str, Any]:
        """Verify AI model security"""
        if not self.ai_security:
            logger.warning("AI security manager not initialized")
            return {"success": False, "error": "AI security manager not initialized"}
        
        try:
            # Validate model performance
            is_valid, metrics = self.ai_security.validate_model_performance(
                model_id=model_id,
                version=version,
                test_data=test_data,
                test_labels=test_labels
            )
            
            if not is_valid:
                logger.warning(f"AI model {model_id} v{version} failed validation")
                return {
                    "success": False,
                    "error": "Model validation failed",
                    "details": metrics
                }
            
            logger.info(f"AI model {model_id} v{version} passed validation")
            return {
                "success": True,
                "metrics": metrics
            }
        except Exception as e:
            logger.error(f"Error verifying AI model: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_strategy_compliance(self, strategy_id: str, assets: List[str],
                                 operations: List[str]) -> Dict[str, Any]:
        """Verify strategy compliance"""
        if not self.compliance:
            logger.warning("Compliance framework not initialized")
            return {"success": False, "error": "Compliance framework not initialized"}
        
        try:
            # Verify strategy compliance
            result = self.compliance.verify_strategy_compliance(
                strategy_id=strategy_id,
                assets=assets,
                operations=operations
            )
            
            if not result["is_compliant"]:
                logger.warning(f"Strategy {strategy_id} failed compliance check: {result['compliance_issues']}")
                return {
                    "success": False,
                    "error": "Strategy compliance check failed",
                    "details": result
                }
            
            logger.info(f"Strategy {strategy_id} passed compliance check")
            return {
                "success": True,
                "details": result
            }
        except Exception as e:
            logger.error(f"Error verifying strategy compliance: {e}")
            return {"success": False, "error": str(e)}
    
    def onboard_user(self, wallet_address: str, first_name: str, last_name: str,
                    dob: str, country_code: str, region_code: str = None) -> Dict[str, Any]:
        """Onboard a new user with KYC"""
        if not self.compliance:
            logger.warning("Compliance framework not initialized")
            return {"success": False, "error": "Compliance framework not initialized"}
        
        try:
            # Onboard user
            result = self.compliance.onboard_user(
                wallet_address=wallet_address,
                first_name=first_name,
                last_name=last_name,
                dob=dob,
                country_code=country_code,
                region_code=region_code
            )
            
            if result["is_restricted"]:
                logger.warning(f"User from restricted location: {country_code}/{region_code}")
                return {
                    "success": False,
                    "error": "User from restricted location",
                    "details": result
                }
            
            if result["aml_status"] == "blocked":
                logger.warning(f"User blocked by AML check: {wallet_address}")
                return {
                    "success": False,
                    "error": "User blocked by AML check",
                    "details": result
                }
            
            logger.info(f"User onboarded successfully: {result['user_id']}")
            return {
                "success": True,
                "user_id": result["user_id"],
                "details": result
            }
        except Exception as e:
            logger.error(f"Error onboarding user: {e}")
            return {"success": False, "error": str(e)}
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get status of all security components"""
        status = {
            "transaction_signer": {
                "type": type(self.signer).__name__,
                "address": self.signer.get_address(),
                "status": "active"
            },
            "transaction_limits": {
                "daily": {
                    "current": self.daily_transactions,
                    "limit": self.config.max_daily_transactions
                },
                "hourly": {
                    "current": self.hourly_transactions,
                    "limit": self.config.max_hourly_transactions
                }
            }
        }
        
        # Add MEV protection status
        if self.mev_protection:
            status["mev_protection"] = {
                "status": "active",
                "stats": self.mev_protection.get_stats()
            }
        else:
            status["mev_protection"] = {"status": "inactive"}
        
        # Add compliance status
        if self.compliance:
            status["compliance"] = {
                "status": "active",
                "kyc_enabled": self.config.kyc_required,
                "aml_enabled": self.config.aml_checks,
                "halal_enabled": self.config.halal_compliance
            }
        else:
            status["compliance"] = {"status": "inactive"}
        
        # Add AI security status
        if self.ai_security:
            status["ai_security"] = {
                "status": "active",
                "model_verification": self.config.model_verification,
                "adversarial_protection": self.config.adversarial_protection
            }
        else:
            status["ai_security"] = {"status": "inactive"}
        
        return status

# Example usage
async def main():
    # Initialize Web3 provider
    web3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_INFURA_KEY"))
    
    # Initialize security integration
    config = SecurityConfig(
        use_hsm=True,
        use_flashbots=True,
        kyc_required=True,
        aml_checks=True,
        halal_compliance=True
    )
    
    security = SecurityIntegration(web3, config)
    
    # Get security status
    status = security.get_security_status()
    print(f"Security status: {json.dumps(status, indent=2)}")
    
    # Example: Onboard a user
    user_result = security.onboard_user(
        wallet_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        first_name="John",
        last_name="Doe",
        dob="1980-01-01",
        country_code="US",
        region_code="CA"
    )
    
    print(f"User onboarding result: {json.dumps(user_result, indent=2)}")
    
    # Example: Verify strategy compliance
    strategy_result = security.verify_strategy_compliance(
        strategy_id="strategy-123",
        assets=[
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"   # WETH
        ],
        operations=[
            "swap",
            "liquidity_provision"
        ]
    )
    
    print(f"Strategy compliance result: {json.dumps(strategy_result, indent=2)}")
    
    # Example: Send a secure transaction
    tx_params = {
        "to": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap V2 Router
        "value": 0,
        "data": "0x38ed1739000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        "chainId": 1
    }
    
    tx_result = await security.secure_transaction(
        tx_params=tx_params,
        user_id=user_result.get("user_id") if user_result.get("success") else None,
        strategy_id="strategy-123"
    )
    
    print(f"Transaction result: {json.dumps(tx_result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())