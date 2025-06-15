#!/usr/bin/env python3
"""
Advanced Flash Loan Arbitrage System - V33 Improved
==================================================

This is an enhanced version of the arbitrage bot with:
- Better error handling and logging
- Improved configuration management
- Enhanced opportunity detection
- Better state management
- Async operations support
- Comprehensive monitoring

Author: AI Assistant
Version: 33.1 (Improved)
"""

import time
import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import traceback

from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
from dotenv import load_dotenv
import requests
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arbitrage_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
STATE_FILE = "state.json"
CONFIG_FILE = "bot_config.json"
OPPORTUNITIES_CACHE_FILE = "opportunities_cache.json"

@dataclass
class OpportunityData:
    """Data class for arbitrage opportunities"""
    net_profit_usd: float
    loan_asset: str
    loan_amount: int
    strategy_params: Dict[str, Any]
    confidence_score: float
    estimated_gas: int
    dex_route: List[str]
    timestamp: datetime

@dataclass
class StrategyMetrics:
    """Metrics for strategy performance tracking"""
    total_executions: int = 0
    successful_executions: int = 0
    total_profit: float = 0.0
    total_gas_used: int = 0
    average_execution_time: float = 0.0
    last_execution: Optional[datetime] = None

class ConfigManager:
    """Enhanced configuration management"""
    
    def __init__(self):
        load_dotenv()
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment and config file"""
        config = {
            # Blockchain settings
            'rpc_url': os.getenv('RPC_URL'),
            'private_key': 'DISABLED_FOR_SECURITY'  # Use SecureTransactionSigner instead,
            'incubator_address': os.getenv('INCUBATOR_ADDRESS'),
            'executor_address': os.getenv('EXECUTOR_ADDRESS'),
            
            # Gas settings
            'max_priority_fee_gwei': float(os.getenv('MAX_PRIORITY_FEE_GWEI', '2.0')),
            'max_fee_gwei': float(os.getenv('MAX_FEE_GWEI', '100')),
            
            # Bot settings
            'min_profit_usd': float(os.getenv('MIN_PROFIT_USD', '50')),
            'scan_interval_seconds': int(os.getenv('SCAN_INTERVAL_SECONDS', '15')),
            'max_concurrent_strategies': int(os.getenv('MAX_CONCURRENT_STRATEGIES', '5')),
            
            # DEX addresses
            'uniswap_v2_router': os.getenv('UNISWAP_V2_ROUTER'),
            'sushiswap_router': os.getenv('SUSHISWAP_ROUTER'),
            
            # Token addresses
            'weth': os.getenv('WETH'),
            'dai': os.getenv('DAI'),
            'usdc': os.getenv('USDC'),
        }
        
        # Load additional config from file if exists
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                logger.warning(f"Could not load config file: {e}")
        
        return config
    
    def _validate_config(self):
        """Validate required configuration"""
        required_fields = [
            'rpc_url', 'private_key', 'incubator_address', 'executor_address'
        ]
        
        missing_fields = [field for field in required_fields if not self.config.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        # Validate addresses
        try:
            Web3.to_checksum_address(self.config['incubator_address'])
            Web3.to_checksum_address(self.config['executor_address'])
        except Exception as e:
            raise ValueError(f"Invalid contract address: {e}")

class ABIManager:
    """Manage ABI loading with fallback mechanisms"""
    
    def __init__(self):
        self.abi_cache = {}
    
    def load_abi(self, filename: str) -> List[Dict]:
        """Load ABI with caching and error handling"""
        if filename in self.abi_cache:
            return self.abi_cache[filename]
        
        # Try different possible locations
        possible_paths = [
            os.path.join("abi", filename),
            os.path.join("contracts", "abi", filename),
            filename
        ]
        
        for path in possible_paths:
            try:
                with open(path, 'r') as f:
                    abi = json.load(f)
                    self.abi_cache[filename] = abi
                    logger.info(f"Loaded ABI from {path}")
                    return abi
            except FileNotFoundError:
                continue
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {path}: {e}")
                continue
        
        raise FileNotFoundError(f"Could not find ABI file: {filename}")

class OpportunityScanner:
    """Enhanced opportunity scanning with multiple DEX support"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.web3 = Web3(Web3.HTTPProvider(config['rpc_url']))
        self.opportunities_cache = self._load_opportunities_cache()
    
    def _load_opportunities_cache(self) -> Dict:
        """Load cached opportunities"""
        try:
            if os.path.exists(OPPORTUNITIES_CACHE_FILE):
                with open(OPPORTUNITIES_CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load opportunities cache: {e}")
        return {}
    
    def _save_opportunities_cache(self):
        """Save opportunities cache"""
        try:
            with open(OPPORTUNITIES_CACHE_FILE, 'w') as f:
                json.dump(self.opportunities_cache, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save opportunities cache: {e}")
    
    async def scan_for_opportunities(self) -> Optional[OpportunityData]:
        """Enhanced opportunity scanning"""
        try:
            logger.info("Scanning for arbitrage opportunities...")
            
            # Get current market data
            market_data = await self._fetch_market_data()
            if not market_data:
                return None
            
            # Analyze opportunities
            opportunities = await self._analyze_opportunities(market_data)
            
            if opportunities:
                best_opportunity = max(opportunities, key=lambda x: x.confidence_score)
                
                if best_opportunity.net_profit_usd >= self.config['min_profit_usd']:
                    logger.info(f"Found profitable opportunity: ${best_opportunity.net_profit_usd:.2f}")
                    return best_opportunity
            
            logger.debug("No profitable opportunities found")
            return None
            
        except Exception as e:
            logger.error(f"Error scanning opportunities: {e}")
            return None
    
    async def _fetch_market_data(self) -> Optional[Dict]:
        """Fetch current market data from multiple sources"""
        try:
            # This would integrate with real DEX APIs
            # For now, return mock data
            return {
                'uniswap_v2': {'DAI/WETH': 0.0005, 'USDC/WETH': 0.0005},
                'sushiswap': {'DAI/WETH': 0.00051, 'USDC/WETH': 0.00049},
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return None
    
    async def _analyze_opportunities(self, market_data: Dict) -> List[OpportunityData]:
        """Analyze market data for arbitrage opportunities"""
        opportunities = []
        
        try:
            # Example analysis logic
            uniswap_price = market_data['uniswap_v2']['DAI/WETH']
            sushiswap_price = market_data['sushiswap']['DAI/WETH']
            
            price_diff = abs(uniswap_price - sushiswap_price)
            profit_percentage = (price_diff / min(uniswap_price, sushiswap_price)) * 100
            
            if profit_percentage > 0.1:  # 0.1% minimum profit
                loan_amount = self.web3.to_wei(1000, 'ether')  # 1000 DAI
                estimated_profit = loan_amount * price_diff
                estimated_profit_usd = float(self.web3.from_wei(estimated_profit, 'ether')) * 1  # Assuming 1 DAI = 1 USD
                
                opportunity = OpportunityData(
                    net_profit_usd=estimated_profit_usd,
                    loan_asset=self.config['dai'],
                    loan_amount=loan_amount,
                    strategy_params={
                        'dex_pair': 'DAI/WETH',
                        'exchange_route': ['UniswapV2', 'Sushiswap'],
                        'price_diff': price_diff,
                        'profit_percentage': profit_percentage
                    },
                    confidence_score=min(profit_percentage * 10, 100),
                    estimated_gas=300000,
                    dex_route=['UniswapV2', 'Sushiswap'],
                    timestamp=datetime.now()
                )
                
                opportunities.append(opportunity)
        
        except Exception as e:
            logger.error(f"Error analyzing opportunities: {e}")
        
        return opportunities

class EnhancedArbitrageAgent:
    """Enhanced arbitrage agent with improved functionality"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.abi_manager = ABIManager()
        self.opportunity_scanner = OpportunityScanner(self.config)
        
        # Initialize Web3
        self.web3 = Web3(Web3.HTTPProvider(self.config['rpc_url']))
        # SECURITY: Use secure transaction signer instead of private key
try:
    from secure_transaction_signer import SecureTransactionSigner
    self.signer = SecureTransactionSigner()
    self.account = self.signer.get_account()
except ImportError:
    raise RuntimeError("SECURITY ERROR: SecureTransactionSigner not available.")
        self.web3.eth.default_account = self.account.address
        
        # Load state and metrics
        self.state = self._load_state()
        self.metrics = self._load_metrics()
        
        # Initialize contracts
        self._initialize_contracts()
        
        # Setup event monitoring
        self._setup_event_monitoring()
        
        logger.info(f"Enhanced Arbitrage Agent initialized. Wallet: {self.account.address}")
    
    def _load_state(self) -> Dict:
        """Load agent state"""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
        
        return {
            'proposed_strategies': [],
            'strategy_execution_details': {},
            'last_processed_block': self.web3.eth.block_number,
            'total_strategies_deployed': 0,
            'total_profit_earned': 0.0
        }
    
    def _save_state(self):
        """Save agent state"""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=4, default=str)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def _load_metrics(self) -> Dict[str, StrategyMetrics]:
        """Load strategy metrics"""
        try:
            if os.path.exists("metrics.json"):
                with open("metrics.json", 'r') as f:
                    data = json.load(f)
                    return {k: StrategyMetrics(**v) for k, v in data.items()}
        except Exception as e:
            logger.warning(f"Could not load metrics: {e}")
        return {}
    
    def _save_metrics(self):
        """Save strategy metrics"""
        try:
            data = {k: v.__dict__ for k, v in self.metrics.items()}
            with open("metrics.json", 'w') as f:
                json.dump(data, f, indent=4, default=str)
        except Exception as e:
            logger.error(f"Could not save metrics: {e}")
    
    def _initialize_contracts(self):
        """Initialize contract instances"""
        try:
            # Load ABIs
            incubator_abi = self.abi_manager.load_abi("StrategyIncubatorV33.json")
            executor_abi = self.abi_manager.load_abi("ArbitrageExecutorV33.json")
            strategy_abi = self.abi_manager.load_abi("GenericStrategy.json")
            
            # Initialize contracts
            self.incubator = self.web3.eth.contract(
                address=Web3.to_checksum_address(self.config['incubator_address']),
                abi=incubator_abi
            )
            
            self.executor = self.web3.eth.contract(
                address=Web3.to_checksum_address(self.config['executor_address']),
                abi=executor_abi
            )
            
            self.strategy_abi = strategy_abi
            
            # Load bytecode
            bytecode_path = os.path.join("bytecode", "GenericStrategy.bin")
            if os.path.exists(bytecode_path):
                with open(bytecode_path, 'r') as f:
                    self.strategy_bytecode = f.read().strip()
            else:
                logger.warning("Strategy bytecode not found, deployment will fail")
                self.strategy_bytecode = None
            
        except Exception as e:
            logger.error(f"Error initializing contracts: {e}")
            raise
    
    def _setup_event_monitoring(self):
        """Setup event monitoring"""
        try:
            from_block = self.state.get('last_processed_block', 'latest')
            if isinstance(from_block, int):
                from_block = max(from_block - 10, 0)  # Start a few blocks back for safety
            
            self.event_filter = self.incubator.events.StrategyStatusChanged.create_filter(
                fromBlock=from_block
            )
            
            logger.info(f"Event monitoring setup from block {from_block}")
            
        except Exception as e:
            logger.error(f"Error setting up event monitoring: {e}")
            self.event_filter = None
    
    def _send_transaction(self, tx: Dict) -> Optional[Dict]:
        """Enhanced transaction sending with better error handling"""
        try:
            # Add nonce
            tx['nonce'] = self.web3.eth.get_transaction_count(self.account.address)
            
            # EIP-1559 gas settings
            latest_block = self.web3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', 0)
            
            max_priority_fee_per_gas = self.web3.to_wei(self.config['max_priority_fee_gwei'], 'gwei')
            max_fee_per_gas = base_fee + max_priority_fee_per_gas
            
            # Cap max fee
            max_fee_cap = self.web3.to_wei(self.config['max_fee_gwei'], 'gwei')
            if max_fee_per_gas > max_fee_cap:
                max_fee_per_gas = max_fee_cap
                max_priority_fee_per_gas = max(max_fee_per_gas - base_fee, self.web3.to_wei('1', 'gwei'))
            
            tx['maxPriorityFeePerGas'] = max_priority_fee_per_gas
            tx['maxFeePerGas'] = max_fee_per_gas
            
            # Estimate gas with buffer
            try:
                estimated_gas = self.web3.eth.estimate_gas(tx)
                tx['gas'] = int(estimated_gas * 1.2)  # 20% buffer
            except Exception as e:
                logger.warning(f"Gas estimation failed: {e}, using default")
                tx['gas'] = 500000
            
            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.config['private_key'])
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt with timeout
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                logger.info(f"Transaction successful. Gas used: {receipt['gasUsed']}")
                return receipt
            else:
                logger.error(f"Transaction failed. Receipt: {receipt}")
                return None
                
        except ContractLogicError as e:
            logger.error(f"Contract logic error: {e}")
            return None
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            logger.debug(traceback.format_exc())
            return None
    
    async def deploy_and_propose_strategy(self, opportunity: OpportunityData) -> bool:
        """Deploy and propose strategy with enhanced error handling"""
        try:
            logger.info(f"Deploying strategy for ${opportunity.net_profit_usd:.2f} opportunity")
            
            if not self.strategy_bytecode:
                logger.error("Strategy bytecode not available")
                return False
            
            # Create contract instance
            strategy_contract = self.web3.eth.contract(
                abi=self.strategy_abi,
                bytecode=self.strategy_bytecode
            )
            
            # Build deployment transaction
            construct_txn = strategy_contract.constructor().build_transaction({
                'from': self.account.address,
            })
            
            # Deploy contract
            receipt = self._send_transaction(construct_txn)
            if not receipt or not receipt.get('contractAddress'):
                logger.error("Strategy deployment failed")
                return False
            
            strategy_address = receipt['contractAddress']
            logger.info(f"Strategy deployed at: {strategy_address}")
            
            # Check if already proposed
            if strategy_address in self.state['proposed_strategies']:
                logger.info(f"Strategy {strategy_address} already proposed")
                return True
            
            # Store execution details
            self.state['strategy_execution_details'][strategy_address] = {
                'loan_asset': opportunity.loan_asset,
                'loan_amount': opportunity.loan_amount,
                'opportunity_data': opportunity.__dict__
            }
            
            # Propose strategy
            propose_tx = self.incubator.functions.proposeStrategy(strategy_address).build_transaction({
                'from': self.account.address,
            })
            
            if self._send_transaction(propose_tx):
                self.state['proposed_strategies'].append(strategy_address)
                self.state['total_strategies_deployed'] += 1
                self._save_state()
                logger.info(f"Strategy {strategy_address} successfully proposed")
                return True
            else:
                logger.error(f"Failed to propose strategy {strategy_address}")
                return False
                
        except Exception as e:
            logger.error(f"Error deploying strategy: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    async def handle_strategy_events(self):
        """Handle strategy status change events"""
        if not self.event_filter:
            return
        
        try:
            logger.debug("Checking for strategy events...")
            new_events = self.event_filter.get_new_entries()
            
            if not new_events:
                return
            
            logger.info(f"Processing {len(new_events)} new events")
            
            for event in new_events:
                await self._process_strategy_event(event)
                self.state['last_processed_block'] = event['blockNumber']
            
            self._save_state()
            
        except Exception as e:
            logger.error(f"Error handling events: {e}")
            logger.debug(traceback.format_exc())
    
    async def _process_strategy_event(self, event):
        """Process individual strategy event"""
        try:
            strategy_id = event['args']['strategyId']
            new_status = event['args']['newStatus']
            
            logger.info(f"Strategy {strategy_id} status changed to {new_status}")
            
            # Handle LiveTesting status (assuming status 2)
            if new_status == 2:
                await self._execute_live_test(strategy_id)
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    
    async def _execute_live_test(self, strategy_id: int):
        """Execute live test for strategy"""
        try:
            logger.info(f"Executing live test for strategy {strategy_id}")
            
            # Get strategy details
            strategy_data = self.incubator.functions.getStrategy(strategy_id).call()
            strategy_address = strategy_data[0]
            
            # Get execution parameters
            execution_params = self.state['strategy_execution_details'].get(strategy_address)
            if not execution_params:
                logger.error(f"No execution parameters for strategy {strategy_address}")
                return
            
            # Execute live test
            exec_tx = self.executor.functions.executeLiveTestForIncubator(
                strategy_id,
                execution_params['loan_asset'],
                execution_params['loan_amount']
            ).build_transaction({
                'from': self.account.address,
            })
            
            start_time = time.time()
            receipt = self._send_transaction(exec_tx)
            execution_time = time.time() - start_time
            
            # Update metrics
            if strategy_address not in self.metrics:
                self.metrics[strategy_address] = StrategyMetrics()
            
            metrics = self.metrics[strategy_address]
            metrics.total_executions += 1
            metrics.total_gas_used += receipt['gasUsed'] if receipt else 0
            metrics.last_execution = datetime.now()
            
            if receipt:
                metrics.successful_executions += 1
                logger.info(f"Live test successful for strategy {strategy_id}")
            else:
                logger.error(f"Live test failed for strategy {strategy_id}")
            
            # Update average execution time
            if metrics.total_executions > 0:
                metrics.average_execution_time = (
                    (metrics.average_execution_time * (metrics.total_executions - 1) + execution_time) /
                    metrics.total_executions
                )
            
            self._save_metrics()
            
        except Exception as e:
            logger.error(f"Error executing live test: {e}")
            logger.debug(traceback.format_exc())
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        total_strategies = len(self.state['proposed_strategies'])
        total_executions = sum(m.total_executions for m in self.metrics.values())
        successful_executions = sum(m.successful_executions for m in self.metrics.values())
        total_gas_used = sum(m.total_gas_used for m in self.metrics.values())
        
        return {
            'total_strategies_deployed': total_strategies,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
            'total_gas_used': total_gas_used,
            'total_profit_earned': self.state.get('total_profit_earned', 0),
            'uptime_hours': (datetime.now() - datetime.fromtimestamp(self.state.get('start_time', time.time()))).total_seconds() / 3600
        }
    
    async def run(self):
        """Main bot loop with enhanced error handling"""
        logger.info("🚀 Starting Enhanced Arbitrage Agent V33")
        
        self.state['start_time'] = time.time()
        self._save_state()
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                cycle_start = time.time()
                logger.info(f"--- Agent Cycle Start ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
                
                # Scan for opportunities
                opportunity = await self.opportunity_scanner.scan_for_opportunities()
                
                if opportunity and opportunity.net_profit_usd >= self.config['min_profit_usd']:
                    success = await self.deploy_and_propose_strategy(opportunity)
                    if success:
                        consecutive_errors = 0  # Reset error counter on success
                
                # Handle events
                await self.handle_strategy_events()
                
                # Log performance summary periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    summary = self.get_performance_summary()
                    logger.info(f"Performance Summary: {summary}")
                
                cycle_time = time.time() - cycle_start
                sleep_time = max(0, self.config['scan_interval_seconds'] - cycle_time)
                
                logger.info(f"--- Cycle completed in {cycle_time:.2f}s. Sleeping {sleep_time:.2f}s ---")
                await asyncio.sleep(sleep_time)
                
                consecutive_errors = 0  # Reset on successful cycle
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Cycle error ({consecutive_errors}/{max_consecutive_errors}): {e}")
                logger.debug(traceback.format_exc())
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical("Too many consecutive errors, stopping bot")
                    break
                
                # Exponential backoff on errors
                error_sleep = min(60, 2 ** consecutive_errors)
                logger.info(f"Sleeping {error_sleep}s before retry")
                await asyncio.sleep(error_sleep)
        
        logger.info("Bot shutdown complete")

async def main():
    """Main entry point"""
    try:
        agent = EnhancedArbitrageAgent()
        await agent.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        logger.debug(traceback.format_exc())
        return 1
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))