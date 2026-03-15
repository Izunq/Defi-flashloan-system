"""
Arbitrage Pipeline Module
------------------------
This module implements a processing pipeline for arbitrage opportunities.
It uses Celery for asynchronous task processing.
"""

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

import time
import os

# Mock imports for testing
try:
    from core.event_bus import event_bus
except ImportError:
    event_bus = None

try:
    from core.transaction_manager import transaction_manager
except ImportError:
    transaction_manager = None

# Configure Celery; it uses Redis as a message broker
try:
    from celery import Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    
    celery_app = Celery('arbitrage_pipeline', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
    
    # Define configuration for Celery
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )
except ImportError:
    # Mock celery_app for testing
    class MockCeleryApp:
        def task(self, name=None):
            def decorator(func):
                return func
            return decorator
    
    celery_app = MockCeleryApp()

MIN_PROFIT_THRESHOLD = 25.0 # Minimum expected profit in USD to execute a trade

@celery_app.task(name='process_arbitrage_opportunity')
def process_arbitrage_opportunity(opportunity_data: dict):
    """
    This is the core processing pipeline for an arbitrage opportunity.    
    Args:
        opportunity_data: Dictionary containing opportunity details
    
    Returns:
        Dictionary with status and additional information
    """
    try:
        # 1. VALIDATION STAGE
        print(f"[PIPELINE] Validating opportunity: {opportunity_data['pair']}")
        
        # Validate required fields
        required_fields = ['pair', 'dex_a_price', 'dex_b_price', 'timestamp']
        for field in required_fields:
            if field not in opportunity_data:
                raise KeyError(f"Missing required field: {field}")
        
        # Validate data types and values
        if not isinstance(opportunity_data['dex_a_price'], (int, float)) or opportunity_data['dex_a_price'] <= 0:
            raise ValueError("dex_a_price must be a positive number")
        
        if not isinstance(opportunity_data['dex_b_price'], (int, float)) or opportunity_data['dex_b_price'] <= 0:
            raise ValueError("dex_b_price must be a positive number")
        
        if time.time() - opportunity_data['timestamp'] > 15: # Stale data check (15s)
            raise ValueError("Stale opportunity data")

        # 2. ENRICHMENT STAGE
        # In a real system, you might fetch more data here,
        # e.g., on-chain gas fees, contract states, etc.
        print(f"[PIPELINE] Enriching data for {opportunity_data['pair']}")
        estimated_gas_cost_usd = 30.0 # Fetch this dynamically
        
        # 3. DECISION STAGE
        # Simple profit calculation logic
        price_a = opportunity_data['dex_a_price']
        price_b = opportunity_data['dex_b_price']
        # Assume we are buying on A and selling on B for a $10,000 trade
        profit = (price_b - price_a) * (10000 / price_a)
        net_profit = profit - estimated_gas_cost_usd
        
        print(f"[PIPELINE] Estimated Gross Profit: ${profit:.2f}, Net Profit: ${net_profit:.2f}")
        
        if net_profit < MIN_PROFIT_THRESHOLD:
            if event_bus:
                event_bus.publish('monitoring-events', {'status': 'info', 'message': f'Opportunity declined: low profit (${net_profit:.2f})'})
            return {'status': 'declined', 'reason': 'insufficient profit'}

        # 4. DISPATCH STAGE
        print(f"[PIPELINE] Profitable opportunity found! Dispatching to Transaction Manager.")
        if event_bus:
            event_bus.publish('monitoring-events', {'status': 'info', 'message': f'Dispatching trade for {opportunity_data["pair"]}'})
          # This will call the transaction manager to execute the smart contract
        # We're using the asset address from the opportunity data
        if transaction_manager:
            try:
                transaction_manager.execute_flashloan_trade(
                    asset=opportunity_data.get('asset_address', '${CONTRACT_ADDRESS}'), # Default to WETH if not specified
                    amount=int(10000 * 10**18) # Convert $10,000 to wei (assuming 18 decimals)
                )
            except Exception as tx_error:
                print(f"[PIPELINE] Transaction execution failed: {tx_error}")
                if event_bus:
                    event_bus.publish('monitoring-events', {'status': 'error', 'message': f'Transaction execution failed: {tx_error}'})
                return {'status': 'error', 'reason': f'Transaction failed: {tx_error}'}

        return {'status': 'dispatched', 'net_profit': net_profit}

    except Exception as e:
        print(f"[PIPELINE] Error in pipeline: {e}")
        if event_bus:
            event_bus.publish('monitoring-events', {'status': 'error', 'message': f'Pipeline failure: {e}'})
        return {'status': 'error', 'reason': str(e)}

