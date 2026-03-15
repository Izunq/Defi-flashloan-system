#!/usr/bin/env python3
# =================================================================================================
# DATABASE MANAGER MODULE
# =================================================================================================

import os
import yaml
import json
import logging
import asyncio
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Database drivers
import psycopg
import clickhouse_driver
import redis
from redis.cluster import RedisCluster
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic

# Data validation
import great_expectations as ge
from great_expectations.core import ExpectationSuite, ExpectationConfiguration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("database_manager.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("database_manager")

@dataclass
class ConnectionConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    user: str
    password: str
    ssl: bool = True
    ssl_mode: str = "verify-full"
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_root_cert: Optional[str] = None


@dataclass
class PoolConfig:
    """Connection pool configuration"""
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: int = 30
    idle_timeout: int = 300
    max_lifetime: int = 3600


class DatabaseManager:
    """
    Unified database manager for multi-database architecture
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize database manager
        
        Args:
            config_path: Path to database configuration file
        """
        # Load environment variables
        load_dotenv()
        
        self.config_path = config_path or os.getenv("DB_CONFIG_PATH", "database_config.yaml")
        self.config = self._load_config()
        
        # Initialize connections
        self.pg_pool = None
        self.clickhouse_client = None
        self.redis_cluster = None
        self.kafka_producer = None
        self.kafka_consumer = None
        
        # Initialize connections
        self._init_connections()
        
        logger.info("Database Manager initialized")
    
    def _load_config(self) -> Dict:
        """
        Load configuration from YAML file
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Replace environment variables in config
            config_str = json.dumps(config)
            for key, value in os.environ.items():
                placeholder = f"${{{key}}}"
                config_str = config_str.replace(placeholder, value)
            
            config = json.loads(config_str)
            
            logger.info(f"Loaded database configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load database configuration: {e}")
            raise
    
    def _init_connections(self):
        """Initialize all database connections"""
        try:
            # Initialize PostgreSQL connection pool
            self._init_postgres()
            
            # Initialize ClickHouse connection
            self._init_clickhouse()
            
            # Initialize Redis Cluster connection
            self._init_redis()
            
            # Initialize Kafka producer and consumer
            self._init_kafka()
            
            logger.info("All database connections initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        try:
            pg_config = self.config.get("primary_db", {}).get("connection", {})
            pool_config = self.config.get("primary_db", {}).get("pool", {})
            
            # Create connection pool
            self.pg_pool = psycopg.AsyncConnectionPool(
                conninfo=f"host={pg_config.get('host')} "
                        f"port={pg_config.get('port')} "
                        f"dbname={pg_config.get('database')} "
                        f"user={pg_config.get('user')} "
                        f"password={pg_config.get('password')} "
                        f"sslmode={pg_config.get('ssl_mode')} "
                        f"sslcert={pg_config.get('ssl_cert')} "
                        f"sslkey={pg_config.get('ssl_key')} "
                        f"sslrootcert={pg_config.get('ssl_root_cert')}",
                min_size=pool_config.get("min_connections", 5),
                max_size=pool_config.get("max_connections", 20),
                max_idle=pool_config.get("idle_timeout", 300),
                max_lifetime=pool_config.get("max_lifetime", 3600),
                timeout=pool_config.get("connection_timeout", 30)
            )
            
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
            raise
    
    def _init_clickhouse(self):
        """Initialize ClickHouse connection"""
        try:
            ch_config = self.config.get("analytics_db", {}).get("connection", {})
            
            # Create ClickHouse client
            self.clickhouse_client = clickhouse_driver.Client(
                host=ch_config.get("host"),
                port=ch_config.get("port"),
                database=ch_config.get("database"),
                user=ch_config.get("user"),
                password=ch_config.get("password"),
                secure=ch_config.get("secure", True),
                verify=ch_config.get("verify", True),
                ca_certs=ch_config.get("ca_cert"),
                compression=True
            )
            
            logger.info("ClickHouse connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ClickHouse connection: {e}")
            raise
    
    def _init_redis(self):
        """Initialize Redis Cluster connection"""
        try:
            redis_config = self.config.get("cache_layer", {}).get("connection", {})
            
            # Create Redis Cluster client
            startup_nodes = [
                {"host": node.get("host"), "port": node.get("port")}
                for node in redis_config.get("hosts", [])
            ]
            
            self.redis_cluster = RedisCluster(
                startup_nodes=startup_nodes,
                password=redis_config.get("password"),
                ssl=redis_config.get("ssl", True),
                ssl_cert_reqs="required",
                ssl_certfile=redis_config.get("ssl_cert"),
                ssl_keyfile=redis_config.get("ssl_key"),
                ssl_ca_certs=redis_config.get("ssl_ca_cert"),
                decode_responses=True,
                skip_full_coverage_check=True
            )
            
            logger.info("Redis Cluster connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis Cluster connection: {e}")
            raise
    
    def _init_kafka(self):
        """Initialize Kafka producer and consumer"""
        try:
            kafka_config = self.config.get("kafka", {})
            bootstrap_servers = kafka_config.get("bootstrap_servers", [])
            security_config = kafka_config.get("security", {})
            
            # Create Kafka producer
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                security_protocol=security_config.get("security_protocol"),
                sasl_mechanism=security_config.get("sasl_mechanism"),
                sasl_plain_username=security_config.get("sasl_username"),
                sasl_plain_password=security_config.get("sasl_password"),
                ssl_cafile=security_config.get("ssl_cafile"),
                ssl_certfile=security_config.get("ssl_certfile"),
                ssl_keyfile=security_config.get("ssl_keyfile"),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks="all",
                retries=5,
                retry_backoff_ms=100,
                max_in_flight_requests_per_connection=1,
                enable_idempotence=True
            )
            
            # Create Kafka consumer
            self.kafka_consumer = KafkaConsumer(
                bootstrap_servers=bootstrap_servers,
                security_protocol=security_config.get("security_protocol"),
                sasl_mechanism=security_config.get("sasl_mechanism"),
                sasl_plain_username=security_config.get("sasl_username"),
                sasl_plain_password=security_config.get("sasl_password"),
                ssl_cafile=security_config.get("ssl_cafile"),
                ssl_certfile=security_config.get("ssl_certfile"),
                ssl_keyfile=security_config.get("ssl_keyfile"),
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                group_id="flashloan-consumer-group"
            )
            
            logger.info("Kafka producer and consumer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer and consumer: {e}")
            raise
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a query on the primary PostgreSQL database
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query results as a list of dictionaries
        """
        async with self.pg_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params or {})
                
                # Check if query returns results
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    results = await cur.fetchall()
                    
                    # Convert results to list of dictionaries
                    return [dict(zip(columns, row)) for row in results]
                
                return []
    
    async def execute_batch(self, query: str, params_list: List[Dict]) -> None:
        """
        Execute a batch query on the primary PostgreSQL database
        
        Args:
            query: SQL query to execute
            params_list: List of query parameters
        """
        async with self.pg_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(query, params_list)
                await conn.commit()
    
    def execute_clickhouse_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a query on the ClickHouse analytics database
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query results as a list of dictionaries
        """
        # Execute query
        result = self.clickhouse_client.execute(query, params or {}, with_column_types=True)
        
        # Extract data and column names
        data, columns = result
        column_names = [col[0] for col in columns]
        
        # Convert results to list of dictionaries
        return [dict(zip(column_names, row)) for row in data]
    
    def execute_clickhouse_batch(self, query: str, params_list: List[Dict]) -> None:
        """
        Execute a batch query on the ClickHouse analytics database
        
        Args:
            query: SQL query to execute
            params_list: List of query parameters
        """
        self.clickhouse_client.execute(query, params_list)
    
    def cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the Redis cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        # Convert value to JSON if it's a dictionary or list
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        # Set value in cache
        result = self.redis_cluster.set(key, value, ex=ttl)
        
        return result
    
    def cache_get(self, key: str) -> Any:
        """
        Get a value from the Redis cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        # Get value from cache
        value = self.redis_cluster.get(key)
        
        # Try to parse as JSON
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        
        return None
    
    def cache_hash_set(self, key: str, field: str, value: Any) -> bool:
        """
        Set a hash field in the Redis cache
        
        Args:
            key: Cache key
            field: Hash field
            value: Value to cache
            
        Returns:
            True if successful
        """
        # Convert value to JSON if it's a dictionary or list
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        # Set hash field in cache
        result = self.redis_cluster.hset(key, field, value)
        
        return result > 0
    
    def cache_hash_get(self, key: str, field: str) -> Any:
        """
        Get a hash field from the Redis cache
        
        Args:
            key: Cache key
            field: Hash field
            
        Returns:
            Cached value or None if not found
        """
        # Get hash field from cache
        value = self.redis_cluster.hget(key, field)
        
        # Try to parse as JSON
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        
        return None
    
    def cache_hash_get_all(self, key: str) -> Dict:
        """
        Get all hash fields from the Redis cache
        
        Args:
            key: Cache key
            
        Returns:
            Dictionary of hash fields and values
        """
        # Get all hash fields from cache
        hash_dict = self.redis_cluster.hgetall(key)
        
        # Try to parse values as JSON
        result = {}
        for field, value in hash_dict.items():
            try:
                result[field] = json.loads(value)
            except json.JSONDecodeError:
                result[field] = value
        
        return result
    
    def publish_message(self, topic: str, message: Dict, key: Optional[str] = None) -> None:
        """
        Publish a message to a Kafka topic
        
        Args:
            topic: Kafka topic
            message: Message to publish
            key: Message key
        """
        # Publish message
        future = self.kafka_producer.send(topic, message, key=key)
        
        # Wait for message to be sent
        future.get(timeout=10)
        
        logger.debug(f"Published message to topic {topic}")
    
    def subscribe_to_topics(self, topics: List[str]) -> None:
        """
        Subscribe to Kafka topics
        
        Args:
            topics: List of topics to subscribe to
        """
        self.kafka_consumer.subscribe(topics)
        logger.info(f"Subscribed to Kafka topics: {topics}")
    
    def consume_messages(self, timeout_ms: int = 1000) -> List[Dict]:
        """
        Consume messages from subscribed Kafka topics
        
        Args:
            timeout_ms: Timeout in milliseconds
            
        Returns:
            List of consumed messages
        """
        # Poll for messages
        message_batch = self.kafka_consumer.poll(timeout_ms=timeout_ms)
        
        # Process messages
        messages = []
        for topic_partition, partition_messages in message_batch.items():
            for message in partition_messages:
                messages.append({
                    "topic": topic_partition.topic,
                    "partition": topic_partition.partition,
                    "offset": message.offset,
                    "key": message.key,
                    "value": message.value,
                    "timestamp": message.timestamp
                })
                
                # Commit offset
                self.kafka_consumer.commit({topic_partition: message.offset + 1})
        
        return messages
    
    def create_data_validator(self, dataset_name: str) -> ge.dataset.PandasDataset:
        """
        Create a Great Expectations data validator
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Great Expectations dataset
        """
        import pandas as pd
        
        # Create empty DataFrame
        df = pd.DataFrame()
        
        # Create Great Expectations dataset
        dataset = ge.dataset.PandasDataset(df, dataset_name=dataset_name)
        
        return dataset
    
    def validate_data(self, data: List[Dict], expectations: List[Dict]) -> Dict:
        """
        Validate data using Great Expectations
        
        Args:
            data: Data to validate
            expectations: List of expectations
            
        Returns:
            Validation results
        """
        import pandas as pd
        
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        # Create Great Expectations dataset
        dataset = ge.dataset.PandasDataset(df)
        
        # Add expectations
        for expectation in expectations:
            expectation_type = expectation.pop("expectation_type")
            dataset.expect(expectation_type, **expectation)
        
        # Validate data
        results = dataset.validate()
        
        return results
    
    async def close(self):
        """Close all database connections"""
        # Close PostgreSQL connection pool
        if self.pg_pool:
            await self.pg_pool.close()
        
        # Close Kafka producer
        if self.kafka_producer:
            self.kafka_producer.close()
        
        # Close Kafka consumer
        if self.kafka_consumer:
            self.kafka_consumer.close()
        
        logger.info("All database connections closed")


