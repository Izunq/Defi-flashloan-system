"""
Intelligent Message Filtering and Aggregation System

This module implements a sophisticated message filtering and routing system for the swarm
intelligence architecture. It ensures that messages are efficiently routed only to the
agents that need them, reducing communication overhead and preventing information overload.

Key features:
- Hierarchical channel structure
- Message filtering based on content, type, and metadata
- Intelligent message aggregation
- Subscription management
- Rate limiting and throttling
- Priority-based message delivery
"""

import json
import time
import logging
import hashlib
import re
from typing import Dict, List, Set, Callable, Any, Optional, Tuple, Union
from enum import Enum
import redis
from dataclasses import dataclass, field
import threading
from collections import defaultdict, deque
import fnmatch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MessageFilter")

class MessagePriority(Enum):
    """Priority levels for messages"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class ChannelPattern:
    """Represents a channel pattern for subscription matching"""
    pattern: str
    regex: re.Pattern = field(init=False)
    
    def __post_init__(self):
        # Convert glob pattern to regex
        pattern = self.pattern.replace('.', r'\.')
        pattern = pattern.replace('*', r'[^:]*')
        pattern = pattern.replace('#', r'.*')
        self.regex = re.compile(f"^{pattern}$")
    
    def matches(self, channel: str) -> bool:
        """Check if a channel matches this pattern"""
        return bool(self.regex.match(channel))


@dataclass
class Subscription:
    """Represents a subscription to a channel pattern"""
    subscriber_id: str
    channel_pattern: ChannelPattern
    callback: Callable[[Dict[str, Any]], None]
    filters: Dict[str, Any] = field(default_factory=dict)
    last_received: float = field(default_factory=time.time)
    message_count: int = 0


@dataclass
class AggregationRule:
    """Defines how messages should be aggregated"""
    channel_pattern: ChannelPattern
    window_seconds: float
    max_messages: int
    aggregate_fields: List[str]
    aggregate_function: Callable[[List[Dict[str, Any]]], Dict[str, Any]]


class MessageFilter:
    """
    Intelligent message filtering and routing system for the swarm architecture.
    
    This class provides a sophisticated message bus that supports:
    - Hierarchical channel structure (e.g., opportunities:bsc:cake-usdt)
    - Content-based filtering
    - Message aggregation
    - Rate limiting
    - Priority-based delivery
    """
    
    def __init__(self, redis_client: redis.Redis, config: Dict[str, Any] = None):
        """
        Initialize the message filter.
        
        Args:
            redis_client: Redis client for pub/sub communication
            config: Configuration dictionary
        """
        self.redis = redis_client
        self.config = config or {}
        
        # Subscriptions: channel_pattern -> list of Subscription objects
        self.subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
        
        # Message aggregation rules
        self.aggregation_rules: List[AggregationRule] = []
        
        # Aggregation buffers: rule -> list of messages
        self.aggregation_buffers: Dict[AggregationRule, List[Dict[str, Any]]] = defaultdict(list)
        self.aggregation_timers: Dict[AggregationRule, threading.Timer] = {}
        
        # Rate limiting: subscriber_id -> channel -> last message time
        self.rate_limits: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Message history for deduplication
        self.message_history: deque = deque(maxlen=1000)
        
        # Redis pubsub
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub_thread = None
        
        # Load configuration
        self._load_config()
        
        # Start background threads
        self._start_background_threads()
    
    def _load_config(self):
        """Load configuration settings"""
        # Load rate limiting configuration
        self.rate_limit_config = self.config.get('rate_limits', {})
        
        # Load aggregation rules
        for rule_config in self.config.get('aggregation_rules', []):
            pattern = rule_config['channel_pattern']
            window = rule_config['window_seconds']
            max_msgs = rule_config['max_messages']
            fields = rule_config['aggregate_fields']
            
            # Get the aggregation function
            func_name = rule_config.get('aggregate_function', 'default')
            if func_name == 'sum':
                func = self._aggregate_sum
            elif func_name == 'avg':
                func = self._aggregate_avg
            elif func_name == 'max':
                func = self._aggregate_max
            elif func_name == 'min':
                func = self._aggregate_min
            elif func_name == 'count':
                func = self._aggregate_count
            else:
                func = self._aggregate_default
            
            rule = AggregationRule(
                channel_pattern=ChannelPattern(pattern),
                window_seconds=window,
                max_messages=max_msgs,
                aggregate_fields=fields,
                aggregate_function=func
            )
            self.aggregation_rules.append(rule)
    
    def _start_background_threads(self):
        """Start background processing threads"""
        # Start Redis pubsub thread
        self.pubsub_thread = threading.Thread(
            target=self._pubsub_listener,
            daemon=True
        )
        self.pubsub_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self.cleanup_thread.start()
    
    def _pubsub_listener(self):
        """Background thread for Redis pubsub listening"""
        while True:
            try:
                message = self.pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    channel = message['channel'].decode('utf-8')
                    data = json.loads(message['data'].decode('utf-8'))
                    self._process_message(channel, data)
            except Exception as e:
                logger.error(f"Error in pubsub listener: {e}")
                time.sleep(1)
    
    def _cleanup_loop(self):
        """Background thread for cleanup tasks"""
        while True:
            try:
                # Clean up message history
                now = time.time()
                while self.message_history and now - self.message_history[0][0] > 3600:
                    self.message_history.popleft()
                
                # Check for expired aggregation buffers
                for rule, buffer in list(self.aggregation_buffers.items()):
                    if buffer and time.time() - buffer[0].get('_timestamp', 0) > rule.window_seconds:
                        self._flush_aggregation_buffer(rule)
                
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                time.sleep(1)
    
    def subscribe(self, subscriber_id: str, channel_pattern: str, 
                  callback: Callable[[Dict[str, Any]], None], 
                  filters: Dict[str, Any] = None) -> bool:
        """
        Subscribe to a channel pattern.
        
        Args:
            subscriber_id: Unique identifier for the subscriber
            channel_pattern: Channel pattern to subscribe to (supports wildcards)
            callback: Function to call when a message is received
            filters: Optional filters to apply to messages
            
        Returns:
            True if subscription was successful
        """
        pattern_obj = ChannelPattern(channel_pattern)
        subscription = Subscription(
            subscriber_id=subscriber_id,
            channel_pattern=pattern_obj,
            callback=callback,
            filters=filters or {}
        )
        
        self.subscriptions[channel_pattern].append(subscription)
        
        # Subscribe to Redis channel if it's a concrete channel (no wildcards)
        if '*' not in channel_pattern and '#' not in channel_pattern:
            self.pubsub.subscribe(channel_pattern)
            
        # For patterns, we need to subscribe to the parent channel
        else:
            # Extract the root channel (before the first wildcard)
            root_parts = []
            for part in channel_pattern.split(':'):
                if '*' in part or '#' in part:
                    break
                root_parts.append(part)
            
            if root_parts:
                root_channel = ':'.join(root_parts)
                self.pubsub.subscribe(root_channel)
        
        logger.info(f"Subscribed {subscriber_id} to {channel_pattern}")
        return True
    
    def unsubscribe(self, subscriber_id: str, channel_pattern: str = None) -> bool:
        """
        Unsubscribe from a channel pattern.
        
        Args:
            subscriber_id: Unique identifier for the subscriber
            channel_pattern: Channel pattern to unsubscribe from (or None for all)
            
        Returns:
            True if unsubscription was successful
        """
        if channel_pattern:
            if channel_pattern in self.subscriptions:
                self.subscriptions[channel_pattern] = [
                    sub for sub in self.subscriptions[channel_pattern]
                    if sub.subscriber_id != subscriber_id
                ]
                
                # If no more subscriptions for this pattern, unsubscribe from Redis
                if not self.subscriptions[channel_pattern]:
                    if '*' not in channel_pattern and '#' not in channel_pattern:
                        self.pubsub.unsubscribe(channel_pattern)
                    del self.subscriptions[channel_pattern]
                
                logger.info(f"Unsubscribed {subscriber_id} from {channel_pattern}")
                return True
            return False
        else:
            # Unsubscribe from all channels
            for pattern in list(self.subscriptions.keys()):
                self.unsubscribe(subscriber_id, pattern)
            return True
    
    def publish(self, channel: str, message: Dict[str, Any], 
                priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel to publish to
            message: Message to publish
            priority: Message priority
            
        Returns:
            True if message was published
        """
        # Add metadata
        message['_timestamp'] = time.time()
        message['_channel'] = channel
        message['_priority'] = priority.value
        
        # Check for duplicates
        message_hash = self._hash_message(message)
        if self._is_duplicate(message_hash):
            logger.debug(f"Dropping duplicate message on {channel}")
            return False
        
        # Store in history for deduplication
        self.message_history.append((time.time(), message_hash))
        
        # Check if this message should be aggregated
        for rule in self.aggregation_rules:
            if rule.channel_pattern.matches(channel):
                self._add_to_aggregation_buffer(rule, message)
                return True
        
        # If not aggregated, publish directly
        try:
            self.redis.publish(channel, json.dumps(message))
            logger.debug(f"Published message to {channel}")
            return True
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")
            return False
    
    def _process_message(self, channel: str, message: Dict[str, Any]):
        """Process a received message and route to subscribers"""
        # Find matching subscriptions
        matching_subs = []
        for pattern, subs in self.subscriptions.items():
            pattern_obj = ChannelPattern(pattern)
            if pattern_obj.matches(channel):
                matching_subs.extend(subs)
        
        # Route message to each matching subscriber
        for sub in matching_subs:
            # Apply filters
            if not self._passes_filters(message, sub.filters):
                continue
            
            # Apply rate limiting
            if not self._check_rate_limit(sub.subscriber_id, channel):
                continue
            
            # Update subscription stats
            sub.last_received = time.time()
            sub.message_count += 1
            
            # Deliver message
            try:
                sub.callback(message)
            except Exception as e:
                logger.error(f"Error in subscriber callback: {e}")
    
    def _passes_filters(self, message: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if a message passes the subscription filters"""
        if not filters:
            return True
        
        for key, filter_value in filters.items():
            # Handle nested keys with dot notation
            if '.' in key:
                parts = key.split('.')
                msg_value = message
                for part in parts:
                    if isinstance(msg_value, dict) and part in msg_value:
                        msg_value = msg_value[part]
                    else:
                        return False
            else:
                if key not in message:
                    return False
                msg_value = message[key]
            
            # Handle different filter types
            if isinstance(filter_value, list):
                # List of allowed values
                if msg_value not in filter_value:
                    return False
            elif isinstance(filter_value, dict):
                # Complex filter with operators
                for op, op_value in filter_value.items():
                    if op == '$gt' and not (msg_value > op_value):
                        return False
                    elif op == '$gte' and not (msg_value >= op_value):
                        return False
                    elif op == '$lt' and not (msg_value < op_value):
                        return False
                    elif op == '$lte' and not (msg_value <= op_value):
                        return False
                    elif op == '$ne' and msg_value == op_value:
                        return False
                    elif op == '$in' and msg_value not in op_value:
                        return False
                    elif op == '$nin' and msg_value in op_value:
                        return False
                    elif op == '$contains' and op_value not in msg_value:
                        return False
                    elif op == '$regex' and not re.search(op_value, str(msg_value)):
                        return False
            else:
                # Simple equality
                if msg_value != filter_value:
                    return False
        
        return True
    
    def _check_rate_limit(self, subscriber_id: str, channel: str) -> bool:
        """Check if a message should be rate-limited"""
        # Get rate limit configuration for this channel
        rate_limit = None
        for pattern, limit in self.rate_limit_config.items():
            if fnmatch.fnmatch(channel, pattern):
                rate_limit = limit
                break
        
        if not rate_limit:
            return True
        
        # Check if we've exceeded the rate limit
        now = time.time()
        last_time = self.rate_limits.get(subscriber_id, {}).get(channel, 0)
        min_interval = 1.0 / rate_limit
        
        if now - last_time < min_interval:
            return False
        
        # Update last message time
        if subscriber_id not in self.rate_limits:
            self.rate_limits[subscriber_id] = {}
        self.rate_limits[subscriber_id][channel] = now
        
        return True
    
    def _hash_message(self, message: Dict[str, Any]) -> str:
        """Create a hash of a message for deduplication"""
        # Create a copy without metadata fields
        msg_copy = {k: v for k, v in message.items() if not k.startswith('_')}
        msg_str = json.dumps(msg_copy, sort_keys=True)
        return hashlib.md5(msg_str.encode('utf-8')).hexdigest()
    
    def _is_duplicate(self, message_hash: str) -> bool:
        """Check if a message is a duplicate"""
        for _, hash_value in self.message_history:
            if hash_value == message_hash:
                return True
        return False
    
    def _add_to_aggregation_buffer(self, rule: AggregationRule, message: Dict[str, Any]):
        """Add a message to an aggregation buffer"""
        self.aggregation_buffers[rule].append(message)
        
        # If we've reached the max messages, flush the buffer
        if len(self.aggregation_buffers[rule]) >= rule.max_messages:
            self._flush_aggregation_buffer(rule)
            return
        
        # If this is the first message, start a timer
        if len(self.aggregation_buffers[rule]) == 1:
            if rule in self.aggregation_timers and self.aggregation_timers[rule].is_alive():
                self.aggregation_timers[rule].cancel()
            
            timer = threading.Timer(
                rule.window_seconds,
                self._flush_aggregation_buffer,
                args=[rule]
            )
            timer.daemon = True
            timer.start()
            self.aggregation_timers[rule] = timer
    
    def _flush_aggregation_buffer(self, rule: AggregationRule):
        """Flush an aggregation buffer, publishing the aggregated message"""
        buffer = self.aggregation_buffers.get(rule, [])
        if not buffer:
            return
        
        # Cancel any pending timer
        if rule in self.aggregation_timers and self.aggregation_timers[rule].is_alive():
            self.aggregation_timers[rule].cancel()
        
        # Aggregate the messages
        aggregated = rule.aggregate_function(buffer)
        
        # Add metadata
        channel = buffer[0]['_channel']
        aggregated['_aggregated'] = True
        aggregated['_count'] = len(buffer)
        aggregated['_timestamp'] = time.time()
        aggregated['_channel'] = channel
        
        # Publish the aggregated message
        try:
            self.redis.publish(channel, json.dumps(aggregated))
            logger.debug(f"Published aggregated message to {channel} (from {len(buffer)} messages)")
        except Exception as e:
            logger.error(f"Error publishing aggregated message to {channel}: {e}")
        
        # Clear the buffer
        self.aggregation_buffers[rule] = []
    
    # Aggregation functions
    def _aggregate_default(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Default aggregation function - just take the latest message"""
        if not messages:
            return {}
        return {k: v for k, v in messages[-1].items() if not k.startswith('_')}
    
    def _aggregate_sum(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sum aggregation function"""
        if not messages:
            return {}
        
        result = {k: v for k, v in messages[0].items() if not k.startswith('_')}
        
        for field in messages[0].get('_aggregate_fields', []):
            result[field] = 0
            for msg in messages:
                if field in msg and isinstance(msg[field], (int, float)):
                    result[field] += msg[field]
        
        return result
    
    def _aggregate_avg(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Average aggregation function"""
        if not messages:
            return {}
        
        result = {k: v for k, v in messages[0].items() if not k.startswith('_')}
        
        for field in messages[0].get('_aggregate_fields', []):
            values = []
            for msg in messages:
                if field in msg and isinstance(msg[field], (int, float)):
                    values.append(msg[field])
            
            if values:
                result[field] = sum(values) / len(values)
            else:
                result[field] = 0
        
        return result
    
    def _aggregate_max(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Max aggregation function"""
        if not messages:
            return {}
        
        result = {k: v for k, v in messages[0].items() if not k.startswith('_')}
        
        for field in messages[0].get('_aggregate_fields', []):
            values = []
            for msg in messages:
                if field in msg and isinstance(msg[field], (int, float)):
                    values.append(msg[field])
            
            if values:
                result[field] = max(values)
        
        return result
    
    def _aggregate_min(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Min aggregation function"""
        if not messages:
            return {}
        
        result = {k: v for k, v in messages[0].items() if not k.startswith('_')}
        
        for field in messages[0].get('_aggregate_fields', []):
            values = []
            for msg in messages:
                if field in msg and isinstance(msg[field], (int, float)):
                    values.append(msg[field])
            
            if values:
                result[field] = min(values)
        
        return result
    
    def _aggregate_count(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Count aggregation function"""
        if not messages:
            return {}
        
        result = {k: v for k, v in messages[0].items() if not k.startswith('_')}
        result['count'] = len(messages)
        
        return result
    
    def shutdown(self):
        """Shutdown the message filter"""
        # Cancel all timers
        for timer in self.aggregation_timers.values():
            if timer.is_alive():
                timer.cancel()
        
        # Close Redis pubsub
        if self.pubsub:
            self.pubsub.close()


class MessageBus:
    """
    High-level message bus interface that uses the MessageFilter for intelligent
    message routing and filtering.
    """
    
    def __init__(self, redis_client: redis.Redis, config_path: str = None):
        """
        Initialize the message bus.
        
        Args:
            redis_client: Redis client for pub/sub communication
            config_path: Path to configuration file
        """
        self.redis = redis_client
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize message filter
        self.message_filter = MessageFilter(redis_client, self.config)
        
        # Subscriber ID counter
        self._subscriber_counter = 0
        
        # Active subscribers
        self.subscribers: Dict[str, Dict[str, Any]] = {}
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file"""
        config = {
            # Default configuration
            'rate_limits': {
                'system:alerts:*': 10,  # 10 messages per second
                'opportunities:*': 100,  # 100 messages per second
                '*': 1000  # 1000 messages per second for all other channels
            },
            'aggregation_rules': [
                {
                    'channel_pattern': 'metrics:*',
                    'window_seconds': 5.0,
                    'max_messages': 100,
                    'aggregate_fields': ['value'],
                    'aggregate_function': 'avg'
                },
                {
                    'channel_pattern': 'opportunities:*:discovery',
                    'window_seconds': 1.0,
                    'max_messages': 50,
                    'aggregate_fields': ['count'],
                    'aggregate_function': 'count'
                }
            ]
        }
        
        # Load from file if provided
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
        
        return config
    
    def subscribe(self, channel_pattern: str, callback: Callable[[Dict[str, Any]], None], 
                  filters: Dict[str, Any] = None) -> str:
        """
        Subscribe to a channel pattern.
        
        Args:
            channel_pattern: Channel pattern to subscribe to (supports wildcards)
            callback: Function to call when a message is received
            filters: Optional filters to apply to messages
            
        Returns:
            Subscriber ID
        """
        self._subscriber_counter += 1
        subscriber_id = f"sub-{self._subscriber_counter}"
        
        success = self.message_filter.subscribe(
            subscriber_id=subscriber_id,
            channel_pattern=channel_pattern,
            callback=callback,
            filters=filters
        )
        
        if success:
            self.subscribers[subscriber_id] = {
                'channel_pattern': channel_pattern,
                'filters': filters,
                'created_at': time.time()
            }
            return subscriber_id
        
        return None
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """
        Unsubscribe from all channels.
        
        Args:
            subscriber_id: Subscriber ID returned from subscribe()
            
        Returns:
            True if unsubscription was successful
        """
        if subscriber_id not in self.subscribers:
            return False
        
        success = self.message_filter.unsubscribe(subscriber_id)
        
        if success:
            del self.subscribers[subscriber_id]
            return True
        
        return False
    
    def publish(self, channel: str, message: Dict[str, Any], 
                priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel to publish to
            message: Message to publish
            priority: Message priority
            
        Returns:
            True if message was published
        """
        return self.message_filter.publish(channel, message, priority)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the message bus"""
        stats = {
            'subscribers': len(self.subscribers),
            'channels': len(self.message_filter.subscriptions),
            'message_history_size': len(self.message_filter.message_history),
            'aggregation_buffers': {
                str(rule.channel_pattern.pattern): len(buffer)
                for rule, buffer in self.message_filter.aggregation_buffers.items()
            }
        }
        return stats
    
    def shutdown(self):
        """Shutdown the message bus"""
        self.message_filter.shutdown()


# Example usage
if __name__ == "__main__":
    import redis
    
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    
    # Create message bus
    bus = MessageBus(r)
    
    # Example callback
    def on_message(message):
        print(f"Received message: {message}")
    
    # Subscribe to channels
    sub_id1 = bus.subscribe("opportunities:ethereum:*", on_message)
    sub_id2 = bus.subscribe("system:alerts:high-risk", on_message)
    
    # Publish messages
    bus.publish("opportunities:ethereum:uniswap", {
        "type": "price_change",
        "pair": "ETH-USDC",
        "price": 1850.25,
        "change": 0.5
    })
    
    bus.publish("system:alerts:high-risk", {
        "type": "security_alert",
        "severity": "high",
        "message": "Unusual transaction pattern detected"
    })
    
    # Keep the program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bus.shutdown()