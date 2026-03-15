"""
Atomic Cross-Chain Arbitrage

This module implements atomic cross-chain arbitrage capabilities, allowing
for the execution of arbitrage opportunities across multiple blockchain
networks with atomicity guarantees.

Features:
- Cross-chain opportunity detection
- Atomic execution guarantees
- Risk management
- Gas optimization
- Profit calculation and verification
"""

import json
import time
import hashlib
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass
import uuid
import random
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("atomic_arbitrage")

class ArbitrageStatus(Enum):
    """Status of arbitrage operations"""
    SCANNING = "scanning"
    OPPORTUNITY_FOUND = "opportunity_found"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERTED = "reverted"


class ExecutionStrategy(Enum):
    """Execution strategies for arbitrage"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    BATCHED = "batched"
    FLASH_LOAN = "flash_loan"
    FLASH_BOTS = "flash_bots"
    ATOMIC_CROSS_CHAIN = "atomic_cross_chain"


class RiskLevel(Enum):
    """Risk levels for arbitrage opportunities"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ArbitrageOpportunity:
    """Cross-chain arbitrage opportunity"""
    opportunity_id: str
    source_chain_id: int
    target_chain_id: int
    source_token: str
    target_token: str
    source_amount: float
    expected_target_amount: float
    expected_profit_usd: float
    profit_percentage: float
    execution_path: List[Dict[str, Any]]
    risk_level: RiskLevel
    gas_cost_usd: float
    timestamp: int
    expiration: int
    confidence: float


@dataclass
class ArbitrageResult:
    """Result of an arbitrage execution"""
    opportunity_id: str
    status: ArbitrageStatus
    actual_profit_usd: float
    actual_profit_percentage: float
    gas_used_usd: float
    execution_time_ms: int
    transaction_hashes: Dict[int, str]  # Chain ID -> Transaction hash
    error_message: Optional[str]
    timestamp: int


