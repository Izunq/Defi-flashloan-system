"""
Database adapter interface and implementations.
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Import models
from backend.src.models.block_model import Block, Transaction

logger = logging.getLogger(__name__)

class DatabaseAdapter(ABC):
    """Abstract base class for database adapters."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the database."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the database."""
        pass
    
    @abstractmethod
    def save_block(self, block: Block) -> bool:
        """Save a block to the database."""
        pass
    
    @abstractmethod
    def save_transactions(self, transactions: List[Transaction]) -> bool:
        """Save transactions to the database."""
        pass
    
    @abstractmethod
    def get_block(self, block_number: int) -> Optional[Block]:
        """Get a block from the database."""
        pass
    
    @abstractmethod
    def get_latest_block_number(self) -> Optional[int]:
        """Get the latest block number from the database."""
        pass


class JsonFileAdapter(DatabaseAdapter):
    """JSON file adapter for storing blockchain data."""
    
    def __init__(self, base_dir: str = "data"):
        """Initialize the JSON file adapter."""
        self.base_dir = base_dir
        self.blocks_dir = os.path.join(base_dir, "blocks")
        self.transactions_dir = os.path.join(base_dir, "transactions")
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to the file system."""
        try:
            # Create directories if they don't exist
            os.makedirs(self.blocks_dir, exist_ok=True)
            os.makedirs(self.transactions_dir, exist_ok=True)
            self.connected = True
            logger.info(f"Connected to JSON file storage at {self.base_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to JSON file storage: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from the file system."""
        self.connected = False
        return True
    
    def save_block(self, block: Block) -> bool:
        """Save a block to a JSON file."""
        if not self.connected:
            logger.error("Not connected to JSON file storage")
            return False
        
        try:
            # Convert block to dictionary
            block_dict = block.dict(by_alias=True)
            
            # Convert datetime to string
            block_dict["processed_at"] = block_dict["processed_at"].isoformat()
            
            # Save block to file
            file_path = os.path.join(self.blocks_dir, f"block_{block.number}.json")
            with open(file_path, "w") as f:
                json.dump(block_dict, f, indent=2)
            
            logger.debug(f"Saved block {block.number} to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save block {block.number}: {str(e)}")
            return False
    
    def save_transactions(self, transactions: List[Transaction]) -> bool:
        """Save transactions to JSON files."""
        if not self.connected:
            logger.error("Not connected to JSON file storage")
            return False
        
        try:
            for tx in transactions:
                # Convert transaction to dictionary
                tx_dict = tx.dict(by_alias=True)
                
                # Save transaction to file
                file_path = os.path.join(self.transactions_dir, f"tx_{tx.hash}.json")
                with open(file_path, "w") as f:
                    json.dump(tx_dict, f, indent=2)
                
                logger.debug(f"Saved transaction {tx.hash} to {file_path}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to save transactions: {str(e)}")
            return False
    
    def get_block(self, block_number: int) -> Optional[Block]:
        """Get a block from a JSON file."""
        if not self.connected:
            logger.error("Not connected to JSON file storage")
            return None
        
        try:
            file_path = os.path.join(self.blocks_dir, f"block_{block_number}.json")
            if not os.path.exists(file_path):
                logger.warning(f"Block {block_number} not found")
                return None
            
            with open(file_path, "r") as f:
                block_dict = json.load(f)
            
            # Convert string to datetime
            block_dict["processed_at"] = datetime.fromisoformat(block_dict["processed_at"])
            
            return Block(**block_dict)
        except Exception as e:
            logger.error(f"Failed to get block {block_number}: {str(e)}")
            return None
    
    def get_latest_block_number(self) -> Optional[int]:
        """Get the latest block number from the JSON files."""
        if not self.connected:
            logger.error("Not connected to JSON file storage")
            return None
        
        try:
            # Get all block files
            block_files = [f for f in os.listdir(self.blocks_dir) if f.startswith("block_") and f.endswith(".json")]
            if not block_files:
                logger.warning("No blocks found")
                return None
            
            # Extract block numbers
            block_numbers = [int(f.split("_")[1].split(".")[0]) for f in block_files]
            
            # Return the highest block number
            return max(block_numbers)
        except Exception as e:
            logger.error(f"Failed to get latest block number: {str(e)}")
            return None


try:
    import psycopg2
    import psycopg2.extras
    
    class PostgresAdapter(DatabaseAdapter):
        """PostgreSQL adapter for storing blockchain data."""
        
        def __init__(self, config: Dict[str, Any]):
            """Initialize the PostgreSQL adapter."""
            self.config = config
            self.conn = None
            self.connected = False
        
        def connect(self) -> bool:
            """Connect to the PostgreSQL database."""
            try:
                # Connect to the database
                self.conn = psycopg2.connect(
                    host=self.config.get("host", "localhost"),
                    port=self.config.get("port", 5432),
                    database=self.config.get("database", "blockchain_data"),
                    user=self.config.get("username", "postgres"),
                    password=self.config.get("password", "postgres"),
                    sslmode=self.config.get("ssl_mode", "disable")
                )
                
                # Create tables if they don't exist
                self._create_tables()
                
                self.connected = True
                logger.info(f"Connected to PostgreSQL database at {self.config.get('host')}:{self.config.get('port')}")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL database: {str(e)}")
                return False
        
        def disconnect(self) -> bool:
            """Disconnect from the PostgreSQL database."""
            if self.conn:
                self.conn.close()
            self.connected = False
            return True
        
        def _create_tables(self):
            """Create tables if they don't exist."""
            with self.conn.cursor() as cur:
                # Create blocks table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS blocks (
                        number BIGINT PRIMARY KEY,
                        hash VARCHAR(66) UNIQUE NOT NULL,
                        parent_hash VARCHAR(66) NOT NULL,
                        timestamp BIGINT NOT NULL,
                        miner VARCHAR(42) NOT NULL,
                        size BIGINT NOT NULL,
                        gas_used BIGINT NOT NULL,
                        gas_limit BIGINT NOT NULL,
                        base_fee_per_gas BIGINT,
                        transaction_count INT NOT NULL,
                        processed_at TIMESTAMP NOT NULL
                    )
                """)
                
                # Create transactions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        hash VARCHAR(66) PRIMARY KEY,
                        from_address VARCHAR(42) NOT NULL,
                        to_address VARCHAR(42),
                        value VARCHAR(78) NOT NULL,
                        gas BIGINT NOT NULL,
                        gas_price VARCHAR(78) NOT NULL,
                        input TEXT NOT NULL,
                        nonce BIGINT NOT NULL,
                        transaction_index INT NOT NULL,
                        block_number BIGINT NOT NULL REFERENCES blocks(number),
                        block_hash VARCHAR(66) NOT NULL,
                        timestamp BIGINT NOT NULL
                    )
                """)
                
                self.conn.commit()
        
        def save_block(self, block: Block) -> bool:
            """Save a block to the PostgreSQL database."""
            if not self.connected:
                logger.error("Not connected to PostgreSQL database")
                return False
            
            try:
                with self.conn.cursor() as cur:
                    # Insert block
                    cur.execute("""
                        INSERT INTO blocks (
                            number, hash, parent_hash, timestamp, miner, size,
                            gas_used, gas_limit, base_fee_per_gas, transaction_count, processed_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (number) DO UPDATE SET
                            hash = EXCLUDED.hash,
                            parent_hash = EXCLUDED.parent_hash,
                            timestamp = EXCLUDED.timestamp,
                            miner = EXCLUDED.miner,
                            size = EXCLUDED.size,
                            gas_used = EXCLUDED.gas_used,
                            gas_limit = EXCLUDED.gas_limit,
                            base_fee_per_gas = EXCLUDED.base_fee_per_gas,
                            transaction_count = EXCLUDED.transaction_count,
                            processed_at = EXCLUDED.processed_at
                    """, (
                        block.number, block.hash, block.parent_hash, block.timestamp,
                        block.miner, block.size, block.gas_used, block.gas_limit,
                        block.base_fee_per_gas, block.transaction_count, block.processed_at
                    ))
                    
                    self.conn.commit()
                
                logger.debug(f"Saved block {block.number} to PostgreSQL database")
                return True
            except Exception as e:
                logger.error(f"Failed to save block {block.number}: {str(e)}")
                self.conn.rollback()
                return False
        
        def save_transactions(self, transactions: List[Transaction]) -> bool:
            """Save transactions to the PostgreSQL database."""
            if not self.connected:
                logger.error("Not connected to PostgreSQL database")
                return False
            
            if not transactions:
                return True
            
            try:
                with self.conn.cursor() as cur:
                    # Insert transactions
                    psycopg2.extras.execute_values(
                        cur,
                        """
                        INSERT INTO transactions (
                            hash, from_address, to_address, value, gas, gas_price,
                            input, nonce, transaction_index, block_number, block_hash, timestamp
                        ) VALUES %s
                        ON CONFLICT (hash) DO UPDATE SET
                            from_address = EXCLUDED.from_address,
                            to_address = EXCLUDED.to_address,
                            value = EXCLUDED.value,
                            gas = EXCLUDED.gas,
                            gas_price = EXCLUDED.gas_price,
                            input = EXCLUDED.input,
                            nonce = EXCLUDED.nonce,
                            transaction_index = EXCLUDED.transaction_index,
                            block_number = EXCLUDED.block_number,
                            block_hash = EXCLUDED.block_hash,
                            timestamp = EXCLUDED.timestamp
                        """,
                        [(
                            tx.hash, tx.from_address, tx.to_address, tx.value, tx.gas, tx.gas_price,
                            tx.input, tx.nonce, tx.transaction_index, tx.block_number, tx.block_hash, tx.timestamp
                        ) for tx in transactions]
                    )
                    
                    self.conn.commit()
                
                logger.debug(f"Saved {len(transactions)} transactions to PostgreSQL database")
                return True
            except Exception as e:
                logger.error(f"Failed to save transactions: {str(e)}")
                self.conn.rollback()
                return False
        
        def get_block(self, block_number: int) -> Optional[Block]:
            """Get a block from the PostgreSQL database."""
            if not self.connected:
                logger.error("Not connected to PostgreSQL database")
                return None
            
            try:
                with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    # Get block
                    cur.execute("""
                        SELECT * FROM blocks WHERE number = %s
                    """, (block_number,))
                    
                    block_row = cur.fetchone()
                    if not block_row:
                        logger.warning(f"Block {block_number} not found")
                        return None
                    
                    # Get transactions for this block
                    cur.execute("""
                        SELECT * FROM transactions WHERE block_number = %s
                    """, (block_number,))
                    
                    tx_rows = cur.fetchall()
                    
                    # Convert rows to objects
                    transactions = [Transaction(
                        hash=tx["hash"],
                        from_address=tx["from_address"],
                        to_address=tx["to_address"],
                        value=tx["value"],
                        gas=tx["gas"],
                        gas_price=tx["gas_price"],
                        input=tx["input"],
                        nonce=tx["nonce"],
                        transaction_index=tx["transaction_index"],
                        block_number=tx["block_number"],
                        block_hash=tx["block_hash"],
                        timestamp=tx["timestamp"]
                    ) for tx in tx_rows]
                    
                    return Block(
                        number=block_row["number"],
                        hash=block_row["hash"],
                        parent_hash=block_row["parent_hash"],
                        timestamp=block_row["timestamp"],
                        miner=block_row["miner"],
                        size=block_row["size"],
                        gas_used=block_row["gas_used"],
                        gas_limit=block_row["gas_limit"],
                        base_fee_per_gas=block_row["base_fee_per_gas"],
                        transaction_count=block_row["transaction_count"],
                        transactions=transactions,
                        processed_at=block_row["processed_at"]
                    )
            except Exception as e:
                logger.error(f"Failed to get block {block_number}: {str(e)}")
                return None
        
        def get_latest_block_number(self) -> Optional[int]:
            """Get the latest block number from the PostgreSQL database."""
            if not self.connected:
                logger.error("Not connected to PostgreSQL database")
                return None
            
            try:
                with self.conn.cursor() as cur:
                    # Get latest block number
                    cur.execute("""
                        SELECT MAX(number) FROM blocks
                    """)
                    
                    result = cur.fetchone()
                    if not result or result[0] is None:
                        logger.warning("No blocks found")
                        return None
                    
                    return result[0]
            except Exception as e:
                logger.error(f"Failed to get latest block number: {str(e)}")
                return None
