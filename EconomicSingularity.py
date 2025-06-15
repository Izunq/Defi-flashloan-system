import os
import json
import yaml
import time
import logging
import asyncio
from typing import Dict, List, Tuple, Optional, Any, Set
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from CausalityEngine import CausalityEngine
from InterChainCognitiveMesh import InterChainCognitiveMesh

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("economic_singularity.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EconomicSingularity")

class MarketModel:
    """
    Represents a predictive model for a specific market.
    """
    
    def __init__(self, market_address: str, market_name: str):
        """
        Initialize a market model.
        
        Args:
            market_address: Address of the market
            market_name: Name of the market
        """
        self.market_address = market_address
        self.market_name = market_name
        self.model = None
        self.scaler = StandardScaler()
        self.features = []
        self.last_trained = 0
        self.accuracy = 0.0
        self.confidence = 0.0
        self.prediction_horizon = 24  # hours
        self.historical_data = pd.DataFrame()
        self.predictions = []
    
    def train(self, data: pd.DataFrame) -> float:
        """
        Train the market model.
        
        Args:
            data: Training data
            
        Returns:
            float: Model accuracy
        """
        try:
            # Store historical data
            self.historical_data = data
            
            # Extract features and target
            X = data.drop(['price', 'timestamp'], axis=1)
            y = data['price']
            
            # Store feature names
            self.features = X.columns.tolist()
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5)
            self.model.fit(X_scaled, y)
            
            # Calculate accuracy
            self.accuracy = self.model.score(X_scaled, y)
            self.last_trained = time.time()
            
            logger.info(f"Trained model for {self.market_name} with accuracy: {self.accuracy:.4f}")
            return self.accuracy
        
        except Exception as e:
            logger.error(f"Error training model for {self.market_name}: {e}")
            return 0.0
    
    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Make a price prediction.
        
        Args:
            features: Feature values
            
        Returns:
            Tuple[float, float]: (predicted_price, confidence)
        """
        try:
            if self.model is None:
                logger.error(f"Model for {self.market_name} not trained")
                return 0.0, 0.0
            
            # Convert features to DataFrame
            feature_df = pd.DataFrame([features])
            
            # Ensure all required features are present
            for feature in self.features:
                if feature not in feature_df.columns:
                    feature_df[feature] = 0.0
            
            # Select only the features used in training
            feature_df = feature_df[self.features]
            
            # Scale features
            X_scaled = self.scaler.transform(feature_df)
            
            # Make prediction
            predicted_price = self.model.predict(X_scaled)[0]
            
            # Calculate confidence based on historical accuracy
            self.confidence = self.accuracy * 0.8 + 0.2  # Ensure minimum confidence of 0.2
            
            # Store prediction
            self.predictions.append({
                'timestamp': time.time(),
                'predicted_price': predicted_price,
                'confidence': self.confidence,
                'features': features
            })
            
            # Keep only the last 100 predictions
            if len(self.predictions) > 100:
                self.predictions = self.predictions[-100:]
            
            return predicted_price, self.confidence
        
        except Exception as e:
            logger.error(f"Error making prediction for {self.market_name}: {e}")
            return 0.0, 0.0
    
    def evaluate_intervention_impact(self, intervention_size: float, is_injection: bool) -> Dict:
        """
        Evaluate the impact of a potential intervention.
        
        Args:
            intervention_size: Size of the intervention
            is_injection: Whether this is a liquidity injection
            
        Returns:
            Dict: Impact assessment
        """
        try:
            if self.model is None or len(self.historical_data) == 0:
                logger.error(f"Cannot evaluate intervention impact for {self.market_name}: insufficient data")
                return {
                    'success': False,
                    'message': 'Insufficient data'
                }
            
            # Get the latest data point
            latest_data = self.historical_data.iloc[-1].to_dict()
            
            # Create a copy for the intervention scenario
            intervention_data = latest_data.copy()
            
            # Modify liquidity based on intervention
            current_liquidity = intervention_data.get('liquidity', 0)
            if is_injection:
                intervention_data['liquidity'] = current_liquidity + intervention_size
            else:
                intervention_data['liquidity'] = max(0, current_liquidity - intervention_size)
            
            # Make predictions for both scenarios
            current_price, current_confidence = self.predict(latest_data)
            intervention_price, intervention_confidence = self.predict(intervention_data)
            
            # Calculate price impact
            price_impact = (intervention_price - current_price) / current_price * 100
            
            # Determine if the intervention is beneficial
            target_price = latest_data.get('target_price', current_price)
            current_deviation = abs(current_price - target_price) / target_price * 100
            intervention_deviation = abs(intervention_price - target_price) / target_price * 100
            
            is_beneficial = intervention_deviation < current_deviation
            
            return {
                'success': True,
                'current_price': current_price,
                'intervention_price': intervention_price,
                'price_impact': price_impact,
                'current_deviation': current_deviation,
                'intervention_deviation': intervention_deviation,
                'is_beneficial': is_beneficial,
                'confidence': intervention_confidence
            }
        
        except Exception as e:
            logger.error(f"Error evaluating intervention impact for {self.market_name}: {e}")
            return {
                'success': False,
                'message': str(e)
            }

class AssetModel:
    """
    Represents a model for a specific asset.
    """
    
    def __init__(self, token_address: str, symbol: str, asset_type: str):
        """
        Initialize an asset model.
        
        Args:
            token_address: Address of the token
            symbol: Symbol of the token
            asset_type: Type of the asset
        """
        self.token_address = token_address
        self.symbol = symbol
        self.asset_type = asset_type
        self.target_price = 0.0
        self.current_price = 0.0
        self.volatility = 0.0
        self.liquidity = 0.0
        self.volume_24h = 0.0
        self.price_history = []
        self.last_updated = 0
        self.markets = {}  # market_address -> market_data
    
    def update(self, price: float, volatility: float, liquidity: float, volume_24h: float):
        """
        Update asset data.
        
        Args:
            price: Current price
            volatility: Current volatility
            liquidity: Current liquidity
            volume_24h: 24-hour volume
        """
        self.current_price = price
        self.volatility = volatility
        self.liquidity = liquidity
        self.volume_24h = volume_24h
        self.last_updated = time.time()
        
        # Update price history
        self.price_history.append({
            'timestamp': self.last_updated,
            'price': price,
            'volatility': volatility,
            'liquidity': liquidity,
            'volume_24h': volume_24h
        })
        
        # Keep only the last 1000 data points
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-1000:]
    
    def add_market(self, market_address: str, market_name: str, liquidity: float, price: float):
        """
        Add a market for this asset.
        
        Args:
            market_address: Address of the market
            market_name: Name of the market
            liquidity: Liquidity in the market
            price: Price in the market
        """
        self.markets[market_address] = {
            'name': market_name,
            'liquidity': liquidity,
            'price': price,
            'last_updated': time.time()
        }
    
    def update_market(self, market_address: str, liquidity: float, price: float):
        """
        Update market data.
        
        Args:
            market_address: Address of the market
            liquidity: Liquidity in the market
            price: Price in the market
        """
        if market_address in self.markets:
            self.markets[market_address].update({
                'liquidity': liquidity,
                'price': price,
                'last_updated': time.time()
            })
    
    def get_price_deviation(self) -> float:
        """
        Get the deviation from target price.
        
        Returns:
            float: Price deviation percentage
        """
        if self.target_price == 0:
            return 0.0
        
        return (self.current_price - self.target_price) / self.target_price * 100
    
    def get_market_price_spread(self) -> float:
        """
        Get the spread between highest and lowest market prices.
        
        Returns:
            float: Price spread percentage
        """
        if not self.markets:
            return 0.0
        
        prices = [market_data['price'] for market_data in self.markets.values()]
        if not prices:
            return 0.0
        
        min_price = min(prices)
        max_price = max(prices)
        
        if min_price == 0:
            return 0.0
        
        return (max_price - min_price) / min_price * 100
    
    def to_dict(self) -> Dict:
        """
        Convert to dictionary.
        
        Returns:
            Dict: Dictionary representation
        """
        return {
            'token_address': self.token_address,
            'symbol': self.symbol,
            'asset_type': self.asset_type,
            'target_price': self.target_price,
            'current_price': self.current_price,
            'volatility': self.volatility,
            'liquidity': self.liquidity,
            'volume_24h': self.volume_24h,
            'price_deviation': self.get_price_deviation(),
            'market_price_spread': self.get_market_price_spread(),
            'last_updated': self.last_updated,
            'markets': self.markets
        }

class EconomicSingularity:
    """
    The Economic Singularity coordinates market stabilization and liquidity provision
    across the DeFi ecosystem.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Economic Singularity.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path or "economic_singularity_config.yaml")
        self._setup_directories()
        self._init_account()
        self._init_components()
        self._load_contract_abis()
        self._init_web3_connections()
        self.market_models = {}
        self.asset_models = {}
        self.intervention_history = []
        self.running = False
        
        logger.info("Economic Singularity initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from a YAML file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dict: Configuration dictionary
        """
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Default configuration
            return {
                "account": {
                    "private_key": "DISABLED_FOR_SECURITY"  # Use SecureTransactionSigner instead
                },
                "contracts": {
                    "algorithmic_central_bank": os.getenv("ALGORITHMIC_CENTRAL_BANK_ADDRESS", ""),
                    "cognitive_mesh": os.getenv("COGNITIVE_MESH_ADDRESS", "")
                },
                "web3": {
                    "ethereum": {
                        "rpc_url": os.getenv("ETH_RPC_URL", ""),
                        "chain_id": 1
                    },
                    "polygon": {
                        "rpc_url": os.getenv("POLYGON_RPC_URL", ""),
                        "chain_id": 137
                    }
                },
                "paths": {
                    "contract_abis": "./abi",
                    "data_dir": "./economic_data",
                    "models_dir": "./economic_models"
                },
                "monitoring": {
                    "interval_seconds": 60,
                    "market_update_interval": 300,
                    "model_retrain_interval": 86400
                },
                "intervention": {
                    "min_confidence": 0.8,
                    "min_impact_percentage": 1.0,
                    "max_intervention_size": 1000000,
                    "cooldown_seconds": 3600
                }
            }
    
    def _setup_directories(self):
        """
        Create necessary directories if they don't exist.
        """
        for path_key in ["data_dir", "models_dir"]:
            path = self.config["paths"].get(path_key)
            if path and not os.path.exists(path):
                os.makedirs(path)
                logger.info(f"Created directory: {path}")
    
    def _init_account(self):
        """
        Initialize the account.
        """
        try:
            private_key = self.config["account"]["private_key"]
            # SECURITY: Use secure transaction signer instead of private key
try:
    from secure_transaction_signer import SecureTransactionSigner
    self.signer = SecureTransactionSigner()
    self.account = self.signer.get_account()
except ImportError:
    raise RuntimeError("SECURITY ERROR: SecureTransactionSigner not available.")
            logger.info(f"Account initialized: {self.account.address}")
        except Exception as e:
            logger.error(f"Error initializing account: {e}")
            raise
    
    def _init_components(self):
        """
        Initialize required components.
        """
        try:
            # Initialize Causality Engine
            self.causality_engine = CausalityEngine()
            
            # Initialize Cognitive Mesh
            self.cognitive_mesh = InterChainCognitiveMesh()
            
            logger.info("Components initialized")
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def _load_contract_abis(self):
        """
        Load contract ABIs from JSON files.
        """
        self.contract_abis = {}
        abi_dir = self.config["paths"]["contract_abis"]
        
        try:
            for contract_name, address in self.config["contracts"].items():
                abi_path = os.path.join(abi_dir, f"{contract_name.title()}.json")
                if os.path.exists(abi_path):
                    with open(abi_path, 'r') as file:
                        self.contract_abis[contract_name] = json.load(file)
                        logger.info(f"Loaded ABI for {contract_name}")
        except Exception as e:
            logger.error(f"Error loading contract ABIs: {e}")
            raise
    
    def _init_web3_connections(self):
        """
        Initialize Web3 connections.
        """
        self.web3_connections = {}
        
        try:
            for network_name, network_config in self.config["web3"].items():
                rpc_url = network_config["rpc_url"]
                
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                
                if w3.is_connected():
                    self.web3_connections[network_name] = {
                        "w3": w3,
                        "chain_id": network_config["chain_id"],
                        "contracts": {}
                    }
                    
                    logger.info(f"Connected to {network_name}")
                else:
                    logger.error(f"Failed to connect to {network_name}")
        except Exception as e:
            logger.error(f"Error initializing Web3 connections: {e}")
            raise
    
    def _init_contracts(self):
        """
        Initialize contract instances.
        """
        try:
            for network_name, network_data in self.web3_connections.items():
                w3 = network_data["w3"]
                
                for contract_name, contract_address in self.config["contracts"].items():
                    if contract_address and contract_name in self.contract_abis:
                        contract = w3.eth.contract(
                            address=contract_address,
                            abi=self.contract_abis[contract_name]
                        )
                        
                        network_data["contracts"][contract_name] = contract
                        logger.info(f"Initialized contract {contract_name} on {network_name}")
        except Exception as e:
            logger.error(f"Error initializing contracts: {e}")
            raise
    
    async def load_market_data(self):
        """
        Load market data from the blockchain.
        """
        logger.info("Loading market data")
        
        try:
            # Get primary Web3 connection
            primary_network = next(iter(self.web3_connections.values()))
            w3 = primary_network["w3"]
            
            # Get Algorithmic Central Bank contract
            bank_contract = primary_network["contracts"].get("algorithmic_central_bank")
            
            if not bank_contract:
                logger.error("Algorithmic Central Bank contract not initialized")
                return
            
            # Get all registered markets
            market_addresses = await asyncio.to_thread(bank_contract.functions.getAllMarkets().call)
            
            for market_address in market_addresses:
                # Get market info
                market_info = await asyncio.to_thread(
                    bank_contract.functions.getMarketState(market_address).call
                )
                
                market_name = market_info[1]  # name is the second field
                
                # Create market model if it doesn't exist
                if market_address not in self.market_models:
                    self.market_models[market_address] = MarketModel(market_address, market_name)
                    logger.info(f"Created model for market: {market_name}")
            
            # Get all registered assets
            asset_addresses = await asyncio.to_thread(bank_contract.functions.getAllAssets().call)
            
            for asset_address in asset_addresses:
                # Get asset info
                asset_info = await asyncio.to_thread(
                    bank_contract.functions.getAssetInfo(asset_address).call
                )
                
                symbol = asset_info[1]  # symbol is the second field
                asset_type = int(asset_info[2])  # assetType is the third field
                target_price = asset_info[3]  # targetPrice is the fourth field
                
                # Create asset model if it doesn't exist
                if asset_address not in self.asset_models:
                    self.asset_models[asset_address] = AssetModel(
                        asset_address,
                        symbol,
                        self._asset_type_to_string(asset_type)
                    )
                    self.asset_models[asset_address].target_price = target_price / 1e18
                    logger.info(f"Created model for asset: {symbol}")
            
            logger.info(f"Loaded {len(self.market_models)} markets and {len(self.asset_models)} assets")
        
        except Exception as e:
            logger.error(f"Error loading market data: {e}")
    
    def _asset_type_to_string(self, asset_type: int) -> str:
        """
        Convert asset type enum to string.
        
        Args:
            asset_type: Asset type enum value
            
        Returns:
            str: Asset type string
        """
        asset_types = [
            "Stablecoin",
            "GovernanceToken",
            "LiquidityToken",
            "DebtToken",
            "Other"
        ]
        
        if 0 <= asset_type < len(asset_types):
            return asset_types[asset_type]
        else:
            return "Unknown"
    
    async def update_market_data(self):
        """
        Update market data from external sources.
        """
        logger.info("Updating market data")
        
        try:
            # In a real implementation, this would fetch data from various sources
            # For this example, we'll simulate data updates
            
            for market_address, market_model in self.market_models.items():
                # Simulate market data
                market_data = self._simulate_market_data(market_model.market_name)
                
                # Create DataFrame for training
                if not hasattr(market_model, 'training_data') or market_model.training_data is None:
                    market_model.training_data = pd.DataFrame()
                
                # Add new data point
                market_model.training_data = pd.concat([
                    market_model.training_data,
                    pd.DataFrame([market_data])
                ])
                
                # Update asset models with market data
                for asset_address in market_data.get('assets', {}):
                    if asset_address in self.asset_models:
                        asset_data = market_data['assets'][asset_address]
                        self.asset_models[asset_address].update(
                            price=asset_data['price'],
                            volatility=asset_data['volatility'],
                            liquidity=asset_data['liquidity'],
                            volume_24h=asset_data['volume_24h']
                        )
                        
                        self.asset_models[asset_address].update_market(
                            market_address,
                            asset_data['liquidity'],
                            asset_data['price']
                        )
            
            logger.info("Market data updated")
        
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
    
    def _simulate_market_data(self, market_name: str) -> Dict:
        """
        Simulate market data for testing.
        
        Args:
            market_name: Name of the market
            
        Returns:
            Dict: Simulated market data
        """
        # This is a placeholder for real market data
        # In a real implementation, this would fetch data from APIs or blockchain
        
        base_price = 100.0
        if "ETH" in market_name:
            base_price = 2000.0
        elif "BTC" in market_name:
            base_price = 30000.0
        elif "USDC" in market_name or "USDT" in market_name or "DAI" in market_name:
            base_price = 1.0
        
        # Add some randomness
        price_change = np.random.normal(0, 0.02)  # 2% standard deviation
        price = base_price * (1 + price_change)
        
        # Simulate volatility
        volatility = abs(price_change) * 100
        
        # Simulate liquidity
        liquidity = np.random.uniform(1000000, 10000000)
        
        # Simulate volume
        volume = np.random.uniform(500000, 5000000)
        
        # Create asset data
        assets = {}
        asset_symbols = ["ETH", "USDC", "WBTC", "DAI"]
        
        for symbol in asset_symbols:
            asset_price = 1.0
            if symbol == "ETH":
                asset_price = 2000.0 * (1 + np.random.normal(0, 0.02))
            elif symbol == "WBTC":
                asset_price = 30000.0 * (1 + np.random.normal(0, 0.02))
            
            assets[f"0x{symbol.lower()}{'0' * 34}"] = {
                'symbol': symbol,
                'price': asset_price,
                'volatility': abs(np.random.normal(0, 0.02)) * 100,
                'liquidity': np.random.uniform(500000, 5000000),
                'volume_24h': np.random.uniform(250000, 2500000)
            }
        
        return {
            'timestamp': time.time(),
            'price': price,
            'volatility': volatility,
            'liquidity': liquidity,
            'volume_24h': volume,
            'assets': assets,
            'target_price': base_price
        }
    
    async def train_models(self):
        """
        Train market models.
        """
        logger.info("Training market models")
        
        try:
            for market_address, market_model in self.market_models.items():
                # Check if we have enough data and if it's time to retrain
                if (hasattr(market_model, 'training_data') and 
                    len(market_model.training_data) >= 100 and
                    (time.time() - market_model.last_trained) > self.config["monitoring"]["model_retrain_interval"]):
                    
                    # Train the model
                    accuracy = market_model.train(market_model.training_data)
                    logger.info(f"Trained model for {market_model.market_name} with accuracy: {accuracy:.4f}")
                    
                    # Save the model
                    self._save_model(market_model)
            
            logger.info("Model training completed")
        
        except Exception as e:
            logger.error(f"Error training models: {e}")
    
    def _save_model(self, market_model: MarketModel):
        """
        Save a market model to disk.
        
        Args:
            market_model: Market model to save
        """
        try:
            models_dir = self.config["paths"]["models_dir"]
            model_path = os.path.join(models_dir, f"{market_model.market_address}.joblib")
            
            # In a real implementation, this would save the model using joblib or pickle
            # For this example, we'll just log it
            logger.info(f"Saved model for {market_model.market_name} to {model_path}")
        
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    async def analyze_market_conditions(self):
        """
        Analyze current market conditions.
        """
        logger.info("Analyzing market conditions")
        
        try:
            # Get causal relationships from the Causality Engine
            causal_relationships = self.causality_engine.analyze_causal_relationships(lookback_days=30)
            
            # Generate event probabilities
            event_probabilities = self.causality_engine.generate_event_probabilities()
            
            # Analyze market conditions
            market_conditions = {
                'timestamp': time.time(),
                'causal_relationships': causal_relationships,
                'event_probabilities': event_probabilities,
                'markets': {},
                'assets': {},
                'intervention_recommendations': []
            }
            
            # Analyze each market
            for market_address, market_model in self.market_models.items():
                if not hasattr(market_model, 'training_data') or market_model.training_data is None:
                    continue
                
                # Get the latest data point
                if len(market_model.training_data) > 0:
                    latest_data = market_model.training_data.iloc[-1].to_dict()
                    
                    # Make prediction
                    predicted_price, confidence = market_model.predict(latest_data)
                    
                    market_conditions['markets'][market_address] = {
                        'name': market_model.market_name,
                        'current_price': latest_data.get('price', 0),
                        'predicted_price': predicted_price,
                        'confidence': confidence,
                        'volatility': latest_data.get('volatility', 0),
                        'liquidity': latest_data.get('liquidity', 0),
                        'volume_24h': latest_data.get('volume_24h', 0)
                    }
            
            # Analyze each asset
            for asset_address, asset_model in self.asset_models.items():
                market_conditions['assets'][asset_address] = asset_model.to_dict()
            
            # Identify potential interventions
            intervention_recommendations = self._identify_potential_interventions(market_conditions)
            market_conditions['intervention_recommendations'] = intervention_recommendations
            
            # Save market conditions
            self._save_market_conditions(market_conditions)
            
            # Update global state in the cognitive mesh
            await self._update_global_state(market_conditions)
            
            logger.info(f"Market analysis completed with {len(intervention_recommendations)} intervention recommendations")
            
            return market_conditions
        
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return None
    
    def _identify_potential_interventions(self, market_conditions: Dict) -> List[Dict]:
        """
        Identify potential market interventions.
        
        Args:
            market_conditions: Current market conditions
            
        Returns:
            List[Dict]: List of potential interventions
        """
        interventions = []
        
        try:
            # Check each asset for potential interventions
            for asset_address, asset_data in market_conditions['assets'].items():
                asset_model = self.asset_models.get(asset_address)
                if not asset_model:
                    continue
                
                # Check if price is deviating from target
                price_deviation = asset_data['price_deviation']
                
                if abs(price_deviation) >= 1.0:  # 1% deviation threshold
                    # Determine intervention type
                    is_injection = price_deviation < 0  # Price below target, inject liquidity
                    
                    # Find the market with the highest deviation
                    target_market = None
                    max_deviation = 0
                    
                    for market_address, market_data in asset_model.markets.items():
                        if market_address in self.market_models:
                            market_price = market_data['price']
                            market_deviation = abs((market_price - asset_model.target_price) / asset_model.target_price * 100)
                            
                            if market_deviation > max_deviation:
                                max_deviation = market_deviation
                                target_market = market_address
                    
                    if target_market:
                        # Calculate intervention size
                        market_liquidity = asset_model.markets[target_market]['liquidity']
                        intervention_size = market_liquidity * 0.05  # 5% of current liquidity
                        
                        # Cap intervention size
                        max_size = self.config["intervention"]["max_intervention_size"]
                        intervention_size = min(intervention_size, max_size)
                        
                        # Evaluate impact
                        market_model = self.market_models[target_market]
                        impact = market_model.evaluate_intervention_impact(intervention_size, is_injection)
                        
                        if impact.get('success', False) and impact.get('is_beneficial', False):
                            # Check confidence
                            if impact.get('confidence', 0) >= self.config["intervention"]["min_confidence"]:
                                # Check impact size
                                if abs(impact.get('price_impact', 0)) >= self.config["intervention"]["min_impact_percentage"]:
                                    # Create intervention recommendation
                                    interventions.append({
                                        'asset_address': asset_address,
                                        'asset_symbol': asset_model.symbol,
                                        'market_address': target_market,
                                        'market_name': self.market_models[target_market].market_name,
                                        'intervention_size': intervention_size,
                                        'is_injection': is_injection,
                                        'current_price': impact['current_price'],
                                        'predicted_price': impact['intervention_price'],
                                        'price_impact': impact['price_impact'],
                                        'confidence': impact['confidence'],
                                        'reason': f"Price deviation of {price_deviation:.2f}% from target"
                                    })
            
            # Sort interventions by confidence and impact
            interventions.sort(key=lambda x: (x['confidence'], abs(x['price_impact'])), reverse=True)
            
            return interventions
        
        except Exception as e:
            logger.error(f"Error identifying potential interventions: {e}")
            return []
    
    def _save_market_conditions(self, market_conditions: Dict):
        """
        Save market conditions to disk.
        
        Args:
            market_conditions: Market conditions to save
        """
        try:
            data_dir = self.config["paths"]["data_dir"]
            file_path = os.path.join(data_dir, f"market_conditions_{int(time.time())}.json")
            
            with open(file_path, 'w') as file:
                json.dump(market_conditions, file, indent=2)
            
            logger.info(f"Saved market conditions to {file_path}")
        
        except Exception as e:
            logger.error(f"Error saving market conditions: {e}")
    
    async def _update_global_state(self, market_conditions: Dict):
        """
        Update global state in the cognitive mesh.
        
        Args:
            market_conditions: Current market conditions
        """
        try:
            # Create a simplified state update
            state_update = {
                'timestamp': market_conditions['timestamp'],
                'markets': {
                    market_address: {
                        'name': market_data['name'],
                        'price': market_data['current_price'],
                        'predicted_price': market_data['predicted_price'],
                        'confidence': market_data['confidence']
                    }
                    for market_address, market_data in market_conditions['markets'].items()
                },
                'assets': {
                    asset_address: {
                        'symbol': asset_data['symbol'],
                        'price': asset_data['current_price'],
                        'target_price': asset_data['target_price'],
                        'deviation': asset_data['price_deviation']
                    }
                    for asset_address, asset_data in market_conditions['assets'].items()
                },
                'interventions': market_conditions['intervention_recommendations']
            }
            
            # Update global state in the cognitive mesh
            state_key = "economic_singularity_state"
            await self.cognitive_mesh.update_global_state(state_key, json.dumps(state_update))
            
            logger.info("Updated global state in cognitive mesh")
        
        except Exception as e:
            logger.error(f"Error updating global state: {e}")
    
    async def execute_interventions(self, interventions: List[Dict]):
        """
        Execute market interventions.
        
        Args:
            interventions: List of interventions to execute
        """
        logger.info(f"Executing {len(interventions)} interventions")
        
        try:
            # Get primary Web3 connection
            primary_network = next(iter(self.web3_connections.values()))
            w3 = primary_network["w3"]
            
            # Get Algorithmic Central Bank contract
            bank_contract = primary_network["contracts"].get("algorithmic_central_bank")
            
            if not bank_contract:
                logger.error("Algorithmic Central Bank contract not initialized")
                return
            
            # Check cooldown period
            if self.intervention_history:
                last_intervention_time = self.intervention_history[-1]['timestamp']
                cooldown = self.config["intervention"]["cooldown_seconds"]
                
                if time.time() - last_intervention_time < cooldown:
                    logger.info(f"Intervention cooldown period active, skipping execution")
                    return
            
            # Execute each intervention
            for intervention in interventions:
                # Build transaction
                tx = bank_contract.functions.executeIntervention(
                    intervention['market_address'],
                    intervention['asset_address'],
                    int(intervention['intervention_size']),
                    int(intervention['current_price'] * 1e18),  # Convert to wei
                    intervention['is_injection'],
                    intervention['reason']
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': w3.eth.get_transaction_count(self.account.address),
                    'gas': 500000,
                    'gasPrice': w3.eth.gas_price
                })
                
                # Sign transaction
                signed_tx = self.account.sign_transaction(tx)
                
                # Send transaction
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                
                # Wait for receipt
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    logger.info(f"Intervention executed successfully: {tx_hash.hex()}")
                    
                    # Record intervention
                    intervention['timestamp'] = time.time()
                    intervention['tx_hash'] = tx_hash.hex()
                    intervention['status'] = 'success'
                    
                    self.intervention_history.append(intervention)
                else:
                    logger.error(f"Intervention execution failed: {tx_hash.hex()}")
                    
                    # Record failed intervention
                    intervention['timestamp'] = time.time()
                    intervention['tx_hash'] = tx_hash.hex()
                    intervention['status'] = 'failed'
                    
                    self.intervention_history.append(intervention)
            
            # Save intervention history
            self._save_intervention_history()
            
            logger.info("Intervention execution completed")
        
        except Exception as e:
            logger.error(f"Error executing interventions: {e}")
    
    def _save_intervention_history(self):
        """
        Save intervention history to disk.
        """
        try:
            data_dir = self.config["paths"]["data_dir"]
            file_path = os.path.join(data_dir, "intervention_history.json")
            
            with open(file_path, 'w') as file:
                json.dump(self.intervention_history, file, indent=2)
            
            logger.info(f"Saved intervention history to {file_path}")
        
        except Exception as e:
            logger.error(f"Error saving intervention history: {e}")
    
    async def run(self):
        """
        Run the Economic Singularity.
        """
        logger.info("Starting Economic Singularity")
        
        self.running = True
        
        # Initialize contracts
        self._init_contracts()
        
        # Load initial market data
        await self.load_market_data()
        
        # Main loop
        while self.running:
            try:
                # Update market data
                await self.update_market_data()
                
                # Train models
                await self.train_models()
                
                # Analyze market conditions
                market_conditions = await self.analyze_market_conditions()
                
                if market_conditions:
                    # Execute interventions
                    await self.execute_interventions(market_conditions['intervention_recommendations'])
                
                # Sleep
                await asyncio.sleep(self.config["monitoring"]["interval_seconds"])
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)
        
        logger.info("Economic Singularity stopped")
    
    def stop(self):
        """
        Stop the Economic Singularity.
        """
        logger.info("Stopping Economic Singularity")
        self.running = False

async def main():
    """
    Main function to run the Economic Singularity.
    """
    try:
        singularity = EconomicSingularity()
        await singularity.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())