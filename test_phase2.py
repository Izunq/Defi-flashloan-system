"""
Phase 2 Test Script
-----------------
This script tests the Phase 2 integration framework components.
"""

import time
import json
from core.event_bus import event_bus
from core.redis_setup import get_redis_connection

def test_event_bus():
    """Test the event bus by publishing and subscribing to a test channel."""
    print("\n=== Testing Event Bus ===")
    
    # Create a test message
    test_message = {
        "test_id": "event_bus_test",
        "timestamp": time.time(),
        "data": "Hello, Event Bus!"
    }
    
    # Create a flag to track message receipt
    message_received = False
    
    # Define a callback function
    def test_callback(data):
        nonlocal message_received
        print(f"✅ Received test message: {data}")
        message_received = True
    
    # Subscribe to the test channel
    event_bus.subscribe('test-channel', test_callback)
    print("Subscribed to 'test-channel'")
    
    # Wait a moment for the subscription to be established
    time.sleep(1)
    
    # Publish a message
    print("Publishing test message...")
    event_bus.publish('test-channel', test_message)
    
    # Wait for the message to be received
    timeout = 5
    start_time = time.time()
    while not message_received and time.time() - start_time < timeout:
        time.sleep(0.1)
    
    if message_received:
        print("✅ Event Bus test passed!")
    else:
        print("❌ Event Bus test failed: Message not received within timeout")

def test_redis_connection():
    """Test the Redis connection."""
    print("\n=== Testing Redis Connection ===")
    
    try:
        redis_client = get_redis_connection()
        redis_client.ping()
        print("✅ Redis connection successful!")
        
        # Test setting and getting a value
        test_key = "test:phase2:key"
        test_value = json.dumps({"test": "value", "timestamp": time.time()})
        
        redis_client.set(test_key, test_value)
        retrieved_value = redis_client.get(test_key)
        
        if retrieved_value == test_value:
            print("✅ Redis set/get test passed!")
        else:
            print("❌ Redis set/get test failed: Values don't match")
            
        # Clean up
        redis_client.delete(test_key)
        
    except Exception as e:
        print(f"❌ Redis test failed: {e}")

def simulate_market_data():
    """Simulate publishing market data."""
    print("\n=== Simulating Market Data ===")
    
    # Create a sample market data event
    market_data = {
        "pair": "WETH/USDC",
        "timestamp": time.time(),
        "dex_a": "Uniswap",
        "dex_b": "SushiSwap",
        "dex_a_price": 2000.0,
        "dex_b_price": 2010.0,
        "asset_address": "${CONTRACT_ADDRESS}",
        "quote_address": "${CONTRACT_ADDRESS}"
    }
    
    # Publish to the market data channel
    print(f"Publishing market data for {market_data['pair']}...")
    event_bus.publish('market-data-events', market_data)
    print("✅ Market data published!")
    
    # Also publish a monitoring event
    monitoring_event = {
        "status": "info",
        "message": f"Test market data published for {market_data['pair']}"
    }
    event_bus.publish('monitoring-events', monitoring_event)
    print("✅ Monitoring event published!")

if __name__ == "__main__":
    print("=== Phase 2 Integration Test ===")
    
    # Run the tests
    test_redis_connection()
    test_event_bus()
    simulate_market_data()
    
    print("\n=== Test Complete ===")
    print("If all tests passed, the Phase 2 integration framework is working correctly.")
    print("You can now run the full system with 'python main.py'")
    
    # Keep the script running for a moment to allow event processing
    time.sleep(5)