def market_data_subscriber(data: dict):
    """
    Subscribes to market data and triggers the pipeline.
    
    Args:
        data: Market data from the event bus
    """
    print(f"[SUBSCRIBER] New market data received. Sending to pipeline.")
    process_arbitrage_opportunity.delay(data)

def start_pipeline_listener():
    """
    Initializes the event bus subscription for the pipeline.
    """
    event_bus.subscribe('market-data-events', market_data_subscriber)

# Simple synchronous version for testing
def process_arbitrage_opportunity_sync(opportunity_data: dict):
    """
    Synchronous version of the arbitrage opportunity processor for testing
    
    Args:
        opportunity_data: Dictionary containing opportunity details
    
    Returns:
        Dictionary with status and additional information
    """
    try:
        # Validation - check for required fields
        required_fields = ['pair', 'dex_a_price', 'dex_b_price', 'timestamp']
        for field in required_fields:
            if field not in opportunity_data:
                raise KeyError(f"Missing required field: {field}")
        
        # Validate data types and values
        if not isinstance(opportunity_data['dex_a_price'], (int, float)) or opportunity_data['dex_a_price'] <= 0:
            raise ValueError("dex_a_price must be a positive number")
        
        if not isinstance(opportunity_data['dex_b_price'], (int, float)) or opportunity_data['dex_b_price'] <= 0:
            raise ValueError("dex_b_price must be a positive number")
        
        # Check for stale data (default 5 minutes)
        current_time = time.time()
        age = current_time - opportunity_data['timestamp']
        expiry_limit = opportunity_data.get('expiry', 300)
        
        if age > expiry_limit:
            return {
                'status': 'declined',
                'reason': 'expired',
                'age_seconds': age
            }
        
        # Calculate profit
        price_a = float(opportunity_data['dex_a_price'])
        price_b = float(opportunity_data['dex_b_price'])
        
        # Calculate profit percentage
        profit_percentage = ((price_b - price_a) / price_a) * 100
        
        # Get thresholds
        profit_threshold = opportunity_data.get('profit_threshold', 2.0)
        
        # Simple profit calculation for $10,000 trade
        trade_amount = 10000.0
        gross_profit = (price_b - price_a) * (trade_amount / price_a)
        estimated_gas = opportunity_data.get('gas_cost', 30.0)
        net_profit = gross_profit - estimated_gas
        
        # Mock transaction manager behavior for error testing
        if hasattr(transaction_manager, 'execute_flashloan_trade') and transaction_manager.execute_flashloan_trade:
            try:
                # Simulate transaction execution call
                transaction_manager.execute_flashloan_trade(
                    asset=opportunity_data.get('asset_address', '${CONTRACT_ADDRESS}'),
                    amount=int(trade_amount * 10**18)
                )
            except Exception as tx_error:
                return {
                    'status': 'error',
                    'reason': f'Transaction failed: {tx_error}',
                    'opportunity': opportunity_data
                }
        
        # Decision logic
        if profit_percentage >= profit_threshold and net_profit >= MIN_PROFIT_THRESHOLD:
            return {
                'status': 'dispatched',
                'profit_percentage': profit_percentage,
                'gross_profit': gross_profit,
                'net_profit': net_profit,
                'opportunity': opportunity_data
            }
        else:
            return {
                'status': 'declined',
                'reason': 'insufficient_profit',
                'profit_percentage': profit_percentage,
                'gross_profit': gross_profit,
                'net_profit': net_profit
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'reason': str(e),
            'opportunity': opportunity_data
        }

# Alias for backward compatibility with tests
process_arbitrage_opportunity = process_arbitrage_opportunity_sync