class DBeaver:
    """
    DBeaver integration for database management
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize DBeaver integration
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.config = self._load_config()
        
        logger.info("DBeaver integration initialized")
    
    def _load_config(self) -> Dict:
        """
        Load DBeaver configuration
        
        Returns:
            Configuration dictionary
        """
        # Default configuration
        config = {
            "team_edition": True,
            "connection_pools": {
                "primary_db": {
                    "name": "Primary PostgreSQL",
                    "driver": "postgresql",
                    "host": self.db_manager.config.get("primary_db", {}).get("connection", {}).get("host"),
                    "port": self.db_manager.config.get("primary_db", {}).get("connection", {}).get("port"),
                    "database": self.db_manager.config.get("primary_db", {}).get("connection", {}).get("database"),
                    "user": self.db_manager.config.get("primary_db", {}).get("connection", {}).get("user"),
                    "password": self.db_manager.config.get("primary_db", {}).get("connection", {}).get("password"),
                    "ssl": self.db_manager.config.get("primary_db", {}).get("connection", {}).get("ssl", True),
                    "ssl_mode": self.db_manager.config.get("primary_db", {}).get("connection", {}).get("ssl_mode", "verify-full"),
                    "ssl_cert": self.db_manager.config.get("primary_db", {}).get("connection", {}).get("ssl_cert"),
                    "ssl_key": self.db_manager.config.get("primary_db", {}).get("connection", {}).get("ssl_key"),
                    "ssl_root_cert": self.db_manager.config.get("primary_db", {}).get("connection", {}).get("ssl_root_cert")
                },
                "analytics_db": {
                    "name": "Analytics ClickHouse",
                    "driver": "clickhouse",
                    "host": self.db_manager.config.get("analytics_db", {}).get("connection", {}).get("host"),
                    "port": self.db_manager.config.get("analytics_db", {}).get("connection", {}).get("port"),
                    "database": self.db_manager.config.get("analytics_db", {}).get("connection", {}).get("database"),
                    "user": self.db_manager.config.get("analytics_db", {}).get("connection", {}).get("user"),
                    "password": self.db_manager.config.get("analytics_db", {}).get("connection", {}).get("password"),
                    "ssl": self.db_manager.config.get("analytics_db", {}).get("connection", {}).get("secure", True),
                    "ssl_ca_cert": self.db_manager.config.get("analytics_db", {}).get("connection", {}).get("ca_cert")
                }
            },
            "query_monitoring": {
                "enabled": True,
                "log_slow_queries": True,
                "slow_query_threshold_ms": 1000,
                "log_all_queries": False
            },
            "schema_migration": {
                "tool": "flyway",
                "migrations_path": "db/migrations",
                "baseline_version": "1.0.0",
                "auto_baseline": True
            }
        }
        
        return config
    
    def export_connection_config(self, output_path: str) -> None:
        """
        Export DBeaver connection configuration
        
        Args:
            output_path: Path to export configuration
        """
        # Create connection configuration
        connections = {}
        
        for pool_id, pool_config in self.config.get("connection_pools", {}).items():
            connections[pool_id] = {
                "name": pool_config.get("name"),
                "driver": pool_config.get("driver"),
                "configuration": {
                    "host": pool_config.get("host"),
                    "port": pool_config.get("port"),
                    "database": pool_config.get("database"),
                    "user": pool_config.get("user"),
                    "password": pool_config.get("password"),
                    "ssl": pool_config.get("ssl"),
                    "ssl_mode": pool_config.get("ssl_mode"),
                    "ssl_cert": pool_config.get("ssl_cert"),
                    "ssl_key": pool_config.get("ssl_key"),
                    "ssl_root_cert": pool_config.get("ssl_root_cert")
                }
            }
        
        # Export configuration
        with open(output_path, 'w') as f:
            json.dump(connections, f, indent=2)
        
        logger.info(f"Exported DBeaver connection configuration to {output_path}")
    
    async def run_query_monitor(self) -> None:
        """Run query monitoring for PostgreSQL"""
        if not self.config.get("query_monitoring", {}).get("enabled", False):
            logger.info("Query monitoring is disabled")
            return
        
        # Get slow query threshold
        slow_query_threshold = self.config.get("query_monitoring", {}).get("slow_query_threshold_ms", 1000)
        
        # Query to get running queries
        query = """
        SELECT pid, usename, datname, client_addr, state, 
               EXTRACT(EPOCH FROM now() - query_start) * 1000 AS duration_ms,
               query
        FROM pg_stat_activity
        WHERE state = 'active' AND pid <> pg_backend_pid()
        """
        
        # Execute query
        results = await self.db_manager.execute_query(query)
        
        # Log slow queries
        for result in results:
            duration_ms = result.get("duration_ms", 0)
            
            if duration_ms >= slow_query_threshold:
                logger.warning(f"Slow query detected (PID: {result.get('pid')}, Duration: {duration_ms:.2f}ms): {result.get('query')}")
            elif self.config.get("query_monitoring", {}).get("log_all_queries", False):
                logger.info(f"Query (PID: {result.get('pid')}, Duration: {duration_ms:.2f}ms): {result.get('query')}")
    
    async def run_schema_migration(self) -> None:
        """Run schema migration using Flyway"""
        # Get migration configuration
        migration_config = self.config.get("schema_migration", {})
        
        if migration_config.get("tool") != "flyway":
            logger.warning(f"Unsupported migration tool: {migration_config.get('tool')}")
            return
        
        # Get migration parameters
        migrations_path = migration_config.get("migrations_path", "db/migrations")
        baseline_version = migration_config.get("baseline_version", "1.0.0")
        auto_baseline = migration_config.get("auto_baseline", True)
        
        # Get database connection parameters
        db_config = self.config.get("connection_pools", {}).get("primary_db", {})
        
        # Build Flyway command
        command = [
            "flyway",
            "-url=jdbc:postgresql://" + db_config.get("host") + ":" + str(db_config.get("port")) + "/" + db_config.get("database"),
            "-user=" + db_config.get("user"),
            "-password=" + db_config.get("password"),
            "-locations=filesystem:" + migrations_path,
            "-baselineVersion=" + baseline_version
        ]
        
        if auto_baseline:
            command.append("-baselineOnMigrate=true")
        
        # Add migrate command
        command.append("migrate")
        
        # Execute Flyway command
        import subprocess
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            logger.info(f"Schema migration completed: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Schema migration failed: {e.stderr}")
            raise


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Initialize DBeaver integration
        dbeaver = DBeaver(db_manager)
        
        # Export DBeaver connection configuration
        dbeaver.export_connection_config("dbeaver_connections.json")
        
        # Run query monitor
        await dbeaver.run_query_monitor()
        
        # Close database connections
        await db_manager.close()
    
    # Run main function
    asyncio.run(main())