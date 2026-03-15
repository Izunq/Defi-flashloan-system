"""
Message queue adapter interface and implementations.
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable

# Import models
from backend.src.models.block_model import Block, Transaction

logger = logging.getLogger(__name__)

class MessageQueueAdapter(ABC):
    """Abstract base class for message queue adapters."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the message queue."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the message queue."""
        pass
    
    @abstractmethod
    def publish_block(self, block: Block) -> bool:
        """Publish a block to the message queue."""
        pass
    
    @abstractmethod
    def publish_transaction(self, transaction: Transaction) -> bool:
        """Publish a transaction to the message queue."""
        pass
    
    @abstractmethod
    def subscribe_to_blocks(self, callback: Callable[[Block], None]) -> bool:
        """Subscribe to block events."""
        pass
    
    @abstractmethod
    def subscribe_to_transactions(self, callback: Callable[[Transaction], None]) -> bool:
        """Subscribe to transaction events."""
        pass


class DummyAdapter(MessageQueueAdapter):
    """Dummy adapter for when message queue is disabled."""
    
    def connect(self) -> bool:
        """Connect to the message queue."""
        logger.info("Message queue is disabled, using dummy adapter")
        return True
    
    def disconnect(self) -> bool:
        """Disconnect from the message queue."""
        return True
    
    def publish_block(self, block: Block) -> bool:
        """Publish a block to the message queue."""
        logger.debug(f"Would publish block {block.number} to message queue")
        return True
    
    def publish_transaction(self, transaction: Transaction) -> bool:
        """Publish a transaction to the message queue."""
        logger.debug(f"Would publish transaction {transaction.hash} to message queue")
        return True
    
    def subscribe_to_blocks(self, callback: Callable[[Block], None]) -> bool:
        """Subscribe to block events."""
        logger.debug("Would subscribe to block events")
        return True
    
    def subscribe_to_transactions(self, callback: Callable[[Transaction], None]) -> bool:
        """Subscribe to transaction events."""
        logger.debug("Would subscribe to transaction events")
        return True


try:
    import pika
    
    class RabbitMQAdapter(MessageQueueAdapter):
        """RabbitMQ adapter for message queue."""
        
        def __init__(self, config: Dict[str, Any]):
            """Initialize the RabbitMQ adapter."""
            self.config = config
            self.connection = None
            self.channel = None
            self.connected = False
            
            # Get exchange names
            self.exchanges = config.get("exchanges", {})
            self.blocks_exchange = self.exchanges.get("blocks", "blockchain.blocks")
            self.transactions_exchange = self.exchanges.get("transactions", "blockchain.transactions")
        
        def connect(self) -> bool:
            """Connect to RabbitMQ."""
            try:
                # Build connection parameters
                credentials = pika.PlainCredentials(
                    self.config.get("username", "guest"),
                    self.config.get("password", "guest")
                )
                
                parameters = pika.ConnectionParameters(
                    host=self.config.get("host", "localhost"),
                    port=self.config.get("port", 5672),
                    virtual_host=self.config.get("virtual_host", "/"),
                    credentials=credentials
                )
                
                # Connect to RabbitMQ
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Declare exchanges
                self.channel.exchange_declare(
                    exchange=self.blocks_exchange,
                    exchange_type="topic",
                    durable=True
                )
                
                self.channel.exchange_declare(
                    exchange=self.transactions_exchange,
                    exchange_type="topic",
                    durable=True
                )
                
                self.connected = True
                logger.info(f"Connected to RabbitMQ at {self.config.get('host')}:{self.config.get('port')}")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
                return False
        
        def disconnect(self) -> bool:
            """Disconnect from RabbitMQ."""
            if self.connection:
                self.connection.close()
            self.connected = False
            return True
        
        def publish_block(self, block: Block) -> bool:
            """Publish a block to RabbitMQ."""
            if not self.connected:
                logger.error("Not connected to RabbitMQ")
                return False
            
            try:
                # Convert block to JSON
                block_json = json.dumps(block.dict(by_alias=True), default=str)
                
                # Publish block
                self.channel.basic_publish(
                    exchange=self.blocks_exchange,
                    routing_key=f"block.{block.number}",
                    body=block_json,
                    properties=pika.BasicProperties(
                        content_type="application/json",
                        delivery_mode=2  # Persistent
                    )
                )
                
                logger.debug(f"Published block {block.number} to RabbitMQ")
                return True
            except Exception as e:
                logger.error(f"Failed to publish block {block.number}: {str(e)}")
                return False
        
        def publish_transaction(self, transaction: Transaction) -> bool:
            """Publish a transaction to RabbitMQ."""
            if not self.connected:
                logger.error("Not connected to RabbitMQ")
                return False
            
            try:
                # Convert transaction to JSON
                tx_json = json.dumps(transaction.dict(by_alias=True), default=str)
                
                # Publish transaction
                self.channel.basic_publish(
                    exchange=self.transactions_exchange,
                    routing_key=f"transaction.{transaction.block_number}",
                    body=tx_json,
                    properties=pika.BasicProperties(
                        content_type="application/json",
                        delivery_mode=2  # Persistent
                    )
                )
                
                logger.debug(f"Published transaction {transaction.hash} to RabbitMQ")
                return True
            except Exception as e:
                logger.error(f"Failed to publish transaction {transaction.hash}: {str(e)}")
                return False
        
        def subscribe_to_blocks(self, callback: Callable[[Block], None]) -> bool:
            """Subscribe to block events."""
            if not self.connected:
                logger.error("Not connected to RabbitMQ")
                return False
            
            try:
                # Declare queue
                result = self.channel.queue_declare(queue="", exclusive=True)
                queue_name = result.method.queue
                
                # Bind queue to exchange
                self.channel.queue_bind(
                    exchange=self.blocks_exchange,
                    queue=queue_name,
                    routing_key="block.*"
                )
                
                # Define callback
                def on_message(ch, method, properties, body):
                    try:
                        block_dict = json.loads(body)
                        block = Block(**block_dict)
                        callback(block)
                    except Exception as e:
                        logger.error(f"Error processing block message: {str(e)}")
                
                # Start consuming
                self.channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=on_message,
                    auto_ack=True
                )
                
                logger.info(f"Subscribed to block events on {self.blocks_exchange}")
                return True
            except Exception as e:
                logger.error(f"Failed to subscribe to block events: {str(e)}")
                return False
        
        def subscribe_to_transactions(self, callback: Callable[[Transaction], None]) -> bool:
            """Subscribe to transaction events."""
            if not self.connected:
                logger.error("Not connected to RabbitMQ")
                return False
            
            try:
                # Declare queue
                result = self.channel.queue_declare(queue="", exclusive=True)
                queue_name = result.method.queue
                
                # Bind queue to exchange
                self.channel.queue_bind(
                    exchange=self.transactions_exchange,
                    queue=queue_name,
                    routing_key="transaction.*"
                )
                
                # Define callback
                def on_message(ch, method, properties, body):
                    try:
                        tx_dict = json.loads(body)
                        transaction = Transaction(**tx_dict)
                        callback(transaction)
                    except Exception as e:
                        logger.error(f"Error processing transaction message: {str(e)}")
                
                # Start consuming
                self.channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=on_message,
                    auto_ack=True
                )
                
                logger.info(f"Subscribed to transaction events on {self.transactions_exchange}")
                return True
            except Exception as e:
                logger.error(f"Failed to subscribe to transaction events: {str(e)}")
                return False
except ImportError:
    logger.warning("pika not installed, RabbitMQ adapter not available")


try:
    from kafka import KafkaProducer, KafkaConsumer
    import json
    
    class KafkaAdapter(MessageQueueAdapter):
        """Kafka adapter for message queue."""
        
        def __init__(self, config: Dict[str, Any]):
            """Initialize the Kafka adapter."""
            self.config = config
            self.producer = None
            self.consumers = []
            self.connected = False
            
            # Get topic names
            self.topics = config.get("topics", {})
            self.blocks_topic = self.topics.get("blocks", "blockchain.blocks")
            self.transactions_topic = self.topics.get("transactions", "blockchain.transactions")
        
        def connect(self) -> bool:
            """Connect to Kafka."""
            try:
                # Build bootstrap servers string
                bootstrap_servers = f"{self.config.get('host', 'localhost')}:{self.config.get('port', 9092)}"
                
                # Connect to Kafka
                self.producer = KafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
                )
                
                self.connected = True
                logger.info(f"Connected to Kafka at {bootstrap_servers}")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to Kafka: {str(e)}")
                return False
        
        def disconnect(self) -> bool:
            """Disconnect from Kafka."""
            if self.producer:
                self.producer.close()
            
            for consumer in self.consumers:
                consumer.close()
            
            self.connected = False
            return True
        
        def publish_block(self, block: Block) -> bool:
            """Publish a block to Kafka."""
            if not self.connected:
                logger.error("Not connected to Kafka")
                return False
            
            try:
                # Convert block to dictionary
                block_dict = block.dict(by_alias=True)
                
                # Publish block
                self.producer.send(
                    self.blocks_topic,
                    key=str(block.number).encode('utf-8'),
                    value=block_dict
                )
                
                logger.debug(f"Published block {block.number} to Kafka")
                return True
            except Exception as e:
                logger.error(f"Failed to publish block {block.number}: {str(e)}")
                return False
        
        def publish_transaction(self, transaction: Transaction) -> bool:
            """Publish a transaction to Kafka."""
            if not self.connected:
                logger.error("Not connected to Kafka")
                return False
            
            try:
                # Convert transaction to dictionary
                tx_dict = transaction.dict(by_alias=True)
                
                # Publish transaction
                self.producer.send(
                    self.transactions_topic,
                    key=transaction.hash.encode('utf-8'),
                    value=tx_dict
                )
                
                logger.debug(f"Published transaction {transaction.hash} to Kafka")
                return True
            except Exception as e:
                logger.error(f"Failed to publish transaction {transaction.hash}: {str(e)}")
                return False
        
        def subscribe_to_blocks(self, callback: Callable[[Block], None]) -> bool:
            """Subscribe to block events."""
            if not self.connected:
                logger.error("Not connected to Kafka")
                return False
            
            try:
                # Build bootstrap servers string
                bootstrap_servers = f"{self.config.get('host', 'localhost')}:{self.config.get('port', 9092)}"
                
                # Create consumer
                consumer = KafkaConsumer(
                    self.blocks_topic,
                    bootstrap_servers=bootstrap_servers,
                    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                    group_id=f"blockchain-data-{self.blocks_topic}",
                    auto_offset_reset="latest"
                )
                
                # Start consuming in a separate thread
                import threading
                
                def consume():
                    for message in consumer:
                        try:
                            block_dict = message.value
                            block = Block(**block_dict)
                            callback(block)
                        except Exception as e:
                            logger.error(f"Error processing block message: {str(e)}")
                
                thread = threading.Thread(target=consume, daemon=True)
                thread.start()
                
                # Add consumer to list
                self.consumers.append(consumer)
                
                logger.info(f"Subscribed to block events on {self.blocks_topic}")
                return True
            except Exception as e:
                logger.error(f"Failed to subscribe to block events: {str(e)}")
                return False
        
        def subscribe_to_transactions(self, callback: Callable[[Transaction], None]) -> bool:
            """Subscribe to transaction events."""
            if not self.connected:
                logger.error("Not connected to Kafka")
                return False
            
            try:
                # Build bootstrap servers string
                bootstrap_servers = f"{self.config.get('host', 'localhost')}:{self.config.get('port', 9092)}"
                
                # Create consumer
                consumer = KafkaConsumer(
                    self.transactions_topic,
                    bootstrap_servers=bootstrap_servers,
                    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                    group_id=f"blockchain-data-{self.transactions_topic}",
                    auto_offset_reset="latest"
                )
                
                # Start consuming in a separate thread
                import threading
                
                def consume():
                    for message in consumer:
                        try:
                            tx_dict = message.value
                            transaction = Transaction(**tx_dict)
                            callback(transaction)
                        except Exception as e:
                            logger.error(f"Error processing transaction message: {str(e)}")
                
                thread = threading.Thread(target=consume, daemon=True)
                thread.start()
                
                # Add consumer to list
                self.consumers.append(consumer)
                
                logger.info(f"Subscribed to transaction events on {self.transactions_topic}")
                return True
            except Exception as e:
                logger.error(f"Failed to subscribe to transaction events: {str(e)}")
                return False
except ImportError:
    logger.warning("kafka-python not installed, Kafka adapter not available")


def get_message_queue_adapter(config: Dict[str, Any]) -> MessageQueueAdapter:
    """Get a message queue adapter based on the configuration."""
    if not config.get("enabled", False):
        return DummyAdapter()
    
    mq_type = config.get("type", "").lower()
    
    if mq_type == "rabbitmq":
        try:
            return RabbitMQAdapter(config.get("connection", {}))
        except NameError:
            logger.warning("RabbitMQ adapter not available, using dummy adapter")
            return DummyAdapter()
    elif mq_type == "kafka":
        try:
            return KafkaAdapter(config.get("connection", {}))
        except NameError:
            logger.warning("Kafka adapter not available, using dummy adapter")
            return DummyAdapter()
    else:
        logger.warning(f"Unknown message queue type: {mq_type}, using dummy adapter")
        return DummyAdapter()