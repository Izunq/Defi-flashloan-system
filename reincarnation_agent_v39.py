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
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("reincarnation_agent_v39.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ReincarnationAgent")

class ReincarnationAgent:
    """
    RL-based agent that monitors failed strategies and attempts to reincarnate them
    with improved parameters using reinforcement learning techniques.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Reincarnation Agent
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path or "reincarnation_config.yaml"
        self._load_config(self.config_path)
        self._setup_directories()
        self._init_web3()
        self._init_contracts()
        self._init_rl_model()
        
        # Initialize memory for experience replay
        self.memory = deque(maxlen=self.config.get("memory_size", 10000))
        
        # Track reincarnated strategies
        self.reincarnated_strategies = {}
        
        logger.info(f"Reincarnation Agent V39 initialized")
    
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
                    "strategy_generator_address": "",
                    "trust_curve_address": "",
                    "strategy_incubator_address": ""
                },
                "rl_params": {
                    "learning_rate": 0.001,
                    "gamma": 0.95,
                    "epsilon": 1.0,
                    "epsilon_decay": 0.995,
                    "epsilon_min": 0.01,
                    "batch_size": 32
                },
                "monitoring": {
                    "poll_interval": 60,
                    "min_executions_before_reincarnation": 10,
                    "max_reincarnation_attempts": 5
                },
                "data_dir": "data/reincarnation"
            }
            return self.config
    
    def _setup_directories(self):
        """Create necessary directories for data storage"""
        os.makedirs(self.config.get("data_dir", "data/reincarnation"), exist_ok=True)
        os.makedirs(os.path.join(self.config.get("data_dir", "data/reincarnation"), "models"), exist_ok=True)
        os.makedirs(os.path.join(self.config.get("data_dir", "data/reincarnation"), "history"), exist_ok=True)
    
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
            with open("abi/StrategyGeneratorV37.json", "r") as f:
                strategy_generator_abi = json.load(f)
            
            with open("abi/TrustCurve.json", "r") as f:
                trust_curve_abi = json.load(f)
            
            with open("abi/StrategyIncubatorV33.json", "r") as f:
                strategy_incubator_abi = json.load(f)
            
            # Initialize contract instances
            self.strategy_generator = self.w3.eth.contract(
                address=contracts_config.get("strategy_generator_address"),
                abi=strategy_generator_abi
            )
            
            self.trust_curve = self.w3.eth.contract(
                address=contracts_config.get("trust_curve_address"),
                abi=trust_curve_abi
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
        """Initialize the Reinforcement Learning model (Deep Q-Network)"""
        try:
            # Get RL parameters from config
            rl_params = self.config.get("rl_params", {})
            self.learning_rate = rl_params.get("learning_rate", 0.001)
            self.gamma = rl_params.get("gamma", 0.95)  # discount factor
            self.epsilon = rl_params.get("epsilon", 1.0)  # exploration rate
            self.epsilon_decay = rl_params.get("epsilon_decay", 0.995)
            self.epsilon_min = rl_params.get("epsilon_min", 0.01)
            self.batch_size = rl_params.get("batch_size", 32)
            
            # Define state and action dimensions
            self.state_dim = 10  # Market conditions + strategy parameters
            self.action_dim = 5  # Number of parameters to adjust
            
            # Create Deep Q-Network model
            self.model = self._build_dqn_model()
            self.target_model = self._build_dqn_model()
            self.update_target_model()
            
            logger.info("RL model initialized")
            
        except Exception as e:
            logger.error(f"Error initializing RL model: {str(e)}")
            raise
    
    def _build_dqn_model(self):
        """Build a Deep Q-Network model"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(self.state_dim,)),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(self.action_dim)
        ])
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse'
        )
        return model
    
    def update_target_model(self):
        """Update target model weights with current model weights"""
        self.target_model.set_weights(self.model.get_weights())
    
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
    
    def monitor_slashed_strategies(self):
        """
        Monitor for slashed/failed strategies and trigger reincarnation process
        """
        try:
            # Get the latest block number
            latest_block = self.w3.eth.block_number
            
            # Define the event filter for StrategySlashed events
            # Note: In a real implementation, you would need to create a specific event for this
            # or use a combination of events to detect failed strategies
            strategy_slashed_filter = self.strategy_incubator.events.StrategySlashed.createFilter(
                fromBlock=latest_block - 1000,  # Look back 1000 blocks
                toBlock='latest'
            )
            
            # Get events
            events = strategy_slashed_filter.get_all_entries()
            
            for event in events:
                strategy_id = event.args.strategyId
                
                # Check if we've already tried to reincarnate this strategy
                if strategy_id in self.reincarnated_strategies:
                    attempts = self.reincarnated_strategies[strategy_id]
                    max_attempts = self.config.get("monitoring", {}).get("max_reincarnation_attempts", 5)
                    
                    if attempts >= max_attempts:
                        logger.info(f"Strategy {strategy_id} has reached maximum reincarnation attempts ({max_attempts})")
                        continue
                
                logger.info(f"Detected slashed strategy: {strategy_id}")
                
                # Get strategy data
                strategy_data = self.fetch_strategy_data(strategy_id)
                
                # Check if the strategy has enough executions to learn from
                min_executions = self.config.get("monitoring", {}).get("min_executions_before_reincarnation", 10)
                if strategy_data.get("totalExecutions", 0) < min_executions:
                    logger.info(f"Strategy {strategy_id} has insufficient executions ({strategy_data.get('totalExecutions', 0)}/{min_executions})")
                    continue
                
                # Reincarnate the strategy
                self.reincarnate_strategy(strategy_id, strategy_data)
                
        except Exception as e:
            logger.error(f"Error monitoring slashed strategies: {str(e)}")
    
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
    
    def fetch_market_conditions(self, strategy_id: int) -> Dict:
        """
        Fetch market conditions at the time of strategy failure
        
        Args:
            strategy_id: ID of the failed strategy
            
        Returns:
            Dict containing market conditions
        """
        # In a real implementation, this would fetch historical market data
        # from an oracle or other data source
        
        # Mock implementation
        return {
            "gasPrice": self.w3.eth.gas_price,
            "blockNumber": self.w3.eth.block_number,
            "timestamp": self.w3.eth.get_block('latest').timestamp,
            "ethPrice": 2000 + random.uniform(-100, 100),
            "marketVolatility": random.uniform(0.1, 0.5),
            "liquidityDepth": random.uniform(1000000, 10000000)
        }
    
    def fetch_strategy_parameters(self, strategy_address: str) -> Dict:
        """
        Fetch the current parameters of a strategy
        
        Args:
            strategy_address: Address of the strategy contract
            
        Returns:
            Dict containing strategy parameters
        """
        try:
            # In a real implementation, this would call specific functions
            # on the strategy contract to get its parameters
            
            # Mock implementation
            return {
                "riskLevel": random.randint(1, 10),
                "minProfitThreshold": random.randint(5, 50),
                "maxSlippage": random.randint(10, 100),
                "executionTimeLimit": random.randint(30, 300),
                "gasLimitMultiplier": random.uniform(1.0, 2.0)
            }
            
        except Exception as e:
            logger.error(f"Error fetching strategy parameters for {strategy_address}: {str(e)}")
            return {}
    
    def prepare_state(self, strategy_data: Dict, market_conditions: Dict, strategy_params: Dict) -> np.ndarray:
        """
        Prepare the state vector for the RL model
        
        Args:
            strategy_data: Strategy data
            market_conditions: Market conditions
            strategy_params: Strategy parameters
            
        Returns:
            State vector as numpy array
        """
        # Normalize values to appropriate ranges
        state = np.array([
            strategy_data.get("winRate", 0) / 10000,  # Win rate (0-1)
            strategy_data.get("totalExecutions", 0) / 1000,  # Executions (normalized)
            strategy_data.get("failedExecutions", 0) / strategy_data.get("totalExecutions", 1),  # Failure rate
            market_conditions.get("gasPrice", 0) / 1e9,  # Gas price in Gwei
            market_conditions.get("marketVolatility", 0),  # Volatility (0-1)
            market_conditions.get("liquidityDepth", 0) / 1e7,  # Liquidity (normalized)
            strategy_params.get("riskLevel", 5) / 10,  # Risk level (0-1)
            strategy_params.get("minProfitThreshold", 20) / 100,  # Min profit (0-1)
            strategy_params.get("maxSlippage", 50) / 100,  # Max slippage (0-1)
            strategy_params.get("gasLimitMultiplier", 1.5) / 2.0  # Gas multiplier (0-1)
        ])
        
        return state
    
    def get_action(self, state: np.ndarray) -> np.ndarray:
        """
        Get action from the RL model using epsilon-greedy policy
        
        Args:
            state: Current state vector
            
        Returns:
            Action vector
        """
        if np.random.rand() <= self.epsilon:
            # Exploration: random action
            return np.random.uniform(-1, 1, self.action_dim)
        else:
            # Exploitation: predict action from model
            q_values = self.model.predict(state.reshape(1, -1), verbose=0)
            return np.array([
                np.clip(q_values[0][0], -1, 1),  # Risk level adjustment
                np.clip(q_values[0][1], -1, 1),  # Min profit adjustment
                np.clip(q_values[0][2], -1, 1),  # Max slippage adjustment
                np.clip(q_values[0][3], -1, 1),  # Execution time adjustment
                np.clip(q_values[0][4], -1, 1)   # Gas multiplier adjustment
            ])
    
    def apply_action_to_parameters(self, params: Dict, action: np.ndarray) -> Dict:
        """
        Apply the RL action to modify strategy parameters
        
        Args:
            params: Current strategy parameters
            action: Action vector from RL model
            
        Returns:
            Updated strategy parameters
        """
        # Clone the parameters
        new_params = params.copy()
        
        # Apply adjustments based on action values (-1 to 1 range)
        new_params["riskLevel"] = max(1, min(10, params["riskLevel"] + int(action[0] * 3)))
        new_params["minProfitThreshold"] = max(5, min(50, params["minProfitThreshold"] + int(action[1] * 10)))
        new_params["maxSlippage"] = max(10, min(100, params["maxSlippage"] + int(action[2] * 20)))
        new_params["executionTimeLimit"] = max(30, min(300, params["executionTimeLimit"] + int(action[3] * 50)))
        new_params["gasLimitMultiplier"] = max(1.0, min(2.0, params["gasLimitMultiplier"] + action[4] * 0.2))
        
        return new_params
    
    def reincarnate_strategy(self, strategy_id: int, strategy_data: Dict):
        """
        Reincarnate a failed strategy with improved parameters
        
        Args:
            strategy_id: ID of the failed strategy
            strategy_data: Data about the failed strategy
        """
        try:
            logger.info(f"Attempting to reincarnate strategy {strategy_id}")
            
            # Fetch market conditions at failure time
            market_conditions = self.fetch_market_conditions(strategy_id)
            
            # Fetch current strategy parameters
            strategy_params = self.fetch_strategy_parameters(strategy_data["strategyAddress"])
            
            # Prepare state for RL model
            state = self.prepare_state(strategy_data, market_conditions, strategy_params)
            
            # Get action from RL model
            action = self.get_action(state)
            
            # Apply action to modify parameters
            new_params = self.apply_action_to_parameters(strategy_params, action)
            
            logger.info(f"Original parameters: {strategy_params}")
            logger.info(f"New parameters: {new_params}")
            
            # Call reincarnate function on StrategyGeneratorV37 contract
            tx = self.strategy_generator.functions.reincarnate(
                strategy_id
            ).build_transaction({
                'from': self.w3.eth.default_account,
                'gas': self.config.get("web3", {}).get("gas_limit", 3000000),
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.w3.eth.default_account)
            })
            
            # Send transaction
            receipt = self._send_transaction(tx)
            
            # Track reincarnation attempt
            if strategy_id in self.reincarnated_strategies:
                self.reincarnated_strategies[strategy_id] += 1
            else:
                self.reincarnated_strategies[strategy_id] = 1
            
            # Store the experience for training
            # In a real implementation, we would wait for the outcome of the reincarnated strategy
            # and then calculate the reward based on its performance
            
            logger.info(f"Strategy {strategy_id} reincarnated successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error reincarnating strategy {strategy_id}: {str(e)}")
            return False
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in memory for replay"""
        self.memory.append((state, action, reward, next_state, done))
    
    def replay(self):
        """Train the model using experience replay"""
        if len(self.memory) < self.batch_size:
            return
        
        # Sample random minibatch from memory
        minibatch = random.sample(self.memory, self.batch_size)
        
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = reward + self.gamma * np.amax(
                    self.target_model.predict(next_state.reshape(1, -1), verbose=0)[0]
                )
            
            target_f = self.model.predict(state.reshape(1, -1), verbose=0)
            for i in range(self.action_dim):
                # Update Q-value for the action taken
                target_f[0][i] = target
            
            # Train the model
            self.model.fit(state.reshape(1, -1), target_f, epochs=1, verbose=0)
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def save_model(self):
        """Save the RL model"""
        model_path = os.path.join(self.config.get("data_dir", "data/reincarnation"), "models", "dqn_model.h5")
        self.model.save(model_path)
        logger.info(f"Model saved to {model_path}")
    
    def load_model(self):
        """Load the RL model"""
        model_path = os.path.join(self.config.get("data_dir", "data/reincarnation"), "models", "dqn_model.h5")
        if os.path.exists(model_path):
            self.model = tf.keras.models.load_model(model_path)
            self.update_target_model()
            logger.info(f"Model loaded from {model_path}")
    
    def run(self):
        """Main execution loop"""
        logger.info("Starting Reincarnation Agent V39")
        
        try:
            # Load model if exists
            self.load_model()
            
            while True:
                # Monitor for slashed strategies
                self.monitor_slashed_strategies()
                
                # Train model with collected experiences
                self.replay()
                
                # Update target model periodically
                if random.random() < 0.1:  # 10% chance each cycle
                    self.update_target_model()
                    logger.info("Target model updated")
                
                # Save model periodically
                if random.random() < 0.05:  # 5% chance each cycle
                    self.save_model()
                
                # Sleep before next cycle
                poll_interval = self.config.get("monitoring", {}).get("poll_interval", 60)
                logger.info(f"Sleeping for {poll_interval} seconds")
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            logger.info("Reincarnation Agent stopped by user")
            self.save_model()
        except Exception as e:
            logger.error(f"Error in main execution loop: {str(e)}")
            self.save_model()

def main():
    """Main entry point"""
    load_dotenv()  # Load environment variables
    
    # Initialize and run the agent
    agent = ReincarnationAgent("reincarnation_config.yaml")
    agent.run()

if __name__ == "__main__":
    main()