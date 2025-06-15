import os
import json
import yaml
import time
import hashlib
import logging
from typing import Dict, List, Tuple, Optional, Any
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
import numpy as np
import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import solcx
from solcx import compile_source, install_solc

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("metamorphic_core.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MetamorphicCore")

class MetamorphicCore:
    """
    The Metamorphic Core is responsible for analyzing the system's core contracts,
    identifying potential improvements, and proposing upgrades through the SelfAmendingProtocol.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Metamorphic Core.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path or "metamorphic_core_config.yaml")
        self._setup_directories()
        self._init_web3()
        self._init_models()
        self._load_contract_abis()
        self._load_contract_sources()
        
        logger.info("Metamorphic Core initialized")
    
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
                    "self_amending_protocol": os.getenv("SELF_AMENDING_PROTOCOL_ADDRESS", ""),
                    "trust_curve": os.getenv("TRUST_CURVE_ADDRESS", ""),
                    "proof_marketplace": os.getenv("PROOF_MARKETPLACE_ADDRESS", ""),
                    "proxy_admin": os.getenv("PROXY_ADMIN_ADDRESS", "")
                },
                "paths": {
                    "contract_sources": "./contracts",
                    "contract_abis": "./abi",
                    "output_dir": "./metamorphic_output",
                    "simulation_results": "./simulation_results"
                },
                "analysis": {
                    "gas_optimization_threshold": 10,  # Percentage improvement to trigger proposal
                    "security_score_threshold": 85,    # Minimum security score for proposals
                    "max_proposals_per_run": 3
                },
                "simulation": {
                    "num_simulations": 1000,
                    "simulation_duration_days": 30
                }
            }
    
    def _setup_directories(self):
        """
        Create necessary directories if they don't exist.
        """
        for path_key in ["output_dir", "simulation_results"]:
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
    
    def _init_models(self):
        """
        Initialize AI models for contract analysis.
        """
        try:
            # Code quality analysis model
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
            self.code_model = TFAutoModelForSequenceClassification.from_pretrained(
                "microsoft/codebert-base", num_labels=2
            )
            
            # Simple gas usage prediction model
            self.gas_model = tf.keras.Sequential([
                tf.keras.layers.Dense(128, activation='relu', input_shape=(50,)),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dense(1)
            ])
            
            logger.info("AI models initialized")
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")
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
    
    def _load_contract_sources(self):
        """
        Load contract source code from Solidity files.
        """
        self.contract_sources = {}
        source_dir = self.config["paths"]["contract_sources"]
        
        try:
            for file_name in os.listdir(source_dir):
                if file_name.endswith(".sol"):
                    file_path = os.path.join(source_dir, file_name)
                    with open(file_path, 'r') as file:
                        contract_name = file_name.replace(".sol", "")
                        self.contract_sources[contract_name] = file.read()
                        logger.info(f"Loaded source code for {contract_name}")
        except Exception as e:
            logger.error(f"Error loading contract sources: {e}")
            raise
    
    def analyze_contracts(self) -> List[Dict]:
        """
        Analyze all registered contracts for potential improvements.
        
        Returns:
            List[Dict]: List of improvement opportunities
        """
        logger.info("Starting contract analysis")
        improvement_opportunities = []
        
        # Get the list of registered contracts from SelfAmendingProtocol
        registered_contracts = self._get_registered_contracts()
        
        for contract_address in registered_contracts:
            contract_name = self._get_contract_name(contract_address)
            if not contract_name:
                logger.warning(f"Could not determine name for contract at {contract_address}")
                continue
            
            logger.info(f"Analyzing contract: {contract_name} at {contract_address}")
            
            # Get the contract source code
            source_code = self.contract_sources.get(contract_name)
            if not source_code:
                logger.warning(f"Source code not found for {contract_name}")
                continue
            
            # Analyze for gas optimization opportunities
            gas_improvements = self._analyze_gas_usage(contract_name, source_code)
            
            # Analyze for security improvements
            security_improvements = self._analyze_security(contract_name, source_code)
            
            # Analyze for architectural improvements
            architectural_improvements = self._analyze_architecture(contract_name, source_code)
            
            # Combine all improvements
            all_improvements = gas_improvements + security_improvements + architectural_improvements
            
            if all_improvements:
                improvement_opportunities.append({
                    "contract_name": contract_name,
                    "contract_address": contract_address,
                    "improvements": all_improvements
                })
        
        logger.info(f"Found {len(improvement_opportunities)} contracts with improvement opportunities")
        return improvement_opportunities
    
    def _get_registered_contracts(self) -> List[str]:
        """
        Get the list of registered contracts from SelfAmendingProtocol.
        
        Returns:
            List[str]: List of contract addresses
        """
        # This is a placeholder. In a real implementation, you would query the SelfAmendingProtocol contract
        # to get the list of registered contracts.
        return [
            self.config["contracts"]["trust_curve"],
            self.config["contracts"]["proof_marketplace"]
        ]
    
    def _get_contract_name(self, contract_address: str) -> Optional[str]:
        """
        Get the name of a contract from its address.
        
        Args:
            contract_address: Contract address
            
        Returns:
            Optional[str]: Contract name or None if not found
        """
        # This is a placeholder. In a real implementation, you would have a mapping of addresses to names,
        # or query the blockchain for the contract name.
        for name, address in self.config["contracts"].items():
            if address.lower() == contract_address.lower():
                return name
        return None
    
    def _analyze_gas_usage(self, contract_name: str, source_code: str) -> List[Dict]:
        """
        Analyze a contract for gas optimization opportunities.
        
        Args:
            contract_name: Name of the contract
            source_code: Source code of the contract
            
        Returns:
            List[Dict]: List of gas optimization opportunities
        """
        logger.info(f"Analyzing gas usage for {contract_name}")
        improvements = []
        
        # Example gas optimization patterns to look for
        patterns = [
            {
                "name": "Storage vs Memory",
                "pattern": "storage",
                "suggestion": "Consider using memory instead of storage for read-only operations"
            },
            {
                "name": "Unnecessary SLOAD",
                "pattern": "for (uint",
                "suggestion": "Cache storage variables in memory before loops"
            },
            {
                "name": "Multiple Reads",
                "pattern": ".length",
                "suggestion": "Cache array length in a local variable before loop"
            }
        ]
        
        for pattern in patterns:
            if pattern["pattern"] in source_code:
                improvements.append({
                    "type": "gas_optimization",
                    "name": pattern["name"],
                    "description": pattern["suggestion"],
                    "severity": "medium",
                    "estimated_improvement": "5-15%"
                })
        
        return improvements
    
    def _analyze_security(self, contract_name: str, source_code: str) -> List[Dict]:
        """
        Analyze a contract for security improvements.
        
        Args:
            contract_name: Name of the contract
            source_code: Source code of the contract
            
        Returns:
            List[Dict]: List of security improvement opportunities
        """
        logger.info(f"Analyzing security for {contract_name}")
        improvements = []
        
        # Example security patterns to look for
        patterns = [
            {
                "name": "Reentrancy",
                "pattern": "call{value:",
                "suggestion": "Use ReentrancyGuard or checks-effects-interactions pattern"
            },
            {
                "name": "Unchecked Return",
                "pattern": ".call(",
                "suggestion": "Check return value of low-level calls"
            },
            {
                "name": "Integer Overflow",
                "pattern": "uint",
                "suggestion": "Ensure proper overflow checks or use SafeMath"
            }
        ]
        
        for pattern in patterns:
            if pattern["pattern"] in source_code and "// SECURITY: " + pattern["name"] not in source_code:
                improvements.append({
                    "type": "security_improvement",
                    "name": pattern["name"],
                    "description": pattern["suggestion"],
                    "severity": "high",
                    "estimated_improvement": "Critical security enhancement"
                })
        
        return improvements
    
    def _analyze_architecture(self, contract_name: str, source_code: str) -> List[Dict]:
        """
        Analyze a contract for architectural improvements.
        
        Args:
            contract_name: Name of the contract
            source_code: Source code of the contract
            
        Returns:
            List[Dict]: List of architectural improvement opportunities
        """
        logger.info(f"Analyzing architecture for {contract_name}")
        improvements = []
        
        # Example architectural patterns to look for
        if contract_name == "TrustCurve":
            if "verifiedIntelligenceScore" in source_code and "adaptiveWeighting" not in source_code:
                improvements.append({
                    "type": "architectural_improvement",
                    "name": "Adaptive Trust Weighting",
                    "description": "Implement adaptive weighting based on historical accuracy",
                    "severity": "medium",
                    "estimated_improvement": "20% more accurate trust scores"
                })
        
        elif contract_name == "ProofMarketplaceV41":
            if "ExecutionRights" in source_code and "fractionalOwnership" not in source_code:
                improvements.append({
                    "type": "architectural_improvement",
                    "name": "Fractional Ownership",
                    "description": "Implement fractional ownership of execution rights",
                    "severity": "medium",
                    "estimated_improvement": "Increased liquidity and market efficiency"
                })
        
        return improvements
    
    def generate_improved_contract(self, contract_name: str, improvements: List[Dict]) -> str:
        """
        Generate an improved version of a contract based on identified improvements.
        
        Args:
            contract_name: Name of the contract
            improvements: List of improvements to implement
            
        Returns:
            str: Improved contract source code
        """
        logger.info(f"Generating improved contract for {contract_name}")
        
        # Get the original source code
        source_code = self.contract_sources.get(contract_name)
        if not source_code:
            logger.error(f"Source code not found for {contract_name}")
            return ""
        
        # This is a simplified example. In a real implementation, you would use a more sophisticated
        # approach to modify the source code, possibly using a Solidity parser.
        improved_code = source_code
        
        for improvement in improvements:
            if improvement["type"] == "gas_optimization":
                if improvement["name"] == "Storage vs Memory":
                    # Example: Replace storage with memory for read-only operations
                    improved_code = improved_code.replace(
                        "function getTrustScore(uint256 _strategyId) external view returns (uint256) {",
                        "function getTrustScore(uint256 _strategyId) external view returns (uint256) {\n        // Gas optimization: Using memory for read-only operations"
                    )
                
                elif improvement["name"] == "Unnecessary SLOAD":
                    # Example: Cache storage variables in memory before loops
                    improved_code = improved_code.replace(
                        "for (uint256 i = 0; i < array.length; i++) {",
                        "uint256 length = array.length;\n        for (uint256 i = 0; i < length; i++) {"
                    )
            
            elif improvement["type"] == "security_improvement":
                if improvement["name"] == "Reentrancy":
                    # Example: Add ReentrancyGuard
                    improved_code = improved_code.replace(
                        "contract " + contract_name + " {",
                        "import \"@openzeppelin/contracts/security/ReentrancyGuard.sol\";\n\ncontract " + contract_name + " is ReentrancyGuard {"
                    )
                    improved_code = improved_code.replace(
                        "function withdraw(",
                        "function withdraw( nonReentrant "
                    )
            
            elif improvement["type"] == "architectural_improvement":
                if improvement["name"] == "Adaptive Trust Weighting" and contract_name == "TrustCurve":
                    # Example: Add adaptive weighting to TrustCurve
                    improved_code = improved_code.replace(
                        "uint256 public constant RECENCY_WEIGHT = 30;",
                        "uint256 public adaptiveRecencyWeight = 30;\n    uint256 public adaptivePerformanceWeight = 70;"
                    )
                    
                    # Add a new function to adjust weights based on historical accuracy
                    if "function adjustWeights(" not in improved_code:
                        improved_code = improved_code.replace(
                            "function getTrustScore(",
                            "/**\n     * @dev Adjust weights based on historical accuracy\n     * @param _historicalAccuracy The historical accuracy of the trust score (0-100)\n     */\n    function adjustWeights(uint256 _historicalAccuracy) external onlyOwner {\n        require(_historicalAccuracy <= 100, \"Historical accuracy must be 0-100\");\n        \n        // Adjust weights based on historical accuracy\n        // Higher accuracy means we can trust performance more\n        if (_historicalAccuracy > 80) {\n            adaptivePerformanceWeight = 80;\n            adaptiveRecencyWeight = 20;\n        } else if (_historicalAccuracy > 60) {\n            adaptivePerformanceWeight = 70;\n            adaptiveRecencyWeight = 30;\n        } else {\n            adaptivePerformanceWeight = 60;\n            adaptiveRecencyWeight = 40;\n        }\n    }\n\n    function getTrustScore("
                        )
                
                elif improvement["name"] == "Fractional Ownership" and contract_name == "ProofMarketplaceV41":
                    # Example: Add fractional ownership to ProofMarketplaceV41
                    improved_code = improved_code.replace(
                        "struct ExecutionRights {",
                        "struct ExecutionRights {\n        uint256 totalShares;\n        mapping(address => uint256) shares;"
                    )
        
        return improved_code
    
    def compile_and_verify(self, contract_name: str, source_code: str) -> Tuple[bool, str, bytes]:
        """
        Compile and verify a contract.
        
        Args:
            contract_name: Name of the contract
            source_code: Source code of the contract
            
        Returns:
            Tuple[bool, str, bytes]: (success, bytecode, abi)
        """
        logger.info(f"Compiling and verifying {contract_name}")
        
        try:
            # Ensure solc is installed
            solcx.install_solc('0.8.20')
            solcx.set_solc_version('0.8.20')
            
            # Compile the contract
            compiled_sol = solcx.compile_source(
                source_code,
                output_values=['abi', 'bin'],
                solc_version='0.8.20'
            )
            
            # Get contract interface
            contract_id, contract_interface = compiled_sol.popitem()
            bytecode = contract_interface['bin']
            abi = contract_interface['abi']
            
            # Verify the contract (in a real implementation, you would do more thorough verification)
            if not bytecode:
                logger.error(f"Compilation failed for {contract_name}: Empty bytecode")
                return False, "", b""
            
            logger.info(f"Successfully compiled {contract_name}")
            return True, json.dumps(abi), bytes.fromhex(bytecode)
        
        except Exception as e:
            logger.error(f"Error compiling {contract_name}: {e}")
            return False, "", b""
    
    def simulate_contract(self, contract_name: str, bytecode: bytes, abi: str) -> Tuple[bool, Dict]:
        """
        Simulate a contract in the World Model Simulator.
        
        Args:
            contract_name: Name of the contract
            bytecode: Contract bytecode
            abi: Contract ABI
            
        Returns:
            Tuple[bool, Dict]: (success, simulation results)
        """
        logger.info(f"Simulating {contract_name} in World Model")
        
        # This is a placeholder. In a real implementation, you would use the World Model Simulator
        # to simulate the contract under various conditions.
        
        # Simulate success for demonstration purposes
        simulation_results = {
            "success": True,
            "gas_usage": {
                "average": 150000,
                "max": 250000,
                "min": 100000
            },
            "performance": {
                "throughput": 100,
                "latency": 2.5
            },
            "security": {
                "score": 90,
                "vulnerabilities": []
            },
            "compliance": {
                "score": 95,
                "issues": []
            }
        }
        
        # Save simulation results
        results_path = os.path.join(
            self.config["paths"]["simulation_results"],
            f"{contract_name}_simulation_{int(time.time())}.json"
        )
        with open(results_path, 'w') as file:
            json.dump(simulation_results, file, indent=2)
        
        logger.info(f"Simulation results saved to {results_path}")
        return True, simulation_results
    
    def verify_ethical_compliance(self, contract_name: str, source_code: str) -> Tuple[bool, Dict]:
        """
        Verify that a contract complies with the ethical framework.
        
        Args:
            contract_name: Name of the contract
            source_code: Source code of the contract
            
        Returns:
            Tuple[bool, Dict]: (compliant, compliance report)
        """
        logger.info(f"Verifying ethical compliance for {contract_name}")
        
        # This is a placeholder. In a real implementation, you would use a more sophisticated
        # approach to verify ethical compliance.
        
        # Check for common ethical issues
        ethical_issues = []
        
        if "selfdestruct" in source_code:
            ethical_issues.append({
                "type": "destructive_capability",
                "description": "Contract contains selfdestruct, which can permanently destroy the contract",
                "severity": "high"
            })
        
        if "require(msg.sender == owner" in source_code:
            ethical_issues.append({
                "type": "centralization",
                "description": "Contract has centralized control mechanisms",
                "severity": "medium"
            })
        
        # Generate compliance report
        compliance_report = {
            "contract_name": contract_name,
            "timestamp": time.time(),
            "issues": ethical_issues,
            "compliant": len(ethical_issues) == 0,
            "score": 100 - (len(ethical_issues) * 10)
        }
        
        logger.info(f"Ethical compliance verification complete: {compliance_report['compliant']}")
        return compliance_report["compliant"], compliance_report
    
    def create_proposal(self, contract_address: str, new_implementation_bytecode: bytes, 
                       simulation_results: Dict, compliance_report: Dict) -> bool:
        """
        Create a proposal to upgrade a contract.
        
        Args:
            contract_address: Address of the contract to upgrade
            new_implementation_bytecode: Bytecode of the new implementation
            simulation_results: Results of the simulation
            compliance_report: Ethical compliance report
            
        Returns:
            bool: Success
        """
        logger.info(f"Creating proposal for contract at {contract_address}")
        
        try:
            # Deploy the new implementation
            new_implementation_address = self._deploy_contract(new_implementation_bytecode)
            
            if not new_implementation_address:
                logger.error("Failed to deploy new implementation")
                return False
            
            # Generate hashes for verification
            simulation_hash = hashlib.sha256(json.dumps(simulation_results).encode()).hexdigest()
            compliance_hash = hashlib.sha256(json.dumps(compliance_report).encode()).hexdigest()
            
            # Create metadata URI (in a real implementation, you would store this in IPFS or similar)
            metadata_uri = f"https://example.com/proposals/{int(time.time())}"
            
            # Get the SelfAmendingProtocol contract
            protocol_address = self.config["contracts"]["self_amending_protocol"]
            protocol_abi = self.contract_abis.get("self_amending_protocol")
            
            if not protocol_abi:
                logger.error("SelfAmendingProtocol ABI not found")
                return False
            
            protocol_contract = self.w3.eth.contract(address=protocol_address, abi=protocol_abi)
            
            # Create the proposal
            tx = protocol_contract.functions.createProposal(
                contract_address,
                new_implementation_address,
                Web3.to_bytes(hexstr=simulation_hash),
                Web3.to_bytes(hexstr=compliance_hash),
                metadata_uri
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
                logger.info(f"Proposal created successfully: {receipt.transactionHash.hex()}")
                return True
            else:
                logger.error(f"Proposal creation failed: {receipt.transactionHash.hex()}")
                return False
        
        except Exception as e:
            logger.error(f"Error creating proposal: {e}")
            return False
    
    def _deploy_contract(self, bytecode: bytes) -> Optional[str]:
        """
        Deploy a contract.
        
        Args:
            bytecode: Contract bytecode
            
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
                logger.info(f"Contract deployed at {receipt.contractAddress}")
                return receipt.contractAddress
            else:
                logger.error(f"Contract deployment failed: {receipt.transactionHash.hex()}")
                return None
        
        except Exception as e:
            logger.error(f"Error deploying contract: {e}")
            return None
    
    def run(self):
        """
        Run the Metamorphic Core.
        """
        logger.info("Starting Metamorphic Core run")
        
        try:
            # Analyze contracts for improvement opportunities
            improvement_opportunities = self.analyze_contracts()
            
            # Process each contract with improvement opportunities
            for opportunity in improvement_opportunities:
                contract_name = opportunity["contract_name"]
                contract_address = opportunity["contract_address"]
                improvements = opportunity["improvements"]
                
                logger.info(f"Processing {contract_name} with {len(improvements)} improvements")
                
                # Generate improved contract
                improved_code = self.generate_improved_contract(contract_name, improvements)
                
                # Compile and verify the improved contract
                success, abi, bytecode = self.compile_and_verify(contract_name, improved_code)
                if not success:
                    logger.error(f"Failed to compile {contract_name}")
                    continue
                
                # Simulate the improved contract
                simulation_success, simulation_results = self.simulate_contract(contract_name, bytecode, abi)
                if not simulation_success:
                    logger.error(f"Simulation failed for {contract_name}")
                    continue
                
                # Verify ethical compliance
                compliance_success, compliance_report = self.verify_ethical_compliance(contract_name, improved_code)
                if not compliance_success:
                    logger.error(f"Ethical compliance verification failed for {contract_name}")
                    continue
                
                # Create proposal
                proposal_success = self.create_proposal(
                    contract_address,
                    bytecode,
                    simulation_results,
                    compliance_report
                )
                
                if proposal_success:
                    logger.info(f"Successfully created proposal for {contract_name}")
                else:
                    logger.error(f"Failed to create proposal for {contract_name}")
            
            logger.info("Metamorphic Core run completed")
        
        except Exception as e:
            logger.error(f"Error in Metamorphic Core run: {e}")
            raise

def main():
    """
    Main function to run the Metamorphic Core.
    """
    try:
        metamorphic_core = MetamorphicCore()
        metamorphic_core.run()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()