#!/usr/bin/env python3
# =================================================================================================
# DATABASE UTILITIES FOR AIRFLOW
# =================================================================================================

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import great_expectations as ge
from airflow.models import Variable

# Import database manager
import sys
sys.path.append('/opt/airflow')
from database_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("database_utils")

# Global database manager instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """
    Get database manager instance
    
    Returns:
        Database manager instance
    """
    global _db_manager
    
    if _db_manager is None:
        # Get database configuration path
        db_config_path = Variable.get("db_config_path", default="/opt/airflow/database_config.yaml")
        
        # Initialize database manager
        _db_manager = DatabaseManager(db_config_path)
        logger.info("Initialized database manager")
    
    return _db_manager

def validate_market_data(market_data: List[Dict]) -> Dict:
    """
    Validate market data using Great Expectations
    
    Args:
        market_data: Market data to validate
        
    Returns:
        Validation results
    """
    # Get database manager
    db_manager = get_db_manager()
    
    # Define expectations
    expectations = [
        {
            "expectation_type": "expect_column_to_exist",
            "column": "exchange"
        },
        {
            "expectation_type": "expect_column_to_exist",
            "column": "token_pair"
        },
        {
            "expectation_type": "expect_column_to_exist",
            "column": "price"
        },
        {
            "expectation_type": "expect_column_to_exist",
            "column": "volume_24h"
        },
        {
            "expectation_type": "expect_column_to_exist",
            "column": "liquidity"
        },
        {
            "expectation_type": "expect_column_to_exist",
            "column": "timestamp"
        },
        {
            "expectation_type": "expect_column_values_to_not_be_null",
            "column": "exchange"
        },
        {
            "expectation_type": "expect_column_values_to_not_be_null",
            "column": "token_pair"
        },
        {
            "expectation_type": "expect_column_values_to_not_be_null",
            "column": "price"
        },
        {
            "expectation_type": "expect_column_values_to_be_of_type",
            "column": "price",
            "type_": "float"
        },
        {
            "expectation_type": "expect_column_values_to_be_between",
            "column": "price",
            "min_value": 0,
            "max_value": 1000000
        },
        {
            "expectation_type": "expect_column_values_to_be_of_type",
            "column": "volume_24h",
            "type_": "float"
        },
        {
            "expectation_type": "expect_column_values_to_be_between",
            "column": "volume_24h",
            "min_value": 0,
            "max_value": 1000000000000
        },
        {
            "expectation_type": "expect_column_values_to_be_of_type",
            "column": "liquidity",
            "type_": "float"
        },
        {
            "expectation_type": "expect_column_values_to_be_between",
            "column": "liquidity",
            "min_value": 0,
            "max_value": 1000000000000
        }
    ]
    
    # Validate data
    validation_results = db_manager.validate_data(market_data, expectations)
    
    return validation_results

def validate_arbitrage_opportunities(opportunities: List[Dict]) -> Dict:
    """
    Validate arbitrage opportunities using Great Expectations
    
    Args:
        opportunities: Arbitrage opportunities to validate
        
    Returns:
        Validation results
    """
    # Get database manager
    db_manager = get_db_manager()
    
    # Define expectations
    expectations = [
        {
            "expectation_type": "expect_column_to_exist",
            "column": "token_pair"
        },
        {
            "expectation_type": "expect_column_to_exist",
            "column": "exchange_a"
        },
        {
            "expectation_type": "expect_column_to_exist",
            "column": "exchange_b"
        },
        {
            "expectation_type": "expect_column_to_exist",
            "column": "price_difference"
        },
        {
            "expectation_type": "expect_column_to_exist",
            "column": "potential_profit"
        },
        {
            "expectation_type": "expect_column_to_exist",
            "column": "timestamp"
        },
        {
            "expectation_type": "expect_column_values_to_not_be_null",
            "column": "token_pair"
        },
        {
            "expectation_type": "expect_column_values_to_not_be_null",
            "column": "exchange_a"
        },
        {
            "expectation_type": "expect_column_values_to_not_be_null",
            "column": "exchange_b"
        },
        {
            "expectation_type": "expect_column_values_to_not_be_null",
            "column": "price_difference"
        },
        {
            "expectation_type": "expect_column_values_to_be_of_type",
            "column": "price_difference",
            "type_": "float"
        },
        {
            "expectation_type": "expect_column_values_to_be_between",
            "column": "price_difference",
            "min_value": 0,
            "max_value": 1000000
        },
        {
            "expectation_type": "expect_column_values_to_be_of_type",
            "column": "potential_profit",
            "type_": "float"
        },
        {
            "expectation_type": "expect_column_values_to_be_between",
            "column": "potential_profit",
            "min_value": 0,
            "max_value": 1000000
        }
    ]
    
    # Validate data
    validation_results = db_manager.validate_data(opportunities, expectations)
    
    return validation_results

def get_latest_market_data(token_pair: str, exchange: str) -> Optional[Dict]:
    """
    Get latest market data from Redis cache
    
    Args:
        token_pair: Token pair
        exchange: Exchange name
        
    Returns:
        Market data or None if not found
    """
    # Get database manager
    db_manager = get_db_manager()
    
    # Get data from Redis
    key = f"market:prices:{token_pair}:{exchange}"
    data = db_manager.cache_hash_get_all(key)
    
    if not data:
        return None
    
    # Convert types
    if "price" in data:
        data["price"] = float(data["price"])
    
    if "volume_24h" in data:
        data["volume_24h"] = float(data["volume_24h"])
    
    if "liquidity" in data:
        data["liquidity"] = float(data["liquidity"])
    
    # Add token pair and exchange
    data["token_pair"] = token_pair
    data["exchange"] = exchange
    
    return data

def get_arbitrage_opportunities(token_pair: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Get arbitrage opportunities from PostgreSQL
    
    Args:
        token_pair: Token pair to filter by
        limit: Maximum number of opportunities to return
        
    Returns:
        List of arbitrage opportunities
    """
    # Get database manager
    db_manager = get_db_manager()
    
    # Build query
    query = """
    SELECT id, token_pair, exchange_a, exchange_b, price_difference, potential_profit, timestamp, executed
    FROM arbitrage_opportunities
    WHERE executed = false
    """
    
    params = {}
    
    if token_pair:
        query += " AND token_pair = %(token_pair)s"
        params["token_pair"] = token_pair
    
    query += " ORDER BY potential_profit DESC LIMIT %(limit)s"
    params["limit"] = limit
    
    # Execute query
    results = db_manager.execute_query(query, params)
    
    return results