except ImportError:
    logger.warning("psycopg2 not installed, PostgreSQL adapter not available")


try:
    import pymongo
    
    class MongoDBAdapter(DatabaseAdapter):
        """MongoDB adapter for storing blockchain data."""
        
        def __init__(self, config: Dict[str, Any]):
            """Initialize the MongoDB adapter."""
            self.config = config
            self.client = None
            self.db = None
            self.blocks_collection = None
            self.transactions_collection = None
            self.connected = False
        
        def connect(self) -> bool:
            """Connect to the MongoDB database."""
            try:
                # Build connection string
                connection_string = f"mongodb://"
                if self.config.get("username") and self.config.get("password"):
                    connection_string += f"{self.config.get('username')}:{self.config.get('password')}@"
                connection_string += f"{self.config.get('host', 'localhost')}:{self.config.get('port', 27017)}"
                
                # Connect to MongoDB
                self.client = pymongo.MongoClient(connection_string)
                self.db = self.client[self.config.get("database", "blockchain_data")]
                
                # Get collections
                self.blocks_collection = self.db[self.config.get("collections", {}).get("blocks", "blocks")]
                self.transactions_collection = self.db[self.config.get("collections", {}).get("transactions", "transactions")]
                
                # Create indexes
                self.blocks_collection.create_index([("number", pymongo.ASCENDING)], unique=True)
                self.blocks_collection.create_index([("hash", pymongo.ASCENDING)], unique=True)
                self.transactions_collection.create_index([("hash", pymongo.ASCENDING)], unique=True)
                self.transactions_collection.create_index([("block_number", pymongo.ASCENDING)])
                
                self.connected = True
                logger.info(f"Connected to MongoDB database at {self.config.get('host')}:{self.config.get('port')}")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB database: {str(e)}")
                return False
        
        def disconnect(self) -> bool:
            """Disconnect from the MongoDB database."""
            if self.client:
                self.client.close()
            self.connected = False
            return True
        
        def save_block(self, block: Block) -> bool:
            """Save a block to the MongoDB database."""
            if not self.connected:
                logger.error("Not connected to MongoDB database")
                return False
            
            try:
                # Convert block to dictionary
                block_dict = block.dict(by_alias=True)
                
                # Remove transactions from block
                block_dict.pop("transactions", None)
                
                # Insert or update block
                self.blocks_collection.update_one(
                    {"number": block.number},
                    {"$set": block_dict},
                    upsert=True
                )
                
                logger.debug(f"Saved block {block.number} to MongoDB database")
                return True
            except Exception as e:
                logger.error(f"Failed to save block {block.number}: {str(e)}")
                return False
        
        def save_transactions(self, transactions: List[Transaction]) -> bool:
            """Save transactions to the MongoDB database."""
            if not self.connected:
                logger.error("Not connected to MongoDB database")
                return False
            
            if not transactions:
                return True
            
            try:
                # Convert transactions to dictionaries
                tx_dicts = [tx.dict(by_alias=True) for tx in transactions]
                
                # Insert or update transactions
                for tx_dict in tx_dicts:
                    self.transactions_collection.update_one(
                        {"hash": tx_dict["hash"]},
                        {"$set": tx_dict},
                        upsert=True
                    )
                
                logger.debug(f"Saved {len(transactions)} transactions to MongoDB database")
                return True
            except Exception as e:
                logger.error(f"Failed to save transactions: {str(e)}")
                return False
        
        def get_block(self, block_number: int) -> Optional[Block]:
            """Get a block from the MongoDB database."""
            if not self.connected:
                logger.error("Not connected to MongoDB database")
                return None
            
            try:
                # Get block
                block_doc = self.blocks_collection.find_one({"number": block_number})
                if not block_doc:
                    logger.warning(f"Block {block_number} not found")
                    return None
                
                # Get transactions for this block
                tx_docs = self.transactions_collection.find({"block_number": block_number})
                
                # Convert documents to objects
                transactions = [Transaction(**tx_doc) for tx_doc in tx_docs]
                
                # Add transactions to block
                block_doc["transactions"] = transactions
                
                return Block(**block_doc)
            except Exception as e:
                logger.error(f"Failed to get block {block_number}: {str(e)}")
                return None
        
        def get_latest_block_number(self) -> Optional[int]:
            """Get the latest block number from the MongoDB database."""
            if not self.connected:
                logger.error("Not connected to MongoDB database")
                return None
            
            try:
                # Get latest block
                latest_block = self.blocks_collection.find_one(
                    {},
                    sort=[("number", pymongo.DESCENDING)]
                )
                
                if not latest_block:
                    logger.warning("No blocks found")
                    return None
                
                return latest_block["number"]
            except Exception as e:
                logger.error(f"Failed to get latest block number: {str(e)}")
                return None
except ImportError:
    logger.warning("pymongo not installed, MongoDB adapter not available")


def get_database_adapter(config: Dict[str, Any]) -> DatabaseAdapter:
    """Get a database adapter based on the configuration."""
    db_type = config.get("type", "json_files").lower()
    
    if db_type == "postgresql":
        try:
            return PostgresAdapter(config.get("connection", {}))
        except NameError:
            logger.warning("PostgreSQL adapter not available, falling back to JSON files")
            return JsonFileAdapter()
    elif db_type == "mongodb":
        try:
            return MongoDBAdapter(config.get("connection", {}))
        except NameError:
            logger.warning("MongoDB adapter not available, falling back to JSON files")
            return JsonFileAdapter()
    else:
        return JsonFileAdapter()