#!/usr/bin/env python3
# =================================================================================================
# MARKET DATA ETL DAG
# =================================================================================================

import os
import json
import logging
import pendulum
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.redis.operators.redis_publish import RedisPublishOperator
from airflow.models import Variable

# Import custom modules
import sys
sys.path.append('/opt/airflow/dags/utils')
from database_utils import get_db_manager, validate_market_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("market_data_etl")

# Default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

# Define DAG
dag = DAG(
    'market_data_etl',
    default_args=default_args,
    description='ETL pipeline for market data',
    schedule_interval='*/10 * * * *',  # Every 10 minutes
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    catchup=False,
    tags=['market_data', 'etl'],
    max_active_runs=1
)

# Define tasks
def extract_market_data(**context):
    """Extract market data from exchanges"""
    # Get exchanges from configuration
    exchanges = Variable.get("market_data_exchanges", deserialize_json=True)
    
    # Initialize results
    results = []
    
    # Extract data from each exchange
    for exchange in exchanges:
        try:
            # Get exchange API configuration
            api_url = exchange.get("api_url")
            api_key = exchange.get("api_key")
            api_secret = exchange.get("api_secret")
            
            # Get token pairs to extract
            token_pairs = exchange.get("token_pairs", [])
            
            # Initialize exchange client
            if exchange.get("name") == "binance":
                from binance.client import Client
                client = Client(api_key, api_secret)
                
                # Get market data for each token pair
                for token_pair in token_pairs:
                    # Get ticker data
                    ticker = client.get_ticker(symbol=token_pair)
                    
                    # Get 24h stats
                    stats = client.get_24hr_ticker(symbol=token_pair)
                    
                    # Get order book
                    order_book = client.get_order_book(symbol=token_pair, limit=10)
                    
                    # Calculate liquidity (sum of top 10 bids and asks)
                    liquidity = sum(float(bid[0]) * float(bid[1]) for bid in order_book['bids']) + \
                                sum(float(ask[0]) * float(ask[1]) for ask in order_book['asks'])
                    
                    # Add to results
                    results.append({
                        "exchange": exchange.get("name"),
                        "token_pair": token_pair,
                        "price": float(ticker['lastPrice']),
                        "volume_24h": float(stats['volume']),
                        "liquidity": liquidity,
                        "timestamp": datetime.now().isoformat()
                    })
            
            elif exchange.get("name") == "coinbase":
                import requests
                
                # Get market data for each token pair
                for token_pair in token_pairs:
                    # Get ticker data
                    response = requests.get(f"{api_url}/products/{token_pair}/ticker")
                    ticker = response.json()
                    
                    # Get 24h stats
                    response = requests.get(f"{api_url}/products/{token_pair}/stats")
                    stats = response.json()
                    
                    # Get order book
                    response = requests.get(f"{api_url}/products/{token_pair}/book?level=2")
                    order_book = response.json()
                    
                    # Calculate liquidity (sum of top 10 bids and asks)
                    liquidity = sum(float(bid[0]) * float(bid[1]) for bid in order_book['bids'][:10]) + \
                                sum(float(ask[0]) * float(ask[1]) for ask in order_book['asks'][:10])
                    
                    # Add to results
                    results.append({
                        "exchange": exchange.get("name"),
                        "token_pair": token_pair,
                        "price": float(ticker['price']),
                        "volume_24h": float(stats['volume']),
                        "liquidity": liquidity,
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Add more exchanges as needed
            
            logger.info(f"Extracted market data from {exchange.get('name')}")
        except Exception as e:
            logger.error(f"Failed to extract market data from {exchange.get('name')}: {e}")
    
    # Push results to XCom
    context['ti'].xcom_push(key='market_data', value=results)
    
    return results

def transform_market_data(**context):
    """Transform market data"""
    # Get market data from XCom
    market_data = context['ti'].xcom_pull(task_ids='extract_market_data', key='market_data')
    
    # Initialize transformed data
    transformed_data = []
    
    # Transform each market data record
    for record in market_data:
        # Standardize token pair format
        token_pair = record.get("token_pair")
        if "-" not in token_pair and "/" not in token_pair:
            # Convert from format like BTCUSDT to BTC-USDT
            if token_pair.endswith("USDT"):
                base = token_pair[:-4]
                quote = "USDT"
            elif token_pair.endswith("BTC"):
                base = token_pair[:-3]
                quote = "BTC"
            elif token_pair.endswith("ETH"):
                base = token_pair[:-3]
                quote = "ETH"
            else:
                # Skip if we can't parse the token pair
                logger.warning(f"Skipping record with unknown token pair format: {token_pair}")
                continue
            
            token_pair = f"{base}-{quote}"
        
        # Standardize timestamp
        timestamp = record.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        # Add transformed record
        transformed_data.append({
            "exchange": record.get("exchange"),
            "token_pair": token_pair,
            "price": record.get("price"),
            "volume_24h": record.get("volume_24h"),
            "liquidity": record.get("liquidity"),
            "timestamp": timestamp.isoformat()
        })
    
    # Validate transformed data
    db_manager = get_db_manager()
    validation_results = validate_market_data(transformed_data)
    
    # Filter out invalid records
    valid_data = [record for i, record in enumerate(transformed_data) if validation_results["results"][i]]
    
    # Log validation results
    logger.info(f"Validated {len(valid_data)} of {len(transformed_data)} market data records")
    
    # Push results to XCom
    context['ti'].xcom_push(key='transformed_market_data', value=valid_data)
    
    return valid_data

def load_market_data_to_clickhouse(**context):
    """Load market data to ClickHouse"""
    # Get transformed market data from XCom
    market_data = context['ti'].xcom_pull(task_ids='transform_market_data', key='transformed_market_data')
    
    # Get database manager
    db_manager = get_db_manager()
    
    # Prepare data for ClickHouse
    clickhouse_data = []
    for record in market_data:
        clickhouse_data.append({
            "token_pair": record.get("token_pair"),
            "exchange": record.get("exchange"),
            "price": record.get("price"),
            "volume_24h": record.get("volume_24h"),
            "liquidity": record.get("liquidity"),
            "timestamp": datetime.fromisoformat(record.get("timestamp"))
        })
    
    # Insert data into ClickHouse
    query = """
    INSERT INTO market_data
    (token_pair, exchange, price, volume_24h, liquidity, timestamp)
    VALUES
    """
    
    db_manager.execute_clickhouse_batch(query, clickhouse_data)
    
    logger.info(f"Loaded {len(clickhouse_data)} market data records to ClickHouse")
    
    return len(clickhouse_data)

def cache_market_data_in_redis(**context):
    """Cache market data in Redis"""
    # Get transformed market data from XCom
    market_data = context['ti'].xcom_pull(task_ids='transform_market_data', key='transformed_market_data')
    
    # Get database manager
    db_manager = get_db_manager()
    
    # Cache data in Redis
    for record in market_data:
        # Cache price
        key = f"market:prices:{record.get('token_pair')}:{record.get('exchange')}"
        db_manager.cache_hash_set(key, "price", record.get("price"))
        db_manager.cache_hash_set(key, "volume_24h", record.get("volume_24h"))
        db_manager.cache_hash_set(key, "liquidity", record.get("liquidity"))
        db_manager.cache_hash_set(key, "timestamp", record.get("timestamp"))
        
        # Set TTL
        db_manager.redis_cluster.expire(key, 300)  # 5 minutes
    
    logger.info(f"Cached {len(market_data)} market data records in Redis")
    
    return len(market_data)

def publish_market_data_to_kafka(**context):
    """Publish market data to Kafka"""
    # Get transformed market data from XCom
    market_data = context['ti'].xcom_pull(task_ids='transform_market_data', key='transformed_market_data')
    
    # Get database manager
    db_manager = get_db_manager()
    
    # Publish data to Kafka
    for record in market_data:
        # Publish to market-data topic
        db_manager.publish_message(
            topic="market-data",
            message=record,
            key=f"{record.get('token_pair')}:{record.get('exchange')}"
        )
    
    logger.info(f"Published {len(market_data)} market data records to Kafka")
    
    return len(market_data)

def detect_arbitrage_opportunities(**context):
    """Detect arbitrage opportunities"""
    # Get transformed market data from XCom
    market_data = context['ti'].xcom_pull(task_ids='transform_market_data', key='transformed_market_data')
    
    # Get database manager
    db_manager = get_db_manager()
    
    # Group data by token pair
    token_pair_data = {}
    for record in market_data:
        token_pair = record.get("token_pair")
        if token_pair not in token_pair_data:
            token_pair_data[token_pair] = []
        
        token_pair_data[token_pair].append(record)
    
    # Detect arbitrage opportunities
    arbitrage_opportunities = []
    
    for token_pair, records in token_pair_data.items():
        # Skip if we have less than 2 exchanges
        if len(records) < 2:
            continue
        
        # Find min and max prices
        min_price_record = min(records, key=lambda x: x.get("price"))
        max_price_record = max(records, key=lambda x: x.get("price"))
        
        # Skip if min and max are the same exchange
        if min_price_record.get("exchange") == max_price_record.get("exchange"):
            continue
        
        # Calculate price difference
        min_price = min_price_record.get("price")
        max_price = max_price_record.get("price")
        price_difference = max_price - min_price
        price_difference_percent = (price_difference / min_price) * 100
        
        # Skip if price difference is too small
        if price_difference_percent < 0.5:  # Less than 0.5%
            continue
        
        # Calculate potential profit
        # Assume we can trade 1 unit of the base token
        potential_profit = price_difference
        
        # Add to arbitrage opportunities
        arbitrage_opportunities.append({
            "token_pair": token_pair,
            "exchange_a": min_price_record.get("exchange"),
            "exchange_b": max_price_record.get("exchange"),
            "price_a": min_price,
            "price_b": max_price,
            "price_difference": price_difference,
            "price_difference_percent": price_difference_percent,
            "potential_profit": potential_profit,
            "timestamp": datetime.now().isoformat()
        })
    
    # Push results to XCom
    context['ti'].xcom_push(key='arbitrage_opportunities', value=arbitrage_opportunities)
    
    logger.info(f"Detected {len(arbitrage_opportunities)} arbitrage opportunities")
    
    return arbitrage_opportunities

def store_arbitrage_opportunities(**context):
    """Store arbitrage opportunities"""
    # Get arbitrage opportunities from XCom
    arbitrage_opportunities = context['ti'].xcom_pull(task_ids='detect_arbitrage_opportunities', key='arbitrage_opportunities')
    
    # Get database manager
    db_manager = get_db_manager()
    
    # Store in PostgreSQL
    for opportunity in arbitrage_opportunities:
        # Insert into PostgreSQL
        query = """
        INSERT INTO arbitrage_opportunities
        (id, token_pair, exchange_a, exchange_b, price_difference, potential_profit, timestamp, executed)
        VALUES
        (gen_random_uuid(), %(token_pair)s, %(exchange_a)s, %(exchange_b)s, %(price_difference)s, %(potential_profit)s, %(timestamp)s, false)
        """
        
        await db_manager.execute_query(query, opportunity)
    
    # Store in ClickHouse
    clickhouse_data = []
    for opportunity in arbitrage_opportunities:
        clickhouse_data.append({
            "token_pair": opportunity.get("token_pair"),
            "exchange_a": opportunity.get("exchange_a"),
            "exchange_b": opportunity.get("exchange_b"),
            "price_difference": opportunity.get("price_difference"),
            "potential_profit": opportunity.get("potential_profit"),
            "executed": 0,
            "execution_time_ms": 0,
            "gas_cost_usd": 0,
            "net_profit": 0,
            "timestamp": datetime.fromisoformat(opportunity.get("timestamp"))
        })
    
    # Insert data into ClickHouse
    query = """
    INSERT INTO arbitrage_analytics
    (token_pair, exchange_a, exchange_b, price_difference, potential_profit, executed, execution_time_ms, gas_cost_usd, net_profit, timestamp)
    VALUES
    """
    
    db_manager.execute_clickhouse_batch(query, clickhouse_data)
    
    # Publish to Kafka
    for opportunity in arbitrage_opportunities:
        # Publish to arbitrage-opportunities topic
        db_manager.publish_message(
            topic="arbitrage-opportunities",
            message=opportunity,
            key=opportunity.get("token_pair")
        )
    
    logger.info(f"Stored {len(arbitrage_opportunities)} arbitrage opportunities")
    
    return len(arbitrage_opportunities)

# Create tasks
extract_task = PythonOperator(
    task_id='extract_market_data',
    python_callable=extract_market_data,
    provide_context=True,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_market_data',
    python_callable=transform_market_data,
    provide_context=True,
    dag=dag,
)

load_clickhouse_task = PythonOperator(
    task_id='load_market_data_to_clickhouse',
    python_callable=load_market_data_to_clickhouse,
    provide_context=True,
    dag=dag,
)

cache_redis_task = PythonOperator(
    task_id='cache_market_data_in_redis',
    python_callable=cache_market_data_in_redis,
    provide_context=True,
    dag=dag,
)

publish_kafka_task = PythonOperator(
    task_id='publish_market_data_to_kafka',
    python_callable=publish_market_data_to_kafka,
    provide_context=True,
    dag=dag,
)

detect_arbitrage_task = PythonOperator(
    task_id='detect_arbitrage_opportunities',
    python_callable=detect_arbitrage_opportunities,
    provide_context=True,
    dag=dag,
)

store_arbitrage_task = PythonOperator(
    task_id='store_arbitrage_opportunities',
    python_callable=store_arbitrage_opportunities,
    provide_context=True,
    dag=dag,
)

# Define task dependencies
extract_task >> transform_task
transform_task >> [load_clickhouse_task, cache_redis_task, publish_kafka_task]
transform_task >> detect_arbitrage_task >> store_arbitrage_task