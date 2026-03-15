import os
import json
import time
import logging
import numpy as np
import tensorflow as tf
from web3 import Web3
from typing import Dict, List, Tuple, Any
from dotenv import load_dotenv
import yaml
import random
import subprocess
import hashlib
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("zk_rl_agent_v40.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ZK-RL-Agent")

class ZKRLAgent:
    """
    ZK-RL Agent that combines Zero-Knowledge proofs with Reinforcement Learning
    to generate verifiable intelligent strategies.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the ZK-RL Agent
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path or "zk_rl_config.yaml"
        self._load_config(self.config_path)
        self._setup_directories()
        self._init_web3()
        self._init_contracts()
        self._init_rl_model()
        self._init_zk_prover()
        
        logger.info(f"ZK-RL Agent V40 initialized")
    
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
                    "provider_url": "http://localhost:8545",
                    "chain_id": 1,
                    "gas_limit": 3000000,
                    "gas_price": "auto"
                },
                "contracts": {
                    "trust_curve_address": "",
                    "strategy_generator_address": "",
                    "strategy_incubator_address": ""
                },
                "rl_params": {
                    "learning_rate": 0.001,
                    "gamma": 0.95,
                    "epsilon": 0.1,
                    "batch_size": 32,
                    "hidden_layers": [64, 128, 64]
                },
                "zk_params": {
                    "circuit_path": "prover/circuit_v40.circom",
                    "prover_path": "prover",
                    "witness_generator": "prover/generate_witness.js",
                    "proving_key": "prover/proving_key.json",
                    "verification_key": "prover/verification_key.json"
                },
                "data_dir": "data/zk_rl"
            }
            return self.config
    
    def _setup_directories(self):
        """Create necessary directories for data storage"""
        os.makedirs(self.config.get("data_dir", "data/zk_rl"), exist_ok=True)
        os.makedirs(os.path.join(self.config.get("data_dir", "data/zk_rl"), "models"), exist_ok=True)
        os.makedirs(os.path.join(self.config.get("data_dir", "data/zk_rl"), "proofs"), exist_ok=True)
        os.makedirs(os.path.join(self.config.get("data_dir", "data/zk_rl"), "inputs"), exist_ok=True)
    
    def _init_web3(self):
        """Initialize Web3 connection"""
        try:
            web3_config = self.config.get("web3", {})
            provider_url = web3_config.get("provider_url", "http://localhost:8545")
            
            # Connect to Ethereum node
            self.w3 = Web3(Web3.HTTPProvider(provider_url))
            
            # Check connection
            if not self.w3.is_connected():
                logger.error(f"Failed to connect to Ethereum node at {provider_url}")
                raise ConnectionError(f"Failed to connect to Ethereum node at {provider_url}")
              # Initialize secure transaction signer instead of private key
            from secure_transaction_signer import SecureTransactionSigner
            self.transaction_signer = SecureTransactionSigner.from_hsm()  # Use HSM in production
            self.account_address = self.transaction_signer.get_address()
            self.w3.eth.default_account = self.account_address
            logger.info(f"Using secure transaction signer with address: {self.account_address}")
            
            logger.info(f"Connected to Ethereum node at {provider_url}")
            logger.info(f"Current block number: {self.w3.eth.block_number}")
            
        except Exception as e:
            logger.error(f"Error initializing Web3: {str(e)}")
            raise
    
    def _init_contracts(self):
        """Initialize contract interfaces"""
        try:
            contracts_config = self.config.get("contracts", {})
            
            # Load contract ABIs
            with open("abi/TrustCurve.json", "r") as f:
                trust_curve_abi = json.load(f)
            
            with open("abi/StrategyGeneratorV37.json", "r") as f:
                strategy_generator_abi = json.load(f)
            
            with open("abi/StrategyIncubatorV33.json", "r") as f:
                strategy_incubator_abi = json.load(f)
            
            # Initialize contract instances
            self.trust_curve = self.w3.eth.contract(
                address=contracts_config.get("trust_curve_address"),
                abi=trust_curve_abi
            )
            
            self.strategy_generator = self.w3.eth.contract(
                address=contracts_config.get("strategy_generator_address"),
                abi=strategy_generator_abi
            )
            
            self.strategy_incubator = self.w3.eth.contract(
                address=contracts_config.get("strategy_incubator_address"),
                abi=strategy_incubator_abi
            )
            
            logger.info("Contract interfaces initialized")
            
        except Exception as e:
            logger.error(f"Error initializing contracts: {str(e)}")
            raise
    
    def _init_rl_model(self):
        """Initialize the Reinforcement Learning model"""
        try:
            # Get RL parameters from config
            rl_params = self.config.get("rl_params", {})
            self.learning_rate = rl_params.get("learning_rate", 0.001)
            self.hidden_layers = rl_params.get("hidden_layers", [64, 128, 64])
            
            # Define state and action dimensions
            self.state_dim = 10  # Market conditions + strategy parameters
            self.action_dim = 5  # Number of parameters to adjust
            
            # Create RL model
            self.model = self._build_rl_model()
            
            # Load model if exists
            model_path = os.path.join(self.config.get("data_dir", "data/zk_rl"), "models", "rl_model.h5")
            if os.path.exists(model_path):
                self.model.load_weights(model_path)
                logger.info(f"RL model loaded from {model_path}")
            else:
                logger.info("Initialized new RL model")
            
        except Exception as e:
            logger.error(f"Error initializing RL model: {str(e)}")
            raise
    
    def _build_rl_model(self):
        """Build a Reinforcement Learning model"""
        model = tf.keras.Sequential()
        
        # Input layer
        model.add(tf.keras.layers.Dense(self.hidden_layers[0], activation='relu', input_shape=(self.state_dim,)))
        
        # Hidden layers
        for units in self.hidden_layers[1:]:
            model.add(tf.keras.layers.Dense(units, activation='relu'))
        
        # Output layer
        model.add(tf.keras.layers.Dense(self.action_dim))
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse'
        )
        
        return model
    
    def _init_zk_prover(self):
        """Initialize the Zero-Knowledge prover"""
        try:
            zk_params = self.config.get("zk_params", {})
            self.circuit_path = zk_params.get("circuit_path", "prover/circuit_v40.circom")
            self.prover_path = zk_params.get("prover_path", "prover")
            
            # Check if circuit file exists
            if not os.path.exists(self.circuit_path):
                logger.error(f"Circuit file not found: {self.circuit_path}")
                raise FileNotFoundError(f"Circuit file not found: {self.circuit_path}")
            
            logger.info("ZK prover initialized")
            
        except Exception as e:
            logger.error(f"Error initializing ZK prover: {str(e)}")
            raise
    
    def _send_transaction(self, tx: Dict) -> Dict:
        """
        Send a transaction to the blockchain
        
        Args:            tx: Transaction dictionary
            
        Returns:
            Transaction receipt
        """
        try:
            # Use secure transaction signer
            signed_tx = self.transaction_signer.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx)
            
            # Wait for the transaction to be mined
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            logger.info(f"Transaction confirmed: {receipt['transactionHash'].hex()}")
            
            return receipt
        except Exception as e:
            logger.error(f"Transaction error: {str(e)}")
            raise
    
    def generate_strategy_with_zk_proof(self, base_strategy_id: int) -> Dict:
        """
        Generate a new strategy with a ZK proof of its RL-based intelligence
        
        Args:
            base_strategy_id: ID of the base strategy to improve
            
        Returns:
            Dict containing generation result
        """
        try:
            logger.info(f"Generating strategy with ZK proof based on strategy {base_strategy_id}")
            
            # 1. Fetch base strategy data
            strategy_data = self.fetch_strategy_data(base_strategy_id)
            
            # 2. Fetch market conditions
            market_conditions = self.fetch_market_conditions()
            
            # 3. Prepare state for RL model
            state = self.prepare_state(strategy_data, market_conditions)
            
            # 4. Generate new parameters using RL model
            new_parameters = self.generate_parameters(state)
            
            # 5. Generate ZK proof
            proof_data = self.generate_zk_proof(
                strategy_id=base_strategy_id,
                market_conditions=market_conditions,
                model_weights=self.get_model_weights(),
                model_output=new_parameters,
                actual_parameters=new_parameters  # In a real implementation, these might differ slightly
            )
            
            # 6. Submit to blockchain
            result = self.submit_to_blockchain(base_strategy_id, new_parameters, proof_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating strategy with ZK proof: {str(e)}")
            raise
    
    def fetch_strategy_data(self, strategy_id: int) -> Dict:
        """
        Fetch strategy data from the blockchain
        
        Args:
            strategy_id: ID of the strategy
            
        Returns:
            Dict containing strategy data
        """
        try:
            # Get strategy scorecard from TrustCurve
            scorecard = self.trust_curve.functions.getStrategyScorecard(strategy_id).call()
            
            # Get strategy details from StrategyIncubator
            strategy_info = self.strategy_incubator.functions.getStrategy(strategy_id).call()
            
            # Combine data
            strategy_data = {
                "strategyId": strategy_id,
                "strategyAddress": strategy_info[0],
                "proposer": strategy_info[1],
                "totalExecutions": scorecard[0],
                "successfulExecutions": scorecard[1],
                "failedExecutions": scorecard[2],
                "totalProfitVerified": scorecard[3],
                "winRate": scorecard[4],
                "trustScore": scorecard[5],
                "lastExecutionTime": scorecard[6],
                "isActive": strategy_info[3]
            }
            
            return strategy_data
            
        except Exception as e:
            logger.error(f"Error fetching strategy data for ID {strategy_id}: {str(e)}")
            return {}
    
    def fetch_market_conditions(self) -> Dict:
        """
        Fetch current market conditions
        
        Returns:
            Dict containing market conditions
        """
        # In a real implementation, this would fetch data from oracles or APIs
        
        # Mock implementation
        return {
            "gasPrice": self.w3.eth.gas_price / 1e9,  # Convert to Gwei
            "ethPrice": 2000 + random.uniform(-100, 100),
            "marketVolatility": random.uniform(0.1, 0.5),
            "liquidityDepth": random.uniform(1000000, 10000000),
            "blockTime": self.w3.eth.get_block('latest').timestamp
        }
    
    def prepare_state(self, strategy_data: Dict, market_conditions: Dict) -> np.ndarray:
        """
        Prepare the state vector for the RL model
        
        Args:
            strategy_data: Strategy data
            market_conditions: Market conditions
            
        Returns:
            State vector as numpy array
        """
        # Normalize values to appropriate ranges
        state = np.array([
            strategy_data.get("winRate", 0) / 10000,  # Win rate (0-1)
            strategy_data.get("totalExecutions", 0) / 1000,  # Executions (normalized)
            strategy_data.get("failedExecutions", 0) / max(1, strategy_data.get("totalExecutions", 1)),  # Failure rate
            strategy_data.get("trustScore", 0) / 100,  # Trust score (0-1)
            strategy_data.get("totalProfitVerified", 0) / 1e18,  # Profit (normalized)
            market_conditions.get("gasPrice", 0) / 100,  # Gas price in Gwei (normalized)
            market_conditions.get("ethPrice", 2000) / 5000,  # ETH price (normalized)
            market_conditions.get("marketVolatility", 0.2),  # Volatility (0-1)
            market_conditions.get("liquidityDepth", 5000000) / 1e7,  # Liquidity (normalized)
            (market_conditions.get("blockTime", 0) % 86400) / 86400  # Time of day (0-1)
        ])
        
        return state
    
    def generate_parameters(self, state: np.ndarray) -> np.ndarray:
        """
        Generate strategy parameters using the RL model
        
        Args:
            state: Current state vector
            
        Returns:
            Array of strategy parameters
        """
        # Get raw output from model
        raw_output = self.model.predict(state.reshape(1, -1), verbose=0)[0]
        
        # Scale and constrain the parameters to appropriate ranges
        parameters = np.array([
            np.clip(raw_output[0] * 10, 1, 10),  # Risk level (1-10)
            np.clip(raw_output[1] * 100, 5, 50),  # Min profit threshold (5-50 basis points)
            np.clip(raw_output[2] * 200, 10, 100),  # Max slippage (10-100 basis points)
            np.clip(raw_output[3] * 300, 30, 300),  # Execution time limit (30-300 seconds)
            np.clip(raw_output[4] * 2, 1.0, 2.0)  # Gas limit multiplier (1.0-2.0)
        ])
        
        return parameters
    
    def get_model_weights(self) -> np.ndarray:
        """
        Get the weights of the RL model
        
        Returns:
            Flattened array of model weights
        """
        weights = []
        for layer in self.model.layers:
            layer_weights = layer.get_weights()
            if layer_weights:
                weights.extend([w.flatten() for w in layer_weights])
        
        # Flatten all weights into a single array
        flattened_weights = np.concatenate([w for w in weights])
        
        # Truncate or pad to ensure consistent size (for the ZK circuit)
        target_size = 100  # Must match the circuit definition
        if len(flattened_weights) > target_size:
            return flattened_weights[:target_size]
        elif len(flattened_weights) < target_size:
            return np.pad(flattened_weights, (0, target_size - len(flattened_weights)))
        else:
            return flattened_weights
    
    def generate_zk_proof(self, strategy_id: int, market_conditions: Dict, 
                         model_weights: np.ndarray, model_output: np.ndarray, 
                         actual_parameters: np.ndarray) -> Dict:
        """
        Generate a Zero-Knowledge proof that the strategy parameters were generated
        by the RL model given the market conditions
        
        Args:
            strategy_id: ID of the strategy
            market_conditions: Market conditions used as input
            model_weights: Weights of the RL model
            model_output: Output from the RL model
            actual_parameters: Actual parameters used in the strategy
            
        Returns:
            Dict containing proof data
        """
        try:
            # 1. Prepare input for the circuit
            timestamp = int(time.time())
            
            circuit_input = {
                "strategyId": strategy_id,
                "timestamp": timestamp,
                "marketConditions": [
                    int(market_conditions.get("gasPrice", 0) * 1e9),  # Convert to wei
                    int(market_conditions.get("ethPrice", 0) * 1e2),  # Scale by 100
                    int(market_conditions.get("marketVolatility", 0) * 1e4),  # Scale by 10000
                    int(market_conditions.get("liquidityDepth", 0)),
                    int(market_conditions.get("blockTime", 0))
                ],
                "modelWeights": model_weights.tolist(),
                "modelOutput": model_output.tolist(),
                "actualParameters": actual_parameters.tolist()
            }
            
            # 2. Save input to file
            input_path = os.path.join(self.config.get("data_dir", "data/zk_rl"), "inputs", f"input_{strategy_id}_{timestamp}.json")
            with open(input_path, 'w') as f:
                json.dump(circuit_input, f)
            
            # 3. In a real implementation, this would call the ZK prover to generate a proof
            # For this example, we'll simulate the proof generation
            
            # Compute a hash of the input as a simulated proof
            proof_hash = hashlib.sha256(json.dumps(circuit_input).encode()).hexdigest()
            
            # 4. Return proof data
            proof_data = {
                "strategyId": strategy_id,
                "timestamp": timestamp,
                "proofHash": "0x" + proof_hash,
                "isValid": True
            }
            
            logger.info(f"Generated ZK proof for strategy {strategy_id}")
            
            return proof_data
            
        except Exception as e:
            logger.error(f"Error generating ZK proof: {str(e)}")
            raise
    
    def submit_to_blockchain(self, base_strategy_id: int, parameters: np.ndarray, proof_data: Dict) -> Dict:
        """
        Submit the new strategy and its ZK proof to the blockchain
        
        Args:
            base_strategy_id: ID of the base strategy
            parameters: Strategy parameters
            proof_data: ZK proof data
            
        Returns:
            Dict containing submission result
        """
        try:
            # 1. Generate bytecode hash (in a real implementation, this would be the actual bytecode)
            bytecode_hash = self.w3.keccak(text=f"strategy_{base_strategy_id}_{int(time.time())}").hex()
            
            # 2. Generate metadata URI
            metadata_uri = f"ipfs://QmZKLGf6hcQRnPSQPgz5LXczZKqbP4LQUTuMNi9ZdVK6Hx/{base_strategy_id}"
            
            # 3. Generate new strategy
            tx = self.strategy_generator.functions.generateStrategy(
                base_strategy_id,
                bytecode_hash,
                metadata_uri
            ).build_transaction({
                'from': self.w3.eth.default_account,
                'gas': self.config.get("web3", {}).get("gas_limit", 3000000),
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.w3.eth.default_account)
            })
            
            receipt = self._send_transaction(tx)
            
            # 4. Parse events to get generation ID
            generation_id = None
            for log in receipt.logs:
                try:
                    event = self.strategy_generator.events.StrategyGenerated().process_log(log)
                    generation_id = event.args.generationId
                    break
                except:
                    continue
            
            if not generation_id:
                raise Exception("Failed to get generation ID from transaction receipt")
            
            # 5. Submit ZK proof
            # In a real implementation, this would call a function on a contract
            # that verifies the ZK proof and updates the trust score
            
            # For this example, we'll simulate the proof submission
            logger.info(f"Simulating ZK proof submission for generation {generation_id}")
            
            # 6. Return result
            result = {
                "baseStrategyId": base_strategy_id,
                "generationId": generation_id,
                "bytecodeHash": bytecode_hash,
                "metadataUri": metadata_uri,
                "parameters": parameters.tolist(),
                "proofHash": proof_data["proofHash"],
                "timestamp": proof_data["timestamp"],
                "transactionHash": receipt["transactionHash"].hex()
            }
            
            logger.info(f"Strategy with ZK proof submitted successfully: Generation ID {generation_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error submitting to blockchain: {str(e)}")
            raise
    
    def train_model(self, strategy_ids: List[int]) -> Dict:
        """
        Train the RL model using historical strategy data
        
        Args:
            strategy_ids: List of strategy IDs to use for training
            
        Returns:
            Dict containing training results
        """
        try:
            logger.info(f"Training RL model with {len(strategy_ids)} strategies")
            
            # 1. Collect training data
            states = []
            rewards = []
            
            for strategy_id in strategy_ids:
                # Fetch strategy data
                strategy_data = self.fetch_strategy_data(strategy_id)
                
                # Skip strategies with insufficient executions
                if strategy_data.get("totalExecutions", 0) < 10:
                    continue
                
                # Fetch historical market conditions (simulated)
                market_conditions = {
                    "gasPrice": random.uniform(20, 100),
                    "ethPrice": random.uniform(1500, 3000),
                    "marketVolatility": random.uniform(0.1, 0.5),
                    "liquidityDepth": random.uniform(1000000, 10000000),
                    "blockTime": strategy_data.get("lastExecutionTime", int(time.time()))
                }
                
                # Prepare state
                state = self.prepare_state(strategy_data, market_conditions)
                states.append(state)
                
                # Calculate reward based on strategy performance
                win_rate = strategy_data.get("winRate", 0) / 10000  # Convert to 0-1 scale
                profit = strategy_data.get("totalProfitVerified", 0) / 1e18  # Convert to ETH
                
                # Reward function: combination of win rate and profit
                reward = win_rate * 50 + profit * 50
                rewards.append(reward)
            
            if not states:
                logger.warning("No valid training data found")
                return {"success": False, "message": "No valid training data found"}
            
            # 2. Convert to numpy arrays
            X = np.array(states)
            y = np.array(rewards).reshape(-1, 1)
            
            # 3. Train the model
            history = self.model.fit(
                X, y,
                epochs=50,
                batch_size=min(32, len(X)),
                verbose=0
            )
            
            # 4. Save the model
            model_path = os.path.join(self.config.get("data_dir", "data/zk_rl"), "models", "rl_model.h5")
            self.model.save_weights(model_path)
            
            # 5. Return training results
            result = {
                "success": True,
                "strategies_used": len(states),
                "final_loss": float(history.history["loss"][-1]),
                "initial_loss": float(history.history["loss"][0]),
                "improvement": float(history.history["loss"][0] - history.history["loss"][-1]),
                "model_path": model_path
            }
            
            logger.info(f"Model training completed: Loss improved from {result['initial_loss']:.4f} to {result['final_loss']:.4f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def run(self):
        """Main execution loop"""
        logger.info("Starting ZK-RL Agent V40")
        
        try:
            # 1. Train model with historical data
            strategy_ids = list(range(1, 20))  # Example: use strategies 1-19
            training_result = self.train_model(strategy_ids)
            
            if not training_result.get("success", False):
                logger.warning("Model training failed, using existing model")
            
            # 2. Generate new strategies with ZK proofs
            for base_strategy_id in [5, 10, 15]:  # Example: improve strategies 5, 10, 15
                try:
                    result = self.generate_strategy_with_zk_proof(base_strategy_id)
                    logger.info(f"Generated strategy based on {base_strategy_id}: Generation ID {result['generationId']}")
                except Exception as e:
                    logger.error(f"Error generating strategy for {base_strategy_id}: {str(e)}")
            
            logger.info("ZK-RL Agent execution completed")
            
        except KeyboardInterrupt:
            logger.info("ZK-RL Agent stopped by user")
        except Exception as e:
            logger.error(f"Error in main execution loop: {str(e)}")

def main():
    """Main entry point"""
    load_dotenv()  # Load environment variables
    
    # Initialize and run the agent
    agent = ZKRLAgent("zk_rl_config.yaml")
    agent.run()

if __name__ == "__main__":
    main()