import os
import json
import yaml
import time
import logging
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
import numpy as np
import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import solcx
from solcx import compile_source, install_solc
from CausalityEngine import CausalityEngine
from StrategySynthesizer import StrategySynthesizer
from WorldModelSimulator import WorldModelSimulator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("protocol_synthesizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ProtocolSynthesizer")

class ProtocolSynthesizer:
    """
    The Protocol Synthesizer is responsible for identifying market inefficiencies,
    designing new DeFi protocols to address them, and deploying these protocols
    through the ProtocolGenesisEngine.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Protocol Synthesizer.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path or "protocol_synthesizer_config.yaml")
        self._setup_directories()
        self._init_web3()
        self._init_components()
        self._load_contract_abis()
        self._load_protocol_templates()
        
        logger.info("Protocol Synthesizer initialized")
    
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
                "web3": {
                    "provider_url": os.getenv("WEB3_PROVIDER_URL", "http://localhost:8545"),
                    "chain_id": int(os.getenv("CHAIN_ID", "1")),
                    "private_key": "DISABLED_FOR_SECURITY"  # Use SecureTransactionSigner instead
                },
                "contracts": {
                    "protocol_genesis_engine": os.getenv("PROTOCOL_GENESIS_ENGINE_ADDRESS", ""),
                    "treasury": os.getenv("TREASURY_ADDRESS", "")
                },
                "paths": {
                    "contract_templates": "./protocol_templates",
                    "contract_abis": "./abi",
                    "output_dir": "./protocol_output",
                    "simulation_results": "./protocol_simulation_results"
                },
                "analysis": {
                    "inefficiency_threshold": 0.7,  # Minimum score to consider a market inefficiency
                    "max_protocols_per_run": 1
                },
                "simulation": {
                    "num_simulations": 1000,
                    "simulation_duration_days": 90
                },
                "protocol_types": [
                    "DEX",
                    "LendingProtocol",
                    "Derivatives",
                    "Yield",
                    "Insurance",
                    "Stablecoin",
                    "AssetManagement"
                ]
            }
    
    def _setup_directories(self):
        """
        Create necessary directories if they don't exist.
        """
        for path_key in ["contract_templates", "output_dir", "simulation_results"]:
            path = self.config["paths"].get(path_key)
            if path and not os.path.exists(path):
                os.makedirs(path)
                logger.info(f"Created directory: {path}")
    
    def _init_web3(self):
        """
        Initialize Web3 connection and account.
        """
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.config["web3"]["provider_url"]))
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if not self.w3.is_connected():
                logger.error("Failed to connect to Web3 provider")
                raise ConnectionError("Failed to connect to Web3 provider")
            
            # Set up account
            private_key = self.config["web3"]["private_key"]
            # SECURITY: Use secure transaction signer instead of private key
try:
    from secure_transaction_signer import SecureTransactionSigner
    self.signer = SecureTransactionSigner()
    self.account = self.signer.get_account()
except ImportError:
    raise RuntimeError("SECURITY ERROR: SecureTransactionSigner not available.")
            logger.info(f"Connected to Web3 provider, account: {self.account.address}")
        except Exception as e:
            logger.error(f"Error initializing Web3: {e}")
            raise
    
    def _init_components(self):
        """
        Initialize required components.
        """
        try:
            # Initialize Causality Engine for market inefficiency analysis
            self.causality_engine = CausalityEngine()
            
            # Initialize Strategy Synthesizer for protocol design
            self.strategy_synthesizer = StrategySynthesizer()
            
            # Initialize World Model Simulator for protocol testing
            self.world_model = WorldModelSimulator()
            
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
    
    def _load_protocol_templates(self):
        """
        Load protocol templates from the templates directory.
        """
        self.protocol_templates = {}
        templates_dir = self.config["paths"]["contract_templates"]
        
        try:
            if os.path.exists(templates_dir):
                for file_name in os.listdir(templates_dir):
                    if file_name.endswith(".sol"):
                        template_name = file_name.replace(".sol", "")
                        template_path = os.path.join(templates_dir, file_name)
                        
                        with open(template_path, 'r') as file:
                            self.protocol_templates[template_name] = file.read()
                            logger.info(f"Loaded protocol template: {template_name}")
        except Exception as e:
            logger.error(f"Error loading protocol templates: {e}")
            raise
    
    def identify_market_inefficiencies(self) -> List[Dict]:
        """
        Identify market inefficiencies using the Causality Engine.
        
        Returns:
            List[Dict]: List of identified market inefficiencies
        """
        logger.info("Identifying market inefficiencies")
        
        try:
            # Get causal relationships from the Causality Engine
            causal_relationships = self.causality_engine.analyze_causal_relationships(lookback_days=60)
            
            # Generate event probabilities
            event_probabilities = self.causality_engine.generate_event_probabilities()
            
            # Identify inefficiencies based on causal relationships and event probabilities
            inefficiencies = []
            
            # Example inefficiency identification logic
            # In a real implementation, this would be much more sophisticated
            
            # Check for DEX inefficiencies
            if "price_impact" in causal_relationships and causal_relationships["price_impact"]["strength"] > 0.7:
                inefficiencies.append({
                    "type": "DEX",
                    "name": "High Price Impact",
                    "description": "Current DEXs have high price impact for large trades",
                    "score": causal_relationships["price_impact"]["strength"],
                    "opportunity": "Create a DEX with concentrated liquidity and reduced price impact"
                })
            
            # Check for lending protocol inefficiencies
            if "interest_rate_volatility" in causal_relationships and causal_relationships["interest_rate_volatility"]["strength"] > 0.6:
                inefficiencies.append({
                    "type": "LendingProtocol",
                    "name": "Interest Rate Volatility",
                    "description": "Current lending protocols have highly volatile interest rates",
                    "score": causal_relationships["interest_rate_volatility"]["strength"],
                    "opportunity": "Create a lending protocol with stable, predictable interest rates"
                })
            
            # Check for derivatives inefficiencies
            if "oracle_manipulation" in causal_relationships and causal_relationships["oracle_manipulation"]["strength"] > 0.5:
                inefficiencies.append({
                    "type": "Derivatives",
                    "name": "Oracle Manipulation",
                    "description": "Current derivatives protocols are vulnerable to oracle manipulation",
                    "score": causal_relationships["oracle_manipulation"]["strength"],
                    "opportunity": "Create a derivatives protocol with robust, manipulation-resistant oracles"
                })
            
            # Filter inefficiencies by threshold
            threshold = self.config["analysis"]["inefficiency_threshold"]
            inefficiencies = [i for i in inefficiencies if i["score"] >= threshold]
            
            logger.info(f"Identified {len(inefficiencies)} market inefficiencies")
            return inefficiencies
        
        except Exception as e:
            logger.error(f"Error identifying market inefficiencies: {e}")
            return []
    
    def design_protocol(self, inefficiency: Dict) -> Dict:
        """
        Design a new protocol to address a market inefficiency.
        
        Args:
            inefficiency: Market inefficiency to address
            
        Returns:
            Dict: Protocol design
        """
        logger.info(f"Designing protocol for inefficiency: {inefficiency['name']}")
        
        try:
            protocol_type = inefficiency["type"]
            
            # Select appropriate template based on protocol type
            template_name = f"{protocol_type}Template"
            template = self.protocol_templates.get(template_name)
            
            if not template:
                logger.error(f"Template not found for protocol type: {protocol_type}")
                return {}
            
            # Generate protocol parameters based on inefficiency
            parameters = self._generate_protocol_parameters(inefficiency)
            
            # Create protocol design
            protocol_design = {
                "name": f"AI-{protocol_type}-{int(time.time())}",
                "description": f"Autonomous protocol addressing {inefficiency['name']}",
                "type": protocol_type,
                "template": template_name,
                "parameters": parameters,
                "inefficiency": inefficiency
            }
            
            logger.info(f"Protocol design created: {protocol_design['name']}")
            return protocol_design
        
        except Exception as e:
            logger.error(f"Error designing protocol: {e}")
            return {}
    
    def _generate_protocol_parameters(self, inefficiency: Dict) -> Dict:
        """
        Generate protocol parameters based on the inefficiency.
        
        Args:
            inefficiency: Market inefficiency to address
            
        Returns:
            Dict: Protocol parameters
        """
        # This is a simplified example. In a real implementation, this would be much more sophisticated.
        parameters = {}
        
        if inefficiency["type"] == "DEX":
            parameters = {
                "fee_tiers": [0.01, 0.05, 0.3, 1.0],  # Fee tiers in percentage
                "tick_spacing": [1, 10, 60, 200],      # Tick spacing for each fee tier
                "initial_price_range": 20,             # Initial price range percentage
                "protocol_fee": 0.15,                  # Protocol fee percentage
                "max_price_impact": 0.5                # Maximum price impact percentage
            }
        
        elif inefficiency["type"] == "LendingProtocol":
            parameters = {
                "base_rate": 0.5,                      # Base interest rate percentage
                "utilization_slope1": 4.0,             # Slope of interest rate curve below optimal utilization
                "utilization_slope2": 60.0,            # Slope of interest rate curve above optimal utilization
                "optimal_utilization": 80.0,           # Optimal utilization percentage
                "liquidation_threshold": 85.0,         # Liquidation threshold percentage
                "liquidation_bonus": 5.0,              # Liquidation bonus percentage
                "reserve_factor": 10.0                 # Reserve factor percentage
            }
        
        elif inefficiency["type"] == "Derivatives":
            parameters = {
                "max_leverage": 10,                    # Maximum leverage
                "min_collateral": 10.0,                # Minimum collateral percentage
                "funding_interval": 8,                 # Funding interval in hours
                "max_funding_rate": 0.1,               # Maximum funding rate percentage
                "liquidation_fee": 2.0,                # Liquidation fee percentage
                "oracle_sources": 3,                   # Number of oracle sources
                "oracle_deviation_threshold": 2.0      # Oracle deviation threshold percentage
            }
        
        return parameters
    
    def generate_protocol_code(self, protocol_design: Dict) -> str:
        """
        Generate Solidity code for a protocol design.
        
        Args:
            protocol_design: Protocol design
            
        Returns:
            str: Generated Solidity code
        """
        logger.info(f"Generating code for protocol: {protocol_design['name']}")
        
        try:
            template_name = protocol_design["template"]
            template = self.protocol_templates.get(template_name)
            
            if not template:
                logger.error(f"Template not found: {template_name}")
                return ""
            
            # Replace template placeholders with actual parameters
            code = template
            
            # Replace basic placeholders
            code = code.replace("{{PROTOCOL_NAME}}", protocol_design["name"])
            code = code.replace("{{PROTOCOL_DESCRIPTION}}", protocol_design["description"])
            
            # Replace parameter placeholders
            for param_name, param_value in protocol_design["parameters"].items():
                placeholder = f"{{{{PARAM_{param_name.upper()}}}}}"
                
                if isinstance(param_value, list):
                    # Handle list parameters
                    param_str = ", ".join([str(v) for v in param_value])
                    code = code.replace(placeholder, param_str)
                else:
                    # Handle scalar parameters
                    code = code.replace(placeholder, str(param_value))
            
            # Save generated code
            output_path = os.path.join(
                self.config["paths"]["output_dir"],
                f"{protocol_design['name']}.sol"
            )
            
            with open(output_path, 'w') as file:
                file.write(code)
            
            logger.info(f"Protocol code generated and saved to {output_path}")
            return code
        
        except Exception as e:
            logger.error(f"Error generating protocol code: {e}")
            return ""
    
    def simulate_protocol(self, protocol_design: Dict, code: str) -> Dict:
        """
        Simulate a protocol in the World Model Simulator.
        
        Args:
            protocol_design: Protocol design
            code: Generated Solidity code
            
        Returns:
            Dict: Simulation results
        """
        logger.info(f"Simulating protocol: {protocol_design['name']}")
        
        try:
            # Compile the protocol code
            compiled_code = self._compile_protocol(code)
            
            if not compiled_code:
                logger.error(f"Failed to compile protocol: {protocol_design['name']}")
                return {"success": False}
            
            # Set up simulation parameters
            simulation_params = {
                "protocol_name": protocol_design["name"],
                "protocol_type": protocol_design["type"],
                "bytecode": compiled_code["bytecode"],
                "abi": compiled_code["abi"],
                "parameters": protocol_design["parameters"],
                "num_simulations": self.config["simulation"]["num_simulations"],
                "duration_days": self.config["simulation"]["simulation_duration_days"]
            }
            
            # Run the simulation
            simulation_results = self.world_model.simulate_protocol(simulation_params)
            
            # Save simulation results
            results_path = os.path.join(
                self.config["paths"]["simulation_results"],
                f"{protocol_design['name']}_simulation_{int(time.time())}.json"
            )
            
            with open(results_path, 'w') as file:
                json.dump(simulation_results, file, indent=2)
            
            logger.info(f"Simulation results saved to {results_path}")
            return simulation_results
        
        except Exception as e:
            logger.error(f"Error simulating protocol: {e}")
            return {"success": False}
    
    def _compile_protocol(self, code: str) -> Dict:
        """
        Compile a protocol's Solidity code.
        
        Args:
            code: Solidity code
            
        Returns:
            Dict: Compilation results
        """
        try:
            # Ensure solc is installed
            solcx.install_solc('0.8.20')
            solcx.set_solc_version('0.8.20')
            
            # Compile the contract
            compiled_sol = solcx.compile_source(
                code,
                output_values=['abi', 'bin'],
                solc_version='0.8.20'
            )
            
            # Get contract interface
            contract_id, contract_interface = compiled_sol.popitem()
            
            return {
                "bytecode": contract_interface['bin'],
                "abi": contract_interface['abi']
            }
        
        except Exception as e:
            logger.error(f"Error compiling protocol: {e}")
            return {}
    
    def deploy_protocol(self, protocol_design: Dict, simulation_results: Dict, code: str) -> bool:
        """
        Deploy a protocol using the ProtocolGenesisEngine.
        
        Args:
            protocol_design: Protocol design
            simulation_results: Simulation results
            code: Generated Solidity code
            
        Returns:
            bool: Success
        """
        logger.info(f"Deploying protocol: {protocol_design['name']}")
        
        try:
            # Check if simulation was successful
            if not simulation_results.get("success", False):
                logger.error(f"Cannot deploy protocol with unsuccessful simulation: {protocol_design['name']}")
                return False
            
            # Check if protocol meets performance criteria
            if not self._meets_performance_criteria(simulation_results):
                logger.error(f"Protocol does not meet performance criteria: {protocol_design['name']}")
                return False
            
            # Compile the protocol code
            compiled_code = self._compile_protocol(code)
            
            if not compiled_code:
                logger.error(f"Failed to compile protocol for deployment: {protocol_design['name']}")
                return False
            
            # Deploy the implementation contract
            implementation_address = self._deploy_implementation(compiled_code["bytecode"], compiled_code["abi"])
            
            if not implementation_address:
                logger.error(f"Failed to deploy implementation: {protocol_design['name']}")
                return False
            
            # Register the implementation as a template in the ProtocolGenesisEngine
            template_id = self._register_template(
                implementation_address,
                protocol_design["name"],
                protocol_design["description"],
                protocol_design["type"]
            )
            
            if template_id is None:
                logger.error(f"Failed to register template: {protocol_design['name']}")
                return False
            
            # Create a protocol instance
            instance_id = self._create_protocol_instance(
                template_id,
                protocol_design["name"],
                protocol_design["description"],
                5000,  # 50% treasury allocation (in basis points)
                b''    # Empty initialization data for this example
            )
            
            if instance_id is None:
                logger.error(f"Failed to create protocol instance: {protocol_design['name']}")
                return False
            
            logger.info(f"Protocol deployed successfully: {protocol_design['name']}")
            return True
        
        except Exception as e:
            logger.error(f"Error deploying protocol: {e}")
            return False
    
    def _meets_performance_criteria(self, simulation_results: Dict) -> bool:
        """
        Check if a protocol meets performance criteria.
        
        Args:
            simulation_results: Simulation results
            
        Returns:
            bool: Whether the protocol meets performance criteria
        """
        # This is a simplified example. In a real implementation, this would be much more sophisticated.
        
        # Check for minimum success rate
        if simulation_results.get("success_rate", 0) < 0.9:
            return False
        
        # Check for minimum profitability
        if simulation_results.get("profitability", {}).get("roi", 0) < 0.1:
            return False
        
        # Check for maximum risk
        if simulation_results.get("risk", {}).get("max_drawdown", 1.0) > 0.2:
            return False
        
        return True
    
    def _deploy_implementation(self, bytecode: str, abi: List) -> Optional[str]:
        """
        Deploy an implementation contract.
        
        Args:
            bytecode: Contract bytecode
            abi: Contract ABI
            
        Returns:
            Optional[str]: Contract address or None if deployment failed
        """
        try:
            # Create the transaction
            tx = {
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 4000000,
                'gasPrice': self.w3.eth.gas_price,
                'data': bytecode
            }
            
            # Sign and send the transaction
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for the transaction to be mined
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1 and receipt.contractAddress:
                logger.info(f"Implementation deployed at {receipt.contractAddress}")
                return receipt.contractAddress
            else:
                logger.error(f"Implementation deployment failed: {receipt.transactionHash.hex()}")
                return None
        
        except Exception as e:
            logger.error(f"Error deploying implementation: {e}")
            return None
    
    def _register_template(self, implementation_address: str, name: str, description: str, protocol_type: str) -> Optional[int]:
        """
        Register a protocol template in the ProtocolGenesisEngine.
        
        Args:
            implementation_address: Address of the implementation contract
            name: Name of the protocol
            description: Description of the protocol
            protocol_type: Type of the protocol
            
        Returns:
            Optional[int]: Template ID or None if registration failed
        """
        try:
            # Get the ProtocolGenesisEngine contract
            engine_address = self.config["contracts"]["protocol_genesis_engine"]
            engine_abi = self.contract_abis.get("protocol_genesis_engine")
            
            if not engine_abi:
                logger.error("ProtocolGenesisEngine ABI not found")
                return None
            
            engine_contract = self.w3.eth.contract(address=engine_address, abi=engine_abi)
            
            # Map protocol type string to enum value
            protocol_types = self.config["protocol_types"]
            protocol_type_enum = protocol_types.index(protocol_type) if protocol_type in protocol_types else len(protocol_types)
            
            # Register the template
            tx = engine_contract.functions.registerTemplate(
                implementation_address,
                name,
                description,
                protocol_type_enum
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send the transaction
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for the transaction to be mined
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                # Get the template ID from the event
                template_id = None
                for log in engine_contract.events.TemplateRegistered().process_receipt(receipt):
                    template_id = log.args.templateId
                
                if template_id is not None:
                    logger.info(f"Template registered with ID: {template_id}")
                    return template_id
                else:
                    logger.error("Failed to get template ID from event")
                    return None
            else:
                logger.error(f"Template registration failed: {receipt.transactionHash.hex()}")
                return None
        
        except Exception as e:
            logger.error(f"Error registering template: {e}")
            return None
    
    def _create_protocol_instance(self, template_id: int, name: str, description: str, 
                                 treasury_allocation: int, init_data: bytes) -> Optional[int]:
        """
        Create a protocol instance using the ProtocolGenesisEngine.
        
        Args:
            template_id: ID of the template
            name: Name of the protocol instance
            description: Description of the protocol instance
            treasury_allocation: Treasury allocation in basis points
            init_data: Initialization data
            
        Returns:
            Optional[int]: Instance ID or None if creation failed
        """
        try:
            # Get the ProtocolGenesisEngine contract
            engine_address = self.config["contracts"]["protocol_genesis_engine"]
            engine_abi = self.contract_abis.get("protocol_genesis_engine")
            
            if not engine_abi:
                logger.error("ProtocolGenesisEngine ABI not found")
                return None
            
            engine_contract = self.w3.eth.contract(address=engine_address, abi=engine_abi)
            
            # Create the protocol instance
            tx = engine_contract.functions.createProtocol(
                template_id,
                name,
                description,
                treasury_allocation,
                init_data
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 4000000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send the transaction
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for the transaction to be mined
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                # Get the instance ID from the event
                instance_id = None
                for log in engine_contract.events.ProtocolCreated().process_receipt(receipt):
                    instance_id = log.args.instanceId
                
                if instance_id is not None:
                    logger.info(f"Protocol instance created with ID: {instance_id}")
                    return instance_id
                else:
                    logger.error("Failed to get instance ID from event")
                    return None
            else:
                logger.error(f"Protocol instance creation failed: {receipt.transactionHash.hex()}")
                return None
        
        except Exception as e:
            logger.error(f"Error creating protocol instance: {e}")
            return None
    
    def run(self):
        """
        Run the Protocol Synthesizer.
        """
        logger.info("Starting Protocol Synthesizer run")
        
        try:
            # Identify market inefficiencies
            inefficiencies = self.identify_market_inefficiencies()
            
            if not inefficiencies:
                logger.info("No market inefficiencies identified")
                return
            
            # Sort inefficiencies by score (highest first)
            inefficiencies.sort(key=lambda x: x["score"], reverse=True)
            
            # Limit the number of protocols to create
            max_protocols = self.config["analysis"]["max_protocols_per_run"]
            inefficiencies = inefficiencies[:max_protocols]
            
            for inefficiency in inefficiencies:
                # Design a protocol to address the inefficiency
                protocol_design = self.design_protocol(inefficiency)
                
                if not protocol_design:
                    logger.error(f"Failed to design protocol for inefficiency: {inefficiency['name']}")
                    continue
                
                # Generate protocol code
                code = self.generate_protocol_code(protocol_design)
                
                if not code:
                    logger.error(f"Failed to generate code for protocol: {protocol_design['name']}")
                    continue
                
                # Simulate the protocol
                simulation_results = self.simulate_protocol(protocol_design, code)
                
                if not simulation_results.get("success", False):
                    logger.error(f"Simulation failed for protocol: {protocol_design['name']}")
                    continue
                
                # Deploy the protocol
                deployment_success = self.deploy_protocol(protocol_design, simulation_results, code)
                
                if deployment_success:
                    logger.info(f"Successfully deployed protocol: {protocol_design['name']}")
                else:
                    logger.error(f"Failed to deploy protocol: {protocol_design['name']}")
            
            logger.info("Protocol Synthesizer run completed")
        
        except Exception as e:
            logger.error(f"Error in Protocol Synthesizer run: {e}")
            raise

def main():
    """
    Main function to run the Protocol Synthesizer.
    """
    try:
        protocol_synthesizer = ProtocolSynthesizer()
        protocol_synthesizer.run()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()