def mark_arbitrage_executed(opportunity_id: str, tx_id: str) -> bool:
    """
    Mark arbitrage opportunity as executed
    
    Args:
        opportunity_id: Opportunity ID
        tx_id: Transaction ID
        
    Returns:
        True if successful
    """
    # Get database manager
    db_manager = get_db_manager()
    
    # Update opportunity
    query = """
    UPDATE arbitrage_opportunities
    SET executed = true, execution_tx_id = %(tx_id)s
    WHERE id = %(opportunity_id)s
    """
    
    params = {
        "opportunity_id": opportunity_id,
        "tx_id": tx_id
    }
    
    # Execute query
    db_manager.execute_query(query, params)
    
    return True

def store_transaction(tx_data: Dict) -> str:
    """
    Store transaction in PostgreSQL
    
    Args:
        tx_data: Transaction data
        
    Returns:
        Transaction ID
    """
    # Get database manager
    db_manager = get_db_manager()
    
    # Generate UUID
    import uuid
    tx_id = str(uuid.uuid4())
    
    # Insert transaction
    query = """
    INSERT INTO transactions
    (id, tx_hash, from_address, to_address, value, gas_price, gas_used, status, block_number, timestamp, data)
    VALUES
    (%(id)s, %(tx_hash)s, %(from_address)s, %(to_address)s, %(value)s, %(gas_price)s, %(gas_used)s, %(status)s, %(block_number)s, %(timestamp)s, %(data)s)
    """
    
    params = {
        "id": tx_id,
        "tx_hash": tx_data.get("tx_hash"),
        "from_address": tx_data.get("from_address"),
        "to_address": tx_data.get("to_address"),
        "value": tx_data.get("value"),
        "gas_price": tx_data.get("gas_price"),
        "gas_used": tx_data.get("gas_used"),
        "status": tx_data.get("status"),
        "block_number": tx_data.get("block_number"),
        "timestamp": tx_data.get("timestamp") or datetime.now(),
        "data": tx_data.get("data")
    }
    
    # Execute query
    db_manager.execute_query(query, params)
    
    return tx_id

def close_db_connections():
    """Close database connections"""
    global _db_manager
    
    if _db_manager:
        _db_manager.close()
        _db_manager = None
        logger.info("Closed database connections")