class AtomicCrossChainArbitrage:
    """
    Atomic Cross-Chain Arbitrage system.
    
    This class provides capabilities for detecting and executing arbitrage
    opportunities across multiple blockchain networks with atomicity guarantees.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the Atomic Cross-Chain Arbitrage system.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.chain_configs: Dict[int, Dict[str, Any]] = {}
        self.token_configs: Dict[str, Dict[str, Any]] = {}
        self.dex_configs: Dict[str, Dict[str, Any]] = {}
        self.bridge_configs: Dict[Tuple[int, int], Dict[str, Any]] = {}
        
        self.detected_opportunities: List[ArbitrageOpportunity] = []
        self.executed_arbitrages: List[ArbitrageResult] = []
        self.current_status = ArbitrageStatus.SCANNING
        
        self.min_profit_threshold_usd = self.config["global_settings"]["min_profit_threshold_usd"]
        self.min_profit_percentage = self.config["global_settings"]["min_profit_percentage"]
        self.max_gas_percentage = self.config["global_settings"]["max_gas_percentage"]
        self.max_slippage_percentage = self.config["global_settings"]["max_slippage_percentage"]
        
        self.callbacks: Dict[str, List[Callable]] = {
            "opportunity_detected": [],
            "arbitrage_started": [],
            "arbitrage_completed": [],
            "arbitrage_failed": [],
            "status_changed": []
        }
        
        # Initialize configurations
        self._initialize_configs()
        
        # Start background tasks
        self.running = True
        self.background_tasks = [
            asyncio.create_task(self._scan_arbitrage_opportunities()),
            asyncio.create_task(self._execute_arbitrage_opportunities()),
            asyncio.create_task(self._update_market_data())
        ]
        
        logger.info(f"Atomic Cross-Chain Arbitrage initialized with {len(self.chain_configs)} chains")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Use default configuration as fallback
            return {
                "chains": [],
                "tokens": [],
                "dexes": [],
                "bridges": [],
                "global_settings": {
                    "scan_interval_seconds": 10,
                    "execution_interval_seconds": 5,
                    "market_data_update_seconds": 60,
                    "min_profit_threshold_usd": 50,
                    "min_profit_percentage": 0.5,
                    "max_gas_percentage": 30,
                    "max_slippage_percentage": 1.0,
                    "default_execution_strategy": "ATOMIC_CROSS_CHAIN",
                    "max_concurrent_executions": 3,
                    "opportunity_timeout_seconds": 60
                }
            }
    
    def _initialize_configs(self):
        """Initialize configurations from the loaded config"""
        # Initialize chain configurations
        for chain_config in self.config.get("chains", []):
            try:
                chain_id = chain_config["chain_id"]
                self.chain_configs[chain_id] = chain_config
                logger.info(f"Initialized chain config for chain ID {chain_id} ({chain_config['name']})")
            except Exception as e:
                logger.error(f"Failed to initialize chain config: {e}")
        
        # Initialize token configurations
        for token_config in self.config.get("tokens", []):
            try:
                token_symbol = token_config["symbol"]
                self.token_configs[token_symbol] = token_config
                logger.info(f"Initialized token config for {token_symbol}")
            except Exception as e:
                logger.error(f"Failed to initialize token config: {e}")
        
        # Initialize DEX configurations
        for dex_config in self.config.get("dexes", []):
            try:
                dex_id = dex_config["id"]
                self.dex_configs[dex_id] = dex_config
                logger.info(f"Initialized DEX config for {dex_id}")
            except Exception as e:
                logger.error(f"Failed to initialize DEX config: {e}")
        
        # Initialize bridge configurations
        for bridge_config in self.config.get("bridges", []):
            try:
                source_chain_id = bridge_config["source_chain_id"]
                target_chain_id = bridge_config["target_chain_id"]
                bridge_key = (source_chain_id, target_chain_id)
                self.bridge_configs[bridge_key] = bridge_config
                logger.info(f"Initialized bridge config from chain {source_chain_id} to {target_chain_id}")
            except Exception as e:
                logger.error(f"Failed to initialize bridge config: {e}")
    
    async def _scan_arbitrage_opportunities(self):
        """Background task to scan for arbitrage opportunities"""
        interval = self.config["global_settings"]["scan_interval_seconds"]
        while self.running:
            try:
                # Update status
                self._update_status(ArbitrageStatus.SCANNING)
                
                # Scan for opportunities
                opportunities = await self._detect_opportunities()
                
                # Process detected opportunities
                for opportunity in opportunities:
                    # Check if opportunity meets profit thresholds
                    if (opportunity.expected_profit_usd >= self.min_profit_threshold_usd and
                        opportunity.profit_percentage >= self.min_profit_percentage):
                        
                        # Check if gas cost is reasonable
                        gas_percentage = (opportunity.gas_cost_usd / opportunity.expected_profit_usd) * 100
                        if gas_percentage <= self.max_gas_percentage:
                            # Add to detected opportunities
                            self.detected_opportunities.append(opportunity)
                            
                            # Trigger callback
                            self._trigger_callbacks("opportunity_detected", opportunity)
                            
                            logger.info(
                                f"Arbitrage opportunity detected: {opportunity.source_token} -> "
                                f"{opportunity.target_token} on chains {opportunity.source_chain_id} -> "
                                f"{opportunity.target_chain_id} (Expected profit: ${opportunity.expected_profit_usd:.2f}, "
                                f"{opportunity.profit_percentage:.2f}%)"
                            )
                            
                            # Update status if we found at least one opportunity
                            self._update_status(ArbitrageStatus.OPPORTUNITY_FOUND)
                        else:
                            logger.debug(
                                f"Skipping opportunity due to high gas cost: {gas_percentage:.2f}% "
                                f"(threshold: {self.max_gas_percentage}%)"
                            )
                    else:
                        logger.debug(
                            f"Skipping opportunity due to low profit: ${opportunity.expected_profit_usd:.2f}, "
                            f"{opportunity.profit_percentage:.2f}%"
                        )
            
            except Exception as e:
                logger.error(f"Error scanning arbitrage opportunities: {e}")
            
            await asyncio.sleep(interval)
    
    async def _detect_opportunities(self) -> List[ArbitrageOpportunity]:
        """
        Detect cross-chain arbitrage opportunities.
        
        Returns:
            List of detected arbitrage opportunities
        """
        # In a real implementation, this would analyze price data across chains
        # and DEXes to identify profitable arbitrage opportunities.
        # For demonstration, we'll simulate opportunity detection.
        
        opportunities = []
        
        # Get all chain pairs
        chain_pairs = []
        for source_chain_id in self.chain_configs:
            for target_chain_id in self.chain_configs:
                if source_chain_id != target_chain_id:
                    # Check if there's a bridge between these chains
                    if (source_chain_id, target_chain_id) in self.bridge_configs:
                        chain_pairs.append((source_chain_id, target_chain_id))
        
        # Randomly select a few chain pairs to simulate opportunities
        selected_pairs = random.sample(chain_pairs, min(3, len(chain_pairs)))
        
        for source_chain_id, target_chain_id in selected_pairs:
            # Only generate opportunities occasionally to simulate realistic detection
            if random.random() < 0.3:  # 30% chance of detecting an opportunity
                # Get token symbols
                token_symbols = list(self.token_configs.keys())
                if not token_symbols:
                    continue
                
                # Select random tokens
                source_token = random.choice(token_symbols)
                target_token = source_token  # Same token for simplicity
                
                # Generate random amounts and profits
                source_amount = random.uniform(100, 10000)
                profit_percentage = random.uniform(0.1, 3.0)
                expected_target_amount = source_amount * (1 + profit_percentage / 100)
                
                # Calculate USD values (simplified)
                token_price_usd = self._get_token_price_usd(source_token)
                source_amount_usd = source_amount * token_price_usd
                expected_profit_usd = source_amount_usd * (profit_percentage / 100)
                
                # Calculate gas cost
                gas_cost_usd = random.uniform(5, 50)
                
                # Determine risk level based on profit and chains
                risk_level = self._calculate_risk_level(profit_percentage, source_chain_id, target_chain_id)
                
                # Generate execution path
                execution_path = self._generate_execution_path(
                    source_chain_id, target_chain_id, source_token, target_token,
                    source_amount, expected_target_amount
                )
                
                # Create opportunity
                opportunity = ArbitrageOpportunity(
                    opportunity_id=str(uuid.uuid4()),
                    source_chain_id=source_chain_id,
                    target_chain_id=target_chain_id,
                    source_token=source_token,
                    target_token=target_token,
                    source_amount=source_amount,
                    expected_target_amount=expected_target_amount,
                    expected_profit_usd=expected_profit_usd,
                    profit_percentage=profit_percentage,
                    execution_path=execution_path,
                    risk_level=risk_level,
                    gas_cost_usd=gas_cost_usd,
                    timestamp=int(time.time()),
                    expiration=int(time.time()) + self.config["global_settings"]["opportunity_timeout_seconds"],
                    confidence=random.uniform(0.7, 0.95)
                )
                
                opportunities.append(opportunity)
        
        return opportunities
    
    def _get_token_price_usd(self, token_symbol: str) -> float:
        """
        Get the USD price of a token.
        
        Args:
            token_symbol: Token symbol
            
        Returns:
            Token price in USD
        """
        # In a real implementation, this would fetch the current price from an oracle
        # For demonstration, we'll use simulated prices
        
        # Common token prices (simplified)
        token_prices = {
            "ETH": 3000.0,
            "BTC": 50000.0,
            "USDC": 1.0,
            "USDT": 1.0,
            "DAI": 1.0,
            "BNB": 300.0,
            "MATIC": 1.5,
            "AVAX": 30.0,
            "SOL": 100.0,
            "DOT": 20.0
        }
        
        return token_prices.get(token_symbol, 10.0)  # Default to $10 for unknown tokens
    
    def _calculate_risk_level(self, profit_percentage: float, source_chain_id: int, target_chain_id: int) -> RiskLevel:
        """
        Calculate the risk level of an arbitrage opportunity.
        
        Args:
            profit_percentage: Expected profit percentage
            source_chain_id: Source chain ID
            target_chain_id: Target chain ID
            
        Returns:
            Risk level
        """
        # Higher profit often means higher risk
        if profit_percentage > 5.0:
            base_risk = RiskLevel.VERY_HIGH
        elif profit_percentage > 2.0:
            base_risk = RiskLevel.HIGH
        elif profit_percentage > 1.0:
            base_risk = RiskLevel.MEDIUM
        else:
            base_risk = RiskLevel.LOW
        
        # Adjust based on chain reliability (simplified)
        # In a real implementation, this would consider chain security, liquidity, etc.
        reliable_chains = [1, 56, 137]  # Ethereum, BSC, Polygon
        
        if source_chain_id in reliable_chains and target_chain_id in reliable_chains:
            # Both chains are reliable, reduce risk
            risk_levels = list(RiskLevel)
            current_index = risk_levels.index(base_risk)
            if current_index > 0:
                return risk_levels[current_index - 1]
        
        return base_risk
    
    def _generate_execution_path(
        self,
        source_chain_id: int,
        target_chain_id: int,
        source_token: str,
        target_token: str,
        source_amount: float,
        target_amount: float
    ) -> List[Dict[str, Any]]:
        """
        Generate the execution path for an arbitrage opportunity.
        
        Args:
            source_chain_id: Source chain ID
            target_chain_id: Target chain ID
            source_token: Source token symbol
            target_token: Target token symbol
            source_amount: Source amount
            target_amount: Target amount
            
        Returns:
            Execution path as a list of steps
        """
        # In a real implementation, this would calculate the optimal path
        # For demonstration, we'll generate a simplified path
        
        execution_path = []
        
        # Step 1: Get source token on source chain
        execution_path.append({
            "step": 1,
            "type": "source",
            "chain_id": source_chain_id,
            "token": source_token,
            "amount": source_amount,
            "description": f"Start with {source_amount} {source_token} on chain {source_chain_id}"
        })
        
        # Step 2: Bridge to target chain
        bridge_key = (source_chain_id, target_chain_id)
        if bridge_key in self.bridge_configs:
            bridge_config = self.bridge_configs[bridge_key]
            bridge_name = bridge_config.get("name", "Unknown Bridge")
            
            # Calculate bridge fee and amount after bridge
            bridge_fee_percentage = bridge_config.get("fee_percentage", 0.1)
            bridge_fee = source_amount * (bridge_fee_percentage / 100)
            amount_after_bridge = source_amount - bridge_fee
            
            execution_path.append({
                "step": 2,
                "type": "bridge",
                "source_chain_id": source_chain_id,
                "target_chain_id": target_chain_id,
                "bridge": bridge_name,
                "token": source_token,
                "amount_in": source_amount,
                "fee": bridge_fee,
                "amount_out": amount_after_bridge,
                "description": f"Bridge {source_amount} {source_token} from chain {source_chain_id} to {target_chain_id} using {bridge_name}"
            })
        else:
            # If no bridge is configured, simulate a direct transfer
            execution_path.append({
                "step": 2,
                "type": "bridge",
                "source_chain_id": source_chain_id,
                "target_chain_id": target_chain_id,
                "bridge": "Direct Transfer",
                "token": source_token,
                "amount_in": source_amount,
                "fee": 0,
                "amount_out": source_amount,
                "description": f"Transfer {source_amount} {source_token} from chain {source_chain_id} to {target_chain_id}"
            })
        
        # Step 3: Swap on target chain (if source and target tokens are different)
        if source_token != target_token:
            # Find a DEX on the target chain
            target_dexes = [
                dex for dex_id, dex in self.dex_configs.items()
                if dex.get("chain_id") == target_chain_id
            ]
            
            if target_dexes:
                dex = random.choice(target_dexes)
                dex_name = dex.get("name", "Unknown DEX")
                
                execution_path.append({
                    "step": 3,
                    "type": "swap",
                    "chain_id": target_chain_id,
                    "dex": dex_name,
                    "token_in": source_token,
                    "token_out": target_token,
                    "amount_in": amount_after_bridge,
                    "amount_out": target_amount,
                    "description": f"Swap {amount_after_bridge} {source_token} to {target_amount} {target_token} on {dex_name}"
                })
            else:
                # If no DEX is configured, simulate a direct swap
                execution_path.append({
                    "step": 3,
                    "type": "swap",
                    "chain_id": target_chain_id,
                    "dex": "Direct Swap",
                    "token_in": source_token,
                    "token_out": target_token,
                    "amount_in": amount_after_bridge,
                    "amount_out": target_amount,
                    "description": f"Swap {amount_after_bridge} {source_token} to {target_amount} {target_token}"
                })
        
        # Step 4: Final result
        execution_path.append({
            "step": 4,
            "type": "result",
            "chain_id": target_chain_id,
            "token": target_token,
            "amount": target_amount,
            "description": f"End with {target_amount} {target_token} on chain {target_chain_id}"
        })
        
        return execution_path
    
    async def _execute_arbitrage_opportunities(self):
        """Background task to execute arbitrage opportunities"""
        interval = self.config["global_settings"]["execution_interval_seconds"]
        while self.running:
            try:
                # Check if we have opportunities to execute
                if self.detected_opportunities and self.current_status != ArbitrageStatus.EXECUTING:
                    # Sort opportunities by expected profit (highest first)
                    sorted_opportunities = sorted(
                        self.detected_opportunities,
                        key=lambda x: x.expected_profit_usd,
                        reverse=True
                    )
                    
                    # Get the most profitable opportunity
                    opportunity = sorted_opportunities[0]
                    
                    # Check if opportunity is still valid
                    if time.time() < opportunity.expiration:
                        # Update status
                        self._update_status(ArbitrageStatus.EXECUTING)
                        
                        # Execute the opportunity
                        result = await self._execute_arbitrage(opportunity)
                        
                        # Add to executed arbitrages
                        self.executed_arbitrages.append(result)
                        
                        # Remove from detected opportunities
                        self.detected_opportunities.remove(opportunity)
                        
                        # Trigger callback
                        if result.status == ArbitrageStatus.COMPLETED:
                            self._trigger_callbacks("arbitrage_completed", result)
                        else:
                            self._trigger_callbacks("arbitrage_failed", result)
                        
                        # Update status
                        if self.detected_opportunities:
                            self._update_status(ArbitrageStatus.OPPORTUNITY_FOUND)
                        else:
                            self._update_status(ArbitrageStatus.SCANNING)
                    else:
                        # Opportunity expired, remove it
                        logger.warning(f"Opportunity {opportunity.opportunity_id} expired, removing")
                        self.detected_opportunities.remove(opportunity)
            
            except Exception as e:
                logger.error(f"Error executing arbitrage opportunities: {e}")
                self._update_status(ArbitrageStatus.SCANNING)
            
            await asyncio.sleep(interval)
    
    async def _execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> ArbitrageResult:
        """
        Execute an arbitrage opportunity.
        
        Args:
            opportunity: The arbitrage opportunity to execute
            
        Returns:
            Result of the arbitrage execution
        """
        # In a real implementation, this would execute the arbitrage on-chain
        # For demonstration, we'll simulate execution
        
        logger.info(f"Executing arbitrage opportunity {opportunity.opportunity_id}")
        
        # Trigger callback
        self._trigger_callbacks("arbitrage_started", opportunity)
        
        # Simulate execution time
        execution_start = time.time()
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Simulate success/failure
        success_probability = 0.8  # 80% chance of success
        success = random.random() < success_probability
        
        # Generate transaction hashes
        tx_hashes = {}
        for step in opportunity.execution_path:
            if step["type"] in ["source", "swap", "bridge"] and "chain_id" in step:
                chain_id = step.get("source_chain_id", step.get("chain_id"))
                if chain_id not in tx_hashes:
                    tx_hash = f"0x{hashlib.sha256(f'{opportunity.opportunity_id}:{chain_id}:{time.time()}'.encode()).hexdigest()}"
                    tx_hashes[chain_id] = tx_hash
        
        # Calculate execution time
        execution_time_ms = int((time.time() - execution_start) * 1000)
        
        if success:
            # Simulate actual profit (might be slightly different from expected)
            profit_variation = random.uniform(0.8, 1.2)  # 80% to 120% of expected
            actual_profit_usd = opportunity.expected_profit_usd * profit_variation
            actual_profit_percentage = opportunity.profit_percentage * profit_variation
            
            # Simulate gas cost (might be slightly different from expected)
            gas_variation = random.uniform(0.9, 1.3)  # 90% to 130% of expected
            gas_used_usd = opportunity.gas_cost_usd * gas_variation
            
            logger.info(
                f"Arbitrage {opportunity.opportunity_id} completed successfully. "
                f"Profit: ${actual_profit_usd:.2f} ({actual_profit_percentage:.2f}%)"
            )
            
            return ArbitrageResult(
                opportunity_id=opportunity.opportunity_id,
                status=ArbitrageStatus.COMPLETED,
                actual_profit_usd=actual_profit_usd,
                actual_profit_percentage=actual_profit_percentage,
                gas_used_usd=gas_used_usd,
                execution_time_ms=execution_time_ms,
                transaction_hashes=tx_hashes,
                error_message=None,
                timestamp=int(time.time())
            )
        else:
            # Simulate failure
            error_messages = [
                "Insufficient liquidity",
                "Price moved unfavorably",
                "Bridge transaction failed",
                "Slippage exceeded threshold",
                "Transaction reverted",
                "Timeout waiting for confirmation"
            ]
            error_message = random.choice(error_messages)
            
            logger.warning(
                f"Arbitrage {opportunity.opportunity_id} failed: {error_message}"
            )
            
            return ArbitrageResult(
                opportunity_id=opportunity.opportunity_id,
                status=ArbitrageStatus.FAILED,
                actual_profit_usd=0,
                actual_profit_percentage=0,
                gas_used_usd=opportunity.gas_cost_usd * random.uniform(0.1, 0.5),  # Partial gas used
                execution_time_ms=execution_time_ms,
                transaction_hashes=tx_hashes,
                error_message=error_message,
                timestamp=int(time.time())
            )
    
    async def _update_market_data(self):
        """Background task to update market data"""
        interval = self.config["global_settings"]["market_data_update_seconds"]
        while self.running:
            try:
                # In a real implementation, this would fetch the latest market data
                # For demonstration, we'll just log that we're updating
                logger.debug("Updating market data")
                
                # Simulate market data update
                await asyncio.sleep(random.uniform(0.2, 1.0))
                
                # Clean up expired opportunities
                current_time = time.time()
                expired_opportunities = [
                    opp for opp in self.detected_opportunities
                    if current_time > opp.expiration
                ]
                
                for opp in expired_opportunities:
                    logger.debug(f"Removing expired opportunity {opp.opportunity_id}")
                    self.detected_opportunities.remove(opp)
            
            except Exception as e:
                logger.error(f"Error updating market data: {e}")
            
            await asyncio.sleep(interval)
    
    def _update_status(self, status: ArbitrageStatus):
        """
        Update the current status.
        
        Args:
            status: New status
        """
        if status != self.current_status:
            old_status = self.current_status
            self.current_status = status
            logger.info(f"Status changed from {old_status.value} to {status.value}")
            self._trigger_callbacks("status_changed", {"old_status": old_status, "new_status": status})
    
    def _trigger_callbacks(self, event_type: str, data: Any):
        """
        Trigger registered callbacks for an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in {event_type} callback: {e}")
    
    def register_callback(self, event_type: str, callback: Callable):
        """
        Register a callback for a specific event type.
        
        Args:
            event_type: Type of event to register for
            callback: Callback function
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            logger.info(f"Registered callback for event type '{event_type}'")
        else:
            logger.error(f"Unknown event type: {event_type}")
    
    def get_arbitrage_status(self) -> Dict[str, Any]:
        """
        Get the current status of the arbitrage system.
        
        Returns:
            Status information
        """
        return {
            "status": self.current_status.value,
            "detected_opportunities": len(self.detected_opportunities),
            "executed_arbitrages": len(self.executed_arbitrages),
            "successful_arbitrages": sum(1 for result in self.executed_arbitrages if result.status == ArbitrageStatus.COMPLETED),
            "failed_arbitrages": sum(1 for result in self.executed_arbitrages if result.status != ArbitrageStatus.COMPLETED),
            "total_profit_usd": sum(result.actual_profit_usd for result in self.executed_arbitrages if result.status == ArbitrageStatus.COMPLETED),
            "total_gas_used_usd": sum(result.gas_used_usd for result in self.executed_arbitrages),
            "average_execution_time_ms": self._calculate_average_execution_time(),
            "success_rate_percentage": self._calculate_success_rate()
        }
    
    def _calculate_average_execution_time(self) -> float:
        """Calculate the average execution time of arbitrages"""
        if not self.executed_arbitrages:
            return 0
        
        total_time = sum(result.execution_time_ms for result in self.executed_arbitrages)
        return total_time / len(self.executed_arbitrages)
    
    def _calculate_success_rate(self) -> float:
        """Calculate the success rate of arbitrages"""
        if not self.executed_arbitrages:
            return 0
        
        successful = sum(1 for result in self.executed_arbitrages if result.status == ArbitrageStatus.COMPLETED)
        return (successful / len(self.executed_arbitrages)) * 100
    
    def get_recent_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent arbitrage opportunities.
        
        Args:
            limit: Maximum number of opportunities to return
            
        Returns:
            List of recent opportunities
        """
        # Sort by timestamp (newest first)
        sorted_opportunities = sorted(
            self.detected_opportunities,
            key=lambda x: x.timestamp,
            reverse=True
        )
        
        # Limit the number of results
        limited_opportunities = sorted_opportunities[:limit]
        
        # Convert to serializable dictionaries
        return [
            {
                "opportunity_id": opp.opportunity_id,
                "source_chain_id": opp.source_chain_id,
                "target_chain_id": opp.target_chain_id,
                "source_token": opp.source_token,
                "target_token": opp.target_token,
                "expected_profit_usd": opp.expected_profit_usd,
                "profit_percentage": opp.profit_percentage,
                "risk_level": opp.risk_level.value,
                "gas_cost_usd": opp.gas_cost_usd,
                "timestamp": opp.timestamp,
                "expiration": opp.expiration,
                "time_remaining_seconds": max(0, opp.expiration - int(time.time()))
            }
            for opp in limited_opportunities
        ]
    
    def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent arbitrage executions.
        
        Args:
            limit: Maximum number of executions to return
            
        Returns:
            List of recent executions
        """
        # Sort by timestamp (newest first)
        sorted_executions = sorted(
            self.executed_arbitrages,
            key=lambda x: x.timestamp,
            reverse=True
        )
        
        # Limit the number of results
        limited_executions = sorted_executions[:limit]
        
        # Convert to serializable dictionaries
        return [
            {
                "opportunity_id": result.opportunity_id,
                "status": result.status.value,
                "actual_profit_usd": result.actual_profit_usd,
                "actual_profit_percentage": result.actual_profit_percentage,
                "gas_used_usd": result.gas_used_usd,
                "execution_time_ms": result.execution_time_ms,
                "transaction_hashes": result.transaction_hashes,
                "error_message": result.error_message,
                "timestamp": result.timestamp
            }
            for result in limited_executions
        ]
    
    def get_profit_statistics(self) -> Dict[str, Any]:
        """
        Get profit statistics.
        
        Returns:
            Profit statistics
        """
        # Filter successful arbitrages
        successful_arbitrages = [
            result for result in self.executed_arbitrages
            if result.status == ArbitrageStatus.COMPLETED
        ]
        
        if not successful_arbitrages:
            return {
                "total_profit_usd": 0,
                "average_profit_usd": 0,
                "max_profit_usd": 0,
                "min_profit_usd": 0,
                "total_gas_used_usd": 0,
                "net_profit_usd": 0,
                "roi_percentage": 0,
                "profit_distribution": []
            }
        
        # Calculate statistics
        total_profit_usd = sum(result.actual_profit_usd for result in successful_arbitrages)
        average_profit_usd = total_profit_usd / len(successful_arbitrages)
        max_profit_usd = max(result.actual_profit_usd for result in successful_arbitrages)
        min_profit_usd = min(result.actual_profit_usd for result in successful_arbitrages)
        
        total_gas_used_usd = sum(result.gas_used_usd for result in self.executed_arbitrages)
        net_profit_usd = total_profit_usd - total_gas_used_usd
        
        # Calculate ROI
        if total_gas_used_usd > 0:
            roi_percentage = (net_profit_usd / total_gas_used_usd) * 100
        else:
            roi_percentage = 0
        
        # Generate profit distribution
        profit_ranges = [0, 10, 50, 100, 500, 1000, float('inf')]
        profit_distribution = [0] * (len(profit_ranges) - 1)
        
        for result in successful_arbitrages:
            for i in range(len(profit_ranges) - 1):
                if profit_ranges[i] <= result.actual_profit_usd < profit_ranges[i + 1]:
                    profit_distribution[i] += 1
                    break
        
        return {
            "total_profit_usd": total_profit_usd,
            "average_profit_usd": average_profit_usd,
            "max_profit_usd": max_profit_usd,
            "min_profit_usd": min_profit_usd,
            "total_gas_used_usd": total_gas_used_usd,
            "net_profit_usd": net_profit_usd,
            "roi_percentage": roi_percentage,
            "profit_distribution": [
                {
                    "range": f"${profit_ranges[i]} - ${profit_ranges[i+1] if profit_ranges[i+1] != float('inf') else 'inf'}",
                    "count": profit_distribution[i]
                }
                for i in range(len(profit_distribution))
            ]
        }
    
    async def shutdown(self):
        """Shutdown the arbitrage system"""
        logger.info("Shutting down Atomic Cross-Chain Arbitrage")
        self.running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        logger.info("Atomic Cross-Chain Arbitrage shutdown complete")


async def main():
    """Example usage of the Atomic Cross-Chain Arbitrage system"""
    # Create arbitrage system
    arbitrage = AtomicCrossChainArbitrage("arbitrage_config.json")
    
    # Register callbacks
    arbitrage.register_callback("opportunity_detected", lambda opp: print(f"Opportunity detected: ${opp.expected_profit_usd:.2f}"))
    arbitrage.register_callback("arbitrage_completed", lambda result: print(f"Arbitrage completed: ${result.actual_profit_usd:.2f}"))
    
    # Run for a while to detect and execute opportunities
    await asyncio.sleep(30)
    
    # Get status
    status = arbitrage.get_arbitrage_status()
    print(f"Arbitrage status: {status}")
    
    # Get recent opportunities
    opportunities = arbitrage.get_recent_opportunities(limit=3)
    print(f"Recent opportunities: {opportunities}")
    
    # Get recent executions
    executions = arbitrage.get_recent_executions(limit=3)
    print(f"Recent executions: {executions}")
    
    # Get profit statistics
    stats = arbitrage.get_profit_statistics()
    print(f"Profit statistics: {stats}")
    
    # Shutdown
    await arbitrage.shutdown()


if __name__ == "__main__":
    asyncio.run(main())