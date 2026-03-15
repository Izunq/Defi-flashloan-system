import os
import json
import time
import logging
import argparse
from web3 import Web3
from typing import Dict, List, Any
from dotenv import load_dotenv
from pathlib import Path
import yaml
import hashlib
from CausalityEngine import CausalityEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("oracle_connector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OracleConnector")

class OracleConnector:
    """
    Connects the Causality Engine to the Pre-Cognitive Oracle contract,
    allowing off-chain predictions to be posted on-chain.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Oracle Connector
        
        Args:
            config_path: Path to the configuration file
        """
        # Load environment variables
        load_dotenv()
        
        self.config_path = config_path or "oracle_connector_config.yaml"
        self._load_config(self.config_path)
        self._setup_directories()
        self._init_web3()
        self._init_contracts()
        self._init_causality_engine()
        
        logger.info(f"Oracle Connector initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from YAML file
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dict containing configuration
        """
        try:
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
                logger.info(f"Configuration loaded from {config_path}")
                return self.config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            # Default configuration
            self.config = {
                "web3": {
                    "provider_url": os.getenv("WEB3_PROVIDER_URL", "http://localhost:8545"),
                    "chain_id": int(os.getenv("CHAIN_ID", "1")),
                    "gas_limit": 3000000,
                    "gas_price": "auto"
                },
                "contracts": {
                    "oracle_address": os.getenv("ORACLE_ADDRESS", "")
                },
                "causality_engine": {
                    "config_path": "causality_engine_config.yaml"
                },
                "oracle_connector": {
                    "update_frequency": 3600,  # seconds
                    "min_confidence": 7000,    # basis points (70%)
                    "retry_attempts": 3,
                    "retry_delay": 60          # seconds
                },
                "data_dir": "data/oracle_connector"
            }
            return self.config
    
    def _setup_directories(self):
        """Create necessary directories for data storage"""
        os.makedirs(self.config.get("data_dir", "data/oracle_connector"), exist_ok=True)
    
    def _init_web3(self):
        """Initialize Web3 connection"""
        provider_url = self.config.get("web3", {}).get("provider_url", "http://localhost:8545")
        
        try:
            if provider_url.startswith("http"):
                self.w3 = Web3(Web3.HTTPProvider(provider_url))
            elif provider_url.startswith("ws"):
                self.w3 = Web3(Web3.WebsocketProvider(provider_url))
            else:
                raise ValueError(f"Unsupported provider URL: {provider_url}")
            
            if not self.w3.is_connected():
                raise ConnectionError(f"Failed to connect to provider at {provider_url}")
              # SECURITY: Use secure transaction signer instead of private key
            try:
                from secure_transaction_signer import SecureTransactionSigner
                signer = SecureTransactionSigner()
                account = signer.get_account()
                self.w3.eth.default_account = account.address
                logger.info(f"Using secure account: {account.address}")
            except ImportError:
                logger.error("SECURITY ERROR: SecureTransactionSigner not available. Direct private key usage is prohibited.")
                raise RuntimeError("SECURITY ERROR: Direct private key usage is prohibited.")
            
            logger.info(f"Connected to Web3 provider at {provider_url}")
            logger.info(f"Current block number: {self.w3.eth.block_number}")
            
        except Exception as e:
            logger.error(f"Error initializing Web3: {str(e)}")
            raise
    
    def _init_contracts(self):
        """Initialize contract instances"""
        try:
            # Load Pre-Cognitive Oracle ABI
            oracle_abi_path = "abi/PreCognitiveOracle.json"
            with open(oracle_abi_path, 'r') as f:
                oracle_abi = json.load(f)
            
            # Initialize Pre-Cognitive Oracle contract
            oracle_address = self.config.get("contracts", {}).get("oracle_address", "")
            if not oracle_address:
                logger.warning("Oracle address not configured")
                self.oracle = None
            else:
                self.oracle = self.w3.eth.contract(
                    address=self.w3.to_checksum_address(oracle_address),
                    abi=oracle_abi
                )
                logger.info(f"Initialized Pre-Cognitive Oracle contract at {oracle_address}")
            
        except Exception as e:
            logger.error(f"Error initializing contracts: {str(e)}")
            raise
    
    def _init_causality_engine(self):
        """Initialize the Causality Engine"""
        try:
            causality_config_path = self.config.get("causality_engine", {}).get("config_path", "causality_engine_config.yaml")
            self.causality_engine = CausalityEngine(config_path=causality_config_path)
            logger.info(f"Initialized Causality Engine with config from {causality_config_path}")
        except Exception as e:            logger.error(f"Error initializing Causality Engine: {str(e)}")
            raise
    
    def _send_transaction(self, tx: Dict) -> Dict:
        """
        Send a transaction to the blockchain
        
        Args:
            tx: Transaction to send
            
        Returns:
            Transaction receipt
        """
        try:
            # SECURITY: Use secure transaction signer instead of private key
            try:
                from secure_transaction_signer import SecureTransactionSigner
                signer = SecureTransactionSigner()
                signed_tx = signer.sign_transaction(tx)
            except ImportError:
                raise RuntimeError("SECURITY ERROR: SecureTransactionSigner not available. Direct private key usage is prohibited.")
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            logger.info(f"Transaction confirmed: {tx_receipt.transactionHash.hex()}")
            
            return tx_receipt
            
        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            raise
    
    def register_event_types(self) -> Dict:
        """
        Register event types from the Causality Engine in the Oracle
        
        Returns:
            Dict containing registration results
        """
        if not self.oracle:
            logger.error("Oracle contract not initialized")
            return {"status": "error", "message": "Oracle contract not initialized"}
        
        results = {
            "registered": [],
            "failed": []
        }
        
        # Get event types from Causality Engine config
        event_types = self.causality_engine.config.get("event_types", [])
        
        for event_type in event_types:
            try:
                # Check if event type already exists
                # This is a simplified check - in a real implementation, you would query the contract
                
                # Register event type
                tx = self.oracle.functions.registerEventType(
                    event_type,
                    f"Prediction for {event_type} events"
                ).build_transaction({
                    'from': self.w3.eth.default_account,
                    'gas': self.config.get("web3", {}).get("gas_limit", 3000000),
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(self.w3.eth.default_account)
                })
                
                receipt = self._send_transaction(tx)
                
                # Parse event to get event type ID
                event_type_id = None
                for log in receipt.logs:
                    try:
                        event = self.oracle.events.EventTypeRegistered().process_log(log)
                        event_type_id = event.args.eventTypeId
                        break
                    except:
                        continue
                
                if event_type_id:
                    results["registered"].append({
                        "name": event_type,
                        "id": event_type_id.hex()
                    })
                    logger.info(f"Registered event type: {event_type} with ID {event_type_id.hex()}")
                else:
                    results["failed"].append({
                        "name": event_type,
                        "error": "Failed to parse event type ID from receipt"
                    })
                    logger.warning(f"Failed to parse event type ID for {event_type}")
                
            except Exception as e:
                results["failed"].append({
                    "name": event_type,
                    "error": str(e)
                })
                logger.error(f"Error registering event type {event_type}: {str(e)}")
        
        return results
    
    def register_time_horizons(self) -> Dict:
        """
        Register time horizons from the Causality Engine in the Oracle
        
        Returns:
            Dict containing registration results
        """
        if not self.oracle:
            logger.error("Oracle contract not initialized")
            return {"status": "error", "message": "Oracle contract not initialized"}
        
        results = {
            "registered": [],
            "failed": []
        }
        
        # Get time horizons from Causality Engine config
        time_horizons = self.causality_engine.config.get("time_horizons", [])
        
        for horizon in time_horizons:
            try:
                name = horizon.get("name", "")
                days = horizon.get("days", 0)
                
                if not name or not days:
                    results["failed"].append({
                        "name": name,
                        "error": "Invalid horizon configuration"
                    })
                    continue
                
                # Convert days to seconds
                duration_seconds = days * 86400
                
                # Register time horizon
                tx = self.oracle.functions.registerTimeHorizon(
                    name,
                    duration_seconds
                ).build_transaction({
                    'from': self.w3.eth.default_account,
                    'gas': self.config.get("web3", {}).get("gas_limit", 3000000),
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(self.w3.eth.default_account)
                })
                
                receipt = self._send_transaction(tx)
                
                # Parse event to get horizon ID
                horizon_id = None
                for log in receipt.logs:
                    try:
                        event = self.oracle.events.TimeHorizonRegistered().process_log(log)
                        horizon_id = event.args.horizonId
                        break
                    except:
                        continue
                
                if horizon_id:
                    results["registered"].append({
                        "name": name,
                        "days": days,
                        "id": horizon_id.hex()
                    })
                    logger.info(f"Registered time horizon: {name} ({days} days) with ID {horizon_id.hex()}")
                else:
                    results["failed"].append({
                        "name": name,
                        "error": "Failed to parse horizon ID from receipt"
                    })
                    logger.warning(f"Failed to parse horizon ID for {name}")
                
            except Exception as e:
                results["failed"].append({
                    "name": horizon.get("name", "unknown"),
                    "error": str(e)
                })
                logger.error(f"Error registering time horizon {horizon.get('name', 'unknown')}: {str(e)}")
        
        return results
    
    def post_probabilities(self) -> Dict:
        """
        Post event probabilities from the Causality Engine to the Oracle
        
        Returns:
            Dict containing posting results
        """
        if not self.oracle:
            logger.error("Oracle contract not initialized")
            return {"status": "error", "message": "Oracle contract not initialized"}
        
        results = {
            "posted": [],
            "failed": []
        }
        
        # Generate event probabilities from Causality Engine
        event_probabilities = self.causality_engine.generate_event_probabilities()
        
        # Remove metadata
        metadata = event_probabilities.pop("metadata", {})
        
        # Get registered event types and time horizons
        # In a real implementation, you would query the contract
        # For this example, we'll use a simplified approach
        
        # Prepare batch arrays
        event_type_ids = []
        horizon_ids = []
        probabilities = []
        confidences = []
        data_hashes = []
        
        # Process each event type
        for event_type, horizons in event_probabilities.items():
            # Generate event type ID (this should match the ID in the contract)
            event_type_id = self.w3.keccak(text=event_type)
            
            for horizon_name, data in horizons.items():
                # Generate horizon ID (this should match the ID in the contract)
                horizon_id = self.w3.keccak(text=horizon_name)
                
                probability = data.get("probability", 0)
                confidence = data.get("confidence", 0)
                
                # Skip if confidence is below threshold
                min_confidence = self.config.get("oracle_connector", {}).get("min_confidence", 7000)
                if confidence < min_confidence:
                    logger.info(f"Skipping {event_type}/{horizon_name} due to low confidence: {confidence} < {min_confidence}")
                    continue
                
                # Generate data hash
                data_json = json.dumps(data, sort_keys=True)
                data_hash = self.w3.keccak(text=data_json)
                
                # Add to batch arrays
                event_type_ids.append(event_type_id)
                horizon_ids.append(horizon_id)
                probabilities.append(probability)
                confidences.append(confidence)
                data_hashes.append(data_hash)
        
        # Post probabilities in batch
        if event_type_ids:
            try:
                tx = self.oracle.functions.postMultipleProbabilities(
                    event_type_ids,
                    horizon_ids,
                    probabilities,
                    confidences,
                    data_hashes
                ).build_transaction({
                    'from': self.w3.eth.default_account,
                    'gas': self.config.get("web3", {}).get("gas_limit", 3000000),
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(self.w3.eth.default_account)
                })
                
                receipt = self._send_transaction(tx)
                
                # Parse events to get probability IDs
                for log in receipt.logs:
                    try:
                        event = self.oracle.events.ProbabilityPosted().process_log(log)
                        
                        results["posted"].append({
                            "eventTypeId": event.args.eventTypeId.hex(),
                            "horizonId": event.args.horizonId.hex(),
                            "probabilityId": event.args.probabilityId.hex(),
                            "probability": event.args.probability,
                            "confidence": event.args.confidence,
                            "expirationTime": event.args.expirationTime
                        })
                        
                        logger.info(f"Posted probability: {event.args.probabilityId.hex()}")
                    except:
                        continue
                
                logger.info(f"Posted {len(results['posted'])} probabilities to the Oracle")
                
            except Exception as e:
                for i in range(len(event_type_ids)):
                    results["failed"].append({
                        "eventTypeId": event_type_ids[i].hex(),
                        "horizonId": horizon_ids[i].hex(),
                        "probability": probabilities[i],
                        "confidence": confidences[i],
                        "error": str(e)
                    })
                
                logger.error(f"Error posting probabilities: {str(e)}")
        else:
            logger.info("No probabilities to post")
        
        return results
    
    def run(self, register: bool = False) -> Dict:
        """
        Run the Oracle Connector
        
        Args:
            register: Whether to register event types and time horizons
            
        Returns:
            Dict containing run results
        """
        logger.info("Starting Oracle Connector")
        
        results = {
            "status": "success",
            "timestamp": int(time.time())
        }
        
        try:
            # Register event types and time horizons if requested
            if register:
                logger.info("Registering event types and time horizons")
                event_type_results = self.register_event_types()
                time_horizon_results = self.register_time_horizons()
                
                results["registration"] = {
                    "eventTypes": event_type_results,
                    "timeHorizons": time_horizon_results
                }
            
            # Post probabilities
            probability_results = self.post_probabilities()
            results["probabilities"] = probability_results
            
            logger.info("Oracle Connector run completed")
            
        except Exception as e:
            logger.error(f"Error running Oracle Connector: {str(e)}")
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    def run_continuous(self, register: bool = False) -> None:
        """
        Run the Oracle Connector continuously
        
        Args:
            register: Whether to register event types and time horizons on startup
        """
        logger.info("Starting Oracle Connector in continuous mode")
        
        # Register on startup if requested
        if register:
            try:
                logger.info("Registering event types and time horizons")
                self.register_event_types()
                self.register_time_horizons()
            except Exception as e:
                logger.error(f"Error during registration: {str(e)}")
        
        # Get update frequency
        update_frequency = self.config.get("oracle_connector", {}).get("update_frequency", 3600)
        
        try:
            while True:
                start_time = time.time()
                
                try:
                    # Post probabilities
                    self.post_probabilities()
                    logger.info(f"Posted probabilities to Oracle")
                except Exception as e:
                    logger.error(f"Error posting probabilities: {str(e)}")
                
                # Calculate sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0, update_frequency - elapsed)
                
                logger.info(f"Sleeping for {sleep_time:.2f} seconds until next update")
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Oracle Connector stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error in continuous mode: {str(e)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Oracle Connector for Causality Engine")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--register", action="store_true", help="Register event types and time horizons")
    parser.add_argument("--continuous", action="store_true", help="Run in continuous mode")
    
    args = parser.parse_args()
    
    # Initialize and run the Oracle Connector
    connector = OracleConnector(config_path=args.config)
    
    if args.continuous:
        connector.run_continuous(register=args.register)
    else:
        result = connector.run(register=args.register)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()