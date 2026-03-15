"""
Event Bus Module
---------------
This module provides a centralized event bus for communication between different
components of the system using Redis pub/sub.
"""

import json
import redis
import threading
from typing import Callable

# Assuming you have a central Redis connection setup
try:
    from redis_setup import get_redis_connection
except ImportError:
    def get_redis_connection():
        return redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class EventBus:
    def __init__(self):
        self.redis_client = get_redis_connection()
        self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)

    def publish(self, channel: str, data: dict):
        """
        Publish a message to a specific channel.
        
        Args:
            channel: The channel to publish to
            data: Dictionary containing the message data
        """
        message = json.dumps(data)
        self.redis_client.publish(channel, message)

    def subscribe(self, channel: str, callback: Callable[[dict], None]):
        """
        Subscribe to a channel and register a callback function.
        
        Args:
            channel: The channel to subscribe to
            callback: Function to call when a message is received
        """
        self.pubsub.subscribe(**{channel: lambda msg: callback(json.loads(msg['data']))})
        thread = threading.Thread(target=self.pubsub.run, daemon=True)
        thread.start()
        print(f"Subscribed to channel: {channel}")

# Create a singleton instance
event_bus = EventBus()