import redis
import json
import sys

try:
    # Load configuration
    with open('redis_config.json', 'r') as f:
        config = json.load(f)
    
    # Connect to Redis
    r = redis.Redis(**config['redis'])
    
    # Test connection
    r.ping()
    print("✅ Redis connection successful!")
    
    # Test basic operations
    r.set('test_key', 'test_value')
    value = r.get('test_key')
    print(f"✅ Redis operations successful! Retrieved: {value.decode() if value else None}")
    
    # Clean up
    r.delete('test_key')
    
except redis.ConnectionError:
    print("❌ Redis connection failed. Make sure Redis is running.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Redis test failed: {e}")
    sys.exit(1)
