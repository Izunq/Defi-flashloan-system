"""
Redis Setup Module
----------------
This module provides a centralized Redis connection for the entire system.
"""

import redis
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Redis connection parameters
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Redis connection pool
_redis_pool = None

def get_redis_connection():
    """
    Get a Redis connection from the connection pool.
    
    Returns:
        Redis client instance
    """
    global _redis_pool
    
    if _redis_pool is None:
        # Create a connection pool
        _redis_pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
    
    return redis.Redis(connection_pool=_redis_pool)

# Test the connection
if __name__ == "__main__":
    try:
        redis_client = get_redis_connection()
        redis_client.ping()
        print("✅ Redis connection successful!")
    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        print("Make sure Redis server is running.")