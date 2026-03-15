import os
import json
import time
import logging
from web3 import Web3
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("deploy_v42.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DeployV42")

def load_contract_abi_and_bytecode(contract_name):
    """Load contract ABI and bytecode from JSON file"""
    try:
        with open(f"abi/{contract_name}.json", "r") as f:
            contract_json = json.load(f)
            return contract_json["abi"], contract_json["bytecode"]
    except Exception as e:
        logger.error(f"Error loading contract ABI and bytecode for {contract_name}: {str(e)}")
        raise

def deploy_contract(w3, contract_name, deployer_address, deployer_private_key, constructor_args=None):
    """Deploy a contract to the blockchain"""
    try:
        # Load contract ABI and bytecode
        abi, bytecode = load_contract_abi_and_bytecode(contract_name)
        
        # Create contract object
        contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # Build constructor transaction
        if constructor_args:
            tx = contract.constructor(*constructor_args).build_transaction({
                'from': deployer_address,
                'nonce': w3.eth.get_transaction_count(deployer_address),
                'gas': 5000000,
                'gasPrice': w3.eth.gas_price
            })
        else:
            tx = contract.constructor().build_transaction({
                'from': deployer_address,
                'nonce': w3.eth.get_transaction_count(deployer_address),
                'gas': 5000000,
                'gasPrice': w3.eth.gas_price
            })
        
        # Sign transaction
        signed_tx = w3.eth.account.sign_transaction(tx, deployer_private_key)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.info(f"Transaction sent: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress
        
        logger.info(f"Contract {contract_name} deployed at: {contract_address}")
        
        # Create contract instance
        contract_instance = w3.eth.contract(address=contract_address, abi=abi)
        
        return contract_address, contract_instance
        
    except Exception as e:
        logger.error(f"Error deploying contract {contract_name}: {str(e)}")
        raise

def deploy_v42_contracts():
    """Deploy V42 contracts"""
    # Load environment variables
    load_dotenv()
    
    # Connect to blockchain
    provider_url = os.getenv("WEB3_PROVIDER_URL", "http://localhost:8545")
    w3 = Web3(Web3.HTTPProvider(provider_url))
    
    if not w3.is_connected():
        logger.error(f"Failed to connect to provider at {provider_url}")
        return
    
    logger.info(f"Connected to blockchain at {provider_url}")
    logger.info(f"Current block number: {w3.eth.block_number}")
    
    # Get deployer account
    # SECURITY: Private key handling disabled - use secure transaction signer
    if not deployer_private_key:
        logger.error("Private key not found in environment variables")
        return
    
    # SECURITY: Use secure transaction signer instead of private key
try:
    from secure_transaction_signer import SecureTransactionSigner
    signer = SecureTransactionSigner()
    deployer_account = signer.get_account()
except ImportError:
    raise RuntimeError("SECURITY ERROR: SecureTransactionSigner not available. Direct private key usage is prohibited.")
    deployer_address = deployer_account.address
    
    logger.info(f"Deploying contracts from: {deployer_address}")
    
    # Deploy PreCognitiveOracle
    logger.info("Deploying PreCognitiveOracle...")
    oracle_address, oracle_contract = deploy_contract(
        w3, "PreCognitiveOracle", deployer_address, deployer_private_key
    )
    
    # Deploy EventDrivenStrategy
    logger.info("Deploying EventDrivenStrategy...")
    strategy_address, strategy_contract = deploy_contract(
        w3, "EventDrivenStrategy", deployer_address, deployer_private_key,
        constructor_args=[oracle_address]
    )
    
    # Register event types and time horizons
    logger.info("Registering event types and time horizons...")
    
    # Define event types
    event_types = [
        ("regulatory_change", "Prediction for regulatory changes affecting crypto assets"),
        ("market_volatility", "Prediction for significant market volatility events"),
        ("liquidity_crisis", "Prediction for liquidity crises in DeFi protocols"),
        ("protocol_hack", "Prediction for major protocol exploits or hacks"),
        ("macro_economic_shift", "Prediction for macroeconomic shifts affecting crypto"),
        ("supply_shock", "Prediction for supply shocks in major crypto assets")
    ]
    
    # Define time horizons
    time_horizons = [
        ("short_term", 7 * 86400),  # 7 days
        ("medium_term", 30 * 86400),  # 30 days
        ("long_term", 90 * 86400)  # 90 days
    ]
    
    # Register event types
    event_type_ids = {}
    for name, description in event_types:
        try:
            tx = oracle_contract.functions.registerEventType(
                name, description
            ).build_transaction({
                'from': deployer_address,
                'nonce': w3.eth.get_transaction_count(deployer_address),
                'gas': 500000,
                'gasPrice': w3.eth.gas_price
            })
            
            signed_tx = w3.eth.account.sign_transaction(tx, deployer_private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Parse event to get event type ID
            for log in tx_receipt.logs:
                try:
                    event = oracle_contract.events.EventTypeRegistered().process_log(log)
                    event_type_id = event.args.eventTypeId.hex()
                    event_type_ids[name] = event_type_id
                    logger.info(f"Registered event type: {name} with ID {event_type_id}")
                    break
                except:
                    continue
            
        except Exception as e:
            logger.error(f"Error registering event type {name}: {str(e)}")
    
    # Register time horizons
    horizon_ids = {}
    for name, duration in time_horizons:
        try:
            tx = oracle_contract.functions.registerTimeHorizon(
                name, duration
            ).build_transaction({
                'from': deployer_address,
                'nonce': w3.eth.get_transaction_count(deployer_address),
                'gas': 500000,
                'gasPrice': w3.eth.gas_price
            })
            
            signed_tx = w3.eth.account.sign_transaction(tx, deployer_private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Parse event to get horizon ID
            for log in tx_receipt.logs:
                try:
                    event = oracle_contract.events.TimeHorizonRegistered().process_log(log)
                    horizon_id = event.args.horizonId.hex()
                    horizon_ids[name] = horizon_id
                    logger.info(f"Registered time horizon: {name} with ID {horizon_id}")
                    break
                except:
                    continue
            
        except Exception as e:
            logger.error(f"Error registering time horizon {name}: {str(e)}")
    
    # Configure EventDrivenStrategy
    logger.info("Configuring EventDrivenStrategy...")
    
    # Use regulatory_change event type and medium_term horizon
    target_event_type = "regulatory_change"
    target_horizon = "medium_term"
    
    if target_event_type in event_type_ids and target_horizon in horizon_ids:
        try:
            tx = strategy_contract.functions.configureStrategy(
                w3.to_bytes(hexstr=event_type_ids[target_event_type]),
                w3.to_bytes(hexstr=horizon_ids[target_horizon]),
                7500,  # 75% probability trigger
                8000,  # 80% confidence trigger
                True   # Active
            ).build_transaction({
                'from': deployer_address,
                'nonce': w3.eth.get_transaction_count(deployer_address),
                'gas': 500000,
                'gasPrice': w3.eth.gas_price
            })
            
            signed_tx = w3.eth.account.sign_transaction(tx, deployer_private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Configured EventDrivenStrategy with event type {target_event_type} and horizon {target_horizon}")
            
        except Exception as e:
            logger.error(f"Error configuring EventDrivenStrategy: {str(e)}")
    else:
        logger.error(f"Event type {target_event_type} or horizon {target_horizon} not registered")
    
    # Save deployment information
    deployment_info = {
        "network": {
            "provider_url": provider_url,
            "chain_id": w3.eth.chain_id,
            "block_number": w3.eth.block_number
        },
        "deployer": deployer_address,
        "contracts": {
            "PreCognitiveOracle": {
                "address": oracle_address,
                "deployed_at": int(time.time())
            },
            "EventDrivenStrategy": {
                "address": strategy_address,
                "deployed_at": int(time.time()),
                "oracle_address": oracle_address
            }
        },
        "event_types": event_type_ids,
        "time_horizons": horizon_ids
    }
    
    # Save to file
    with open("deployment_v42.json", "w") as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info(f"Deployment information saved to deployment_v42.json")
    
    # Set environment variables for Oracle Connector
    os.environ["ORACLE_ADDRESS"] = oracle_address
    
    logger.info(f"V42 contracts deployed successfully")
    logger.info(f"PreCognitiveOracle: {oracle_address}")
    logger.info(f"EventDrivenStrategy: {strategy_address}")
    
    return deployment_info

if __name__ == "__main__":
    deploy_v42_contracts()