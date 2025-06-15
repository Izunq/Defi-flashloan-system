#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Swarm Intelligence Agent V38
Part of the Swarm Intelligence & Public Marketplace architecture

This module enables inter-agent communication, strategy composition,
and participation in the strategy marketplace.
"""

import os
import json
import time
import hashlib
import logging
import numpy as np
import tensorflow as tf
from web3 import Web3
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from eth_account import Account
from eth_utils import to_checksum_address

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SwarmIntelligenceAgentV38")

# Constants
CONFIG_FILE = "swarm_intelligence_config.yaml"
MODELS_DIR = "swarm_models"
DATA_DIR = "swarm_data"
COMMUNICATION_DIR = "agent_communications"

class SwarmIntelligenceAgent:
    """
    Swarm Intelligence Agent that participates in the decentralized
    strategy marketplace and collaborates with other agents.
    """
    
    def __init__(self, config_path: str = None, agent_name: str = None):
        """
        Initialize the Swarm Intelligence Agent
        
        Args:
            config_path: Path to configuration file
            agent_name: Name of the agent (optional)
        """
        self.config = self._load_config(config_path or CONFIG_FILE)
        self.agent_name = agent_name or self.config.get('agent_name', f"Agent_{int(time.time())}")
        self._setup_directories()
        self._init_web3()
        self._init_contracts()
        self._init_models()
        self._register_agent_if_needed()
        
        # Initialize agent state
        self.state = self._load_state()
        
        logger.info(f"Swarm Intelligence Agent {self.agent_name} initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        import yaml
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                  # Validate required fields
            required_fields = [
                'web3_provider', 'contract_addresses',
                'agent_parameters', 'swarm_parameters'
            ]
            
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required config field: {field}")
                    
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Use default config
            return {
                'web3_provider': 'http://localhost:8545',
                'contract_addresses': {
                    'trust_curve': '',
                    'strategy_incubator': '',
                    'swarm_intelligence': ''
                },
                'agent_parameters': {
                    'name': f"Agent_{int(time.time())}",
                    'description': 'Swarm Intelligence Agent V38',
                    'collaboration_threshold': 70,
                    'trust_threshold': 80,
                    'max_collaborators': 5
                },
                'swarm_parameters': {
                    'message_check_interval': 60,
                    'collaboration_interval': 3600,
                    'marketplace_check_interval': 300,
                    'max_strategy_price': Web3.to_wei(0.1, 'ether')
                }
            }
    
    def _setup_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [MODELS_DIR, DATA_DIR, COMMUNICATION_DIR]:
            os.makedirs(directory, exist_ok=True)
    
    def _init_web3(self):
        """Initialize Web3 connection and account"""
        self.web3 = Web3(Web3.HTTPProvider(self.config['web3_provider']))
        
        if not self.web3.is_connected():
            logger.error("Failed to connect to Web3 provider")
            raise ConnectionError("Failed to connect to Web3 provider")
              # Initialize secure transaction signer instead of private key
        from secure_transaction_signer import get_transaction_signer

# EMERGENCY SECURITY PATCH - DEPLOYED IMMEDIATELY
try:
    from emergency_input_sanitizer import (
        emergency_sanitize,
        emergency_validate_eth_address,
        emergency_validate_number,
        emergency_validate_json_data,
        emergency_validate_url_safe,
        SecurityError
    )
    EMERGENCY_VALIDATION_ENABLED = True
    print("🛡️ EMERGENCY VALIDATION ENABLED")
except ImportError:
    EMERGENCY_VALIDATION_ENABLED = False
    print("⚠️ EMERGENCY VALIDATION NOT AVAILABLE")

def emergency_validate_input(value, field_name="input", validation_type="string"):
    """Emergency input validation wrapper"""
    if not EMERGENCY_VALIDATION_ENABLED:
        return value
    
    try:
        if validation_type == "address":
            return emergency_validate_eth_address(value)
        elif validation_type == "number":
            return emergency_validate_number(value)
        elif validation_type == "json":
            return emergency_validate_json_data(value)
        elif validation_type == "url":
            return emergency_validate_url_safe(value)
        else:
            return emergency_sanitize(value, field_name)
    except SecurityError as e:
        raise ValueError(f"SECURITY: {e}")


        self.transaction_signer = get_transaction_signer()
        self.account_address = self.transaction_signer.get_address()
        logger.info(f"Connected to Web3, account: {self.account_address}")
    
    def _init_contracts(self):
        """Initialize contract interfaces"""
        try:
            # Load ABIs
            with open('abi/TrustCurve.json', 'r') as f:
                trust_curve_abi = json.load(f)
                
            with open('abi/StrategyIncubatorV33.json', 'r') as f:
                incubator_abi = json.load(f)
                
            # We'll need to create this ABI after deploying the contract
            try:
                with open('abi/SwarmIntelligenceV38.json', 'r') as f:
                    swarm_abi = json.load(f)
            except FileNotFoundError:
                swarm_abi = None
                logger.warning("SwarmIntelligenceV38 ABI not found, some functions will be unavailable")
            
            # Initialize contract instances
            self.trust_curve = self.web3.eth.contract(
                address=to_checksum_address(self.config['contract_addresses']['trust_curve']),
                abi=trust_curve_abi
            )
            
            self.incubator = self.web3.eth.contract(
                address=to_checksum_address(self.config['contract_addresses']['strategy_incubator']),
                abi=incubator_abi
            )
            
            if swarm_abi and self.config['contract_addresses']['swarm_intelligence']:
                self.swarm = self.web3.eth.contract(
                    address=to_checksum_address(self.config['contract_addresses']['swarm_intelligence']),
                    abi=swarm_abi
                )
            else:
                self.swarm = None
                logger.warning("SwarmIntelligenceV38 contract not initialized")
                
        except Exception as e:
            logger.error(f"Error initializing contracts: {e}")
            raise
    
    def _init_models(self):
        """Initialize machine learning models"""
        try:
            # Create or load collaboration model
            model_path = os.path.join(MODELS_DIR, 'collaboration_model.h5')
            
            if os.path.exists(model_path):
                self.collaboration_model = tf.keras.models.load_model(model_path)
                logger.info("Loaded existing collaboration model")
            else:
                self.collaboration_model = self._create_collaboration_model()
                logger.info("Created new collaboration model")
                
            # Create or load strategy evaluation model
            model_path = os.path.join(MODELS_DIR, 'strategy_evaluation_model.h5')
            
            if os.path.exists(model_path):
                self.evaluation_model = tf.keras.models.load_model(model_path)
                logger.info("Loaded existing strategy evaluation model")
            else:
                self.evaluation_model = self._create_evaluation_model()
                logger.info("Created new strategy evaluation model")
                
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            self.collaboration_model = None
            self.evaluation_model = None
    
    def _create_collaboration_model(self) -> tf.keras.Model:
        """
        Create a model for evaluating collaboration opportunities
        
        Returns:
            TensorFlow model
        """
        # Input: Agent and strategy features
        inputs = tf.keras.layers.Input(shape=(15,))
        
        # Hidden layers
        x = tf.keras.layers.Dense(32, activation='relu')(inputs)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = tf.keras.layers.Dense(16, activation='relu')(x)
        
        # Output: Collaboration score (0-1)
        outputs = tf.keras.layers.Dense(1, activation='sigmoid')(x)
        
        # Create model
        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        
        # Compile model
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _create_evaluation_model(self) -> tf.keras.Model:
        """
        Create a model for evaluating strategies
        
        Returns:
            TensorFlow model
        """
        # Input: Strategy features
        inputs = tf.keras.layers.Input(shape=(10,))
        
        # Hidden layers
        x = tf.keras.layers.Dense(32, activation='relu')(inputs)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = tf.keras.layers.Dense(16, activation='relu')(x)
        
        # Output: Strategy value (0-1)
        outputs = tf.keras.layers.Dense(1, activation='sigmoid')(x)
        
        # Create model
        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        
        # Compile model
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def _register_agent_if_needed(self):
        """Register agent with the swarm if not already registered"""
        if not self.swarm:
            logger.warning("Swarm contract not initialized, skipping registration")
            return
            
        try:
            # Check if agent is already registered
            agent_details = self.swarm.functions.getAgentDetails(self.account_address).call()
            
            if agent_details[0]:  # Name is not empty
                logger.info(f"Agent already registered as {agent_details[0]}")
                return
                
            # Register agent
            metadata = json.dumps({
                'description': self.config['agent_parameters']['description'],
                'version': 'V38',
                'capabilities': ['strategy_composition', 'zk_verification', 'marketplace_participation'],
                'registration_time': datetime.now().isoformat()
            })
            
            tx = self.swarm.functions.registerAgent(
                self.agent_name,
                metadata
            ).build_transaction({
                'from': self.account_address,
                'gas': 500000,
                'maxFeePerGas': self.web3.to_wei(50, 'gwei'),
                'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(self.account_address)
            })
              # Sign and send transaction using secure signer
            signed_tx = self.transaction_signer.sign_transaction(tx)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx)
            
            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.info(f"Successfully registered agent as {self.agent_name}")
            else:
                logger.error("Failed to register agent")
                
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
    
    def _load_state(self) -> Dict:
        """
        Load agent state from file
        
        Returns:
            Agent state dictionary
        """
        state_file = os.path.join(DATA_DIR, f"agent_state_{self.account_address}.json")
        
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
            else:
                # Initialize new state
                state = {
                    'agent_name': self.agent_name,
                    'address': self.account_address,
                    'last_message_check': 0,
                    'last_collaboration_check': 0,
                    'last_marketplace_check': 0,
                    'collaborators': [],
                    'owned_strategies': [],
                    'composed_strategies': [],
                    'strategy_evaluations': {},
                    'agent_evaluations': {}
                }
                
                # Save initial state
                self._save_state(state)
                
                return state
                
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return {
                'agent_name': self.agent_name,
                'address': self.account_address,
                'last_message_check': 0,
                'last_collaboration_check': 0,
                'last_marketplace_check': 0,
                'collaborators': [],
                'owned_strategies': [],
                'composed_strategies': [],
                'strategy_evaluations': {},
                'agent_evaluations': {}
            }
    
    def _save_state(self, state: Dict = None):
        """
        Save agent state to file
        
        Args:
            state: Agent state dictionary (if None, use self.state)
        """
        if state is None:
            state = self.state
            
        state_file = os.path.join(DATA_DIR, f"agent_state_{self.account_address}.json")
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _send_transaction(self, tx: Dict) -> Dict:
        """
        Sign and send a transaction
        
        Args:
            tx: Transaction dictionary
            
        Returns:
            Transaction receipt
        """
        try:
            # Update nonce
            tx['nonce'] = self.web3.eth.get_transaction_count(self.account_address)
              # Sign transaction using secure signer
            signed_tx = self.transaction_signer.sign_transaction(tx)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx)
            
            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return receipt
            
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            return None
    
    def check_messages(self):
        """Check for new messages from other agents"""
        if not self.swarm:
            logger.warning("Swarm contract not initialized, skipping message check")
            return
            
        try:
            # Get inbox
            message_ids = self.swarm.functions.getAgentInbox(self.account_address).call()
            
            if not message_ids:
                logger.info("No messages in inbox")
                return
                
            # Process each message
            for message_id in message_ids:
                # Get message details
                message = self.swarm.functions.getMessage(message_id).call()
                
                # Check if already processed
                if message[5]:  # isProcessed
                    continue
                    
                # Process message
                self._process_message(message_id, message)
                
            # Update last message check time
            self.state['last_message_check'] = int(time.time())
            self._save_state()
            
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
    
    def _process_message(self, message_id: bytes, message: Tuple):
        """
        Process a message from another agent
        
        Args:
            message_id: Message ID
            message: Message details tuple
        """
        try:
            sender = message[0]
            message_type = message[2].hex()
            data = message[3]
            
            logger.info(f"Processing message from {sender}, type: {message_type}")
            
            # Decode message data
            decoded_data = None
            try:
                decoded_data = json.loads(self.web3.to_text(data))
            except:
                logger.warning(f"Failed to decode message data: {data.hex()}")
                decoded_data = {'raw_data': data.hex()}
            
            # Process based on message type
            if message_type == '0x' + 'collaboration_request'.encode().hex():
                self._handle_collaboration_request(sender, decoded_data)
            elif message_type == '0x' + 'strategy_proposal'.encode().hex():
                self._handle_strategy_proposal(sender, decoded_data)
            elif message_type == '0x' + 'zk_proof_request'.encode().hex():
                self._handle_zk_proof_request(sender, decoded_data)
            elif message_type == '0x' + 'marketplace_offer'.encode().hex():
                self._handle_marketplace_offer(sender, decoded_data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
            
            # Mark message as processed
            tx = self.swarm.functions.processMessage(message_id).build_transaction({
                'from': self.account_address,
                'gas': 100000,
                'maxFeePerGas': self.web3.to_wei(50, 'gwei'),
                'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei')
            })
            
            receipt = self._send_transaction(tx)
            
            if receipt and receipt.status == 1:
                logger.info(f"Successfully processed message {message_id.hex()}")
            else:
                logger.error(f"Failed to process message {message_id.hex()}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _handle_collaboration_request(self, sender: str, data: Dict):
        """
        Handle a collaboration request from another agent
        
        Args:
            sender: Sender address
            data: Message data
        """
        try:
            # Extract collaboration details
            collaboration_type = data.get('type', 'unknown')
            strategy_ids = data.get('strategy_ids', [])
            
            logger.info(f"Received collaboration request of type {collaboration_type} from {sender}")
            
            # Evaluate collaboration opportunity
            collaboration_score = self._evaluate_collaboration(sender, strategy_ids)
            
            # Decide whether to collaborate
            if collaboration_score >= self.config['agent_parameters']['collaboration_threshold'] / 100:
                # Accept collaboration
                response_data = {
                    'response': 'accept',
                    'collaboration_type': collaboration_type,
                    'strategy_ids': strategy_ids,
                    'timestamp': int(time.time())
                }
                
                # Add to collaborators if not already
                if sender not in self.state['collaborators']:
                    self.state['collaborators'].append(sender)
                    self._save_state()
                
                logger.info(f"Accepting collaboration request from {sender}")
            else:
                # Reject collaboration
                response_data = {
                    'response': 'reject',
                    'reason': 'collaboration_score_too_low',
                    'score': collaboration_score,
                    'threshold': self.config['agent_parameters']['collaboration_threshold'] / 100,
                    'timestamp': int(time.time())
                }
                
                logger.info(f"Rejecting collaboration request from {sender}")
            
            # Send response
            self._send_message(
                sender,
                'collaboration_response',
                response_data
            )
            
        except Exception as e:
            logger.error(f"Error handling collaboration request: {e}")
    
    def _handle_strategy_proposal(self, sender: str, data: Dict):
        """
        Handle a strategy proposal from another agent
        
        Args:
            sender: Sender address
            data: Message data
        """
        try:
            # Extract proposal details
            strategy_name = data.get('name', 'Unknown Strategy')
            strategy_description = data.get('description', '')
            component_strategy_ids = data.get('component_strategy_ids', [])
            
            logger.info(f"Received strategy proposal '{strategy_name}' from {sender}")
            
            # Evaluate proposal
            evaluation_score = self._evaluate_strategy_proposal(component_strategy_ids)
            
            # Decide whether to participate
            if evaluation_score >= self.config['agent_parameters']['trust_threshold'] / 100:
                # Accept proposal
                response_data = {
                    'response': 'accept',
                    'strategy_name': strategy_name,
                    'evaluation_score': evaluation_score,
                    'timestamp': int(time.time())
                }
                
                logger.info(f"Accepting strategy proposal '{strategy_name}' from {sender}")
                
                # Collaborate on strategy creation
                if sender in self.state['collaborators']:
                    self._collaborate_on_strategy(sender, strategy_name, strategy_description, component_strategy_ids)
            else:
                # Reject proposal
                response_data = {
                    'response': 'reject',
                    'strategy_name': strategy_name,
                    'reason': 'evaluation_score_too_low',
                    'score': evaluation_score,
                    'threshold': self.config['agent_parameters']['trust_threshold'] / 100,
                    'timestamp': int(time.time())
                }
                
                logger.info(f"Rejecting strategy proposal '{strategy_name}' from {sender}")
            
            # Send response
            self._send_message(
                sender,
                'strategy_proposal_response',
                response_data
            )
            
        except Exception as e:
            logger.error(f"Error handling strategy proposal: {e}")
    
    def _handle_zk_proof_request(self, sender: str, data: Dict):
        """
        Handle a ZK proof verification request from another agent
        
        Args:
            sender: Sender address
            data: Message data
        """
        try:
            # Extract request details
            strategy_id = data.get('strategy_id', 0)
            proof_hash = data.get('proof_hash', '')
            
            logger.info(f"Received ZK proof verification request for strategy {strategy_id} from {sender}")
            
            # Verify proof (mock implementation)
            # In a real implementation, this would perform actual ZK proof verification
            is_valid = True  # Mock result
            
            # Submit verification result
            if self.swarm:
                tx = self.swarm.functions.submitZKProof(
                    strategy_id,
                    Web3.to_bytes(hexstr=proof_hash),
                    is_valid
                ).build_transaction({
                    'from': self.account_address,
                    'gas': 200000,
                    'maxFeePerGas': self.web3.to_wei(50, 'gwei'),
                    'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei')
                })
                
                receipt = self._send_transaction(tx)
                
                if receipt and receipt.status == 1:
                    logger.info(f"Successfully submitted ZK proof verification for strategy {strategy_id}")
                    
                    # Send response
                    response_data = {
                        'response': 'verification_submitted',
                        'strategy_id': strategy_id,
                        'proof_hash': proof_hash,
                        'is_valid': is_valid,
                        'timestamp': int(time.time())
                    }
                else:
                    logger.error(f"Failed to submit ZK proof verification for strategy {strategy_id}")
                    
                    # Send response
                    response_data = {
                        'response': 'verification_failed',
                        'strategy_id': strategy_id,
                        'proof_hash': proof_hash,
                        'reason': 'transaction_failed',
                        'timestamp': int(time.time())
                    }
            else:
                logger.warning("Swarm contract not initialized, skipping ZK proof submission")
                
                # Send response
                response_data = {
                    'response': 'verification_failed',
                    'strategy_id': strategy_id,
                    'proof_hash': proof_hash,
                    'reason': 'swarm_contract_not_initialized',
                    'timestamp': int(time.time())
                }
            
            # Send response
            self._send_message(
                sender,
                'zk_proof_response',
                response_data
            )
            
        except Exception as e:
            logger.error(f"Error handling ZK proof request: {e}")
    
    def _handle_marketplace_offer(self, sender: str, data: Dict):
        """
        Handle a marketplace offer from another agent
        
        Args:
            sender: Sender address
            data: Message data
        """
        try:
            # Extract offer details
            strategy_id = data.get('strategy_id', 0)
            price = data.get('price', 0)
            expiration_time = data.get('expiration_time', 0)
            
            logger.info(f"Received marketplace offer for strategy {strategy_id} from {sender}")
            
            # Evaluate offer
            should_purchase = self._evaluate_marketplace_offer(strategy_id, price)
            
            if should_purchase:
                # Purchase execution rights
                if self.swarm:
                    tx = self.swarm.functions.purchaseExecutionRights(
                        strategy_id
                    ).build_transaction({
                        'from': self.account_address,
                        'gas': 300000,
                        'maxFeePerGas': self.web3.to_wei(50, 'gwei'),
                        'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei'),
                        'value': price
                    })
                    
                    receipt = self._send_transaction(tx)
                    
                    if receipt and receipt.status == 1:
                        logger.info(f"Successfully purchased execution rights for strategy {strategy_id}")
                        
                        # Add to owned strategies
                        self.state['owned_strategies'].append({
                            'strategy_id': strategy_id,
                            'purchase_price': price,
                            'purchase_time': int(time.time()),
                            'seller': sender
                        })
                        self._save_state()
                        
                        # Send response
                        response_data = {
                            'response': 'purchase_successful',
                            'strategy_id': strategy_id,
                            'price': price,
                            'timestamp': int(time.time())
                        }
                    else:
                        logger.error(f"Failed to purchase execution rights for strategy {strategy_id}")
                        
                        # Send response
                        response_data = {
                            'response': 'purchase_failed',
                            'strategy_id': strategy_id,
                            'reason': 'transaction_failed',
                            'timestamp': int(time.time())
                        }
                else:
                    logger.warning("Swarm contract not initialized, skipping purchase")
                    
                    # Send response
                    response_data = {
                        'response': 'purchase_failed',
                        'strategy_id': strategy_id,
                        'reason': 'swarm_contract_not_initialized',
                        'timestamp': int(time.time())
                    }
            else:
                # Reject offer
                response_data = {
                    'response': 'offer_rejected',
                    'strategy_id': strategy_id,
                    'reason': 'price_too_high_or_strategy_not_valuable',
                    'timestamp': int(time.time())
                }
                
                logger.info(f"Rejecting marketplace offer for strategy {strategy_id} from {sender}")
            
            # Send response
            self._send_message(
                sender,
                'marketplace_response',
                response_data
            )
            
        except Exception as e:
            logger.error(f"Error handling marketplace offer: {e}")
    
    def _send_message(self, recipient: str, message_type: str, data: Dict) -> bool:
        """
        Send a message to another agent
        
        Args:
            recipient: Recipient address
            message_type: Type of message
            data: Message data
            
        Returns:
            Whether the message was sent successfully
        """
        if not self.swarm:
            logger.warning("Swarm contract not initialized, skipping message send")
            return False
            
        try:
            # Encode message data
            encoded_data = self.web3.to_bytes(text=json.dumps(data))
            
            # Encode message type
            encoded_type = self.web3.to_bytes(text=message_type)
            
            # Send message
            tx = self.swarm.functions.sendMessage(
                recipient,
                encoded_type,
                encoded_data
            ).build_transaction({
                'from': self.account_address,
                'gas': 300000,
                'maxFeePerGas': self.web3.to_wei(50, 'gwei'),
                'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei')
            })
            
            receipt = self._send_transaction(tx)
            
            if receipt and receipt.status == 1:
                logger.info(f"Successfully sent message of type {message_type} to {recipient}")
                return True
            else:
                logger.error(f"Failed to send message of type {message_type} to {recipient}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def _evaluate_collaboration(self, agent_address: str, strategy_ids: List[int]) -> float:
        """
        Evaluate a collaboration opportunity with another agent
        
        Args:
            agent_address: Agent address
            strategy_ids: List of strategy IDs
            
        Returns:
            Collaboration score (0-1)
        """
        try:
            # Get agent details
            agent_details = None
            if self.swarm:
                agent_details = self.swarm.functions.getAgentDetails(agent_address).call()
            
            # Get strategy details
            strategy_details = []
            for strategy_id in strategy_ids:
                if self.incubator:
                    strategy = self.incubator.functions.getStrategy(strategy_id).call()
                    strategy_details.append(strategy)
            
            # Check if agent is already a collaborator
            is_collaborator = agent_address in self.state['collaborators']
            
            # Check agent reputation
            reputation = agent_details[2] if agent_details else 50  # Default to 50 if not available
            
            # Check if we have previous evaluations for this agent
            previous_evaluation = self.state['agent_evaluations'].get(agent_address, 0.5)
            
            # In a real implementation, this would use the collaboration model
            # For now, we'll use a simple heuristic
            
            # Calculate collaboration score
            if is_collaborator:
                # Higher score for existing collaborators
                base_score = 0.7
            else:
                # Base score for new collaborators
                base_score = 0.5
            
            # Adjust based on reputation
            reputation_factor = reputation / 100  # Normalize to 0-1
            
            # Adjust based on previous evaluation
            evaluation_factor = previous_evaluation
            
            # Calculate final score
            collaboration_score = (base_score * 0.4 + reputation_factor * 0.3 + evaluation_factor * 0.3)
            
            # Store evaluation
            self.state['agent_evaluations'][agent_address] = collaboration_score
            self._save_state()
            
            return collaboration_score
            
        except Exception as e:
            logger.error(f"Error evaluating collaboration: {e}")
            return 0.0
    
    def _evaluate_strategy_proposal(self, strategy_ids: List[int]) -> float:
        """
        Evaluate a strategy proposal
        
        Args:
            strategy_ids: List of component strategy IDs
            
        Returns:
            Evaluation score (0-1)
        """
        try:
            # Get strategy details
            strategy_details = []
            for strategy_id in strategy_ids:
                if self.incubator:
                    strategy = self.incubator.functions.getStrategy(strategy_id).call()
                    strategy_details.append(strategy)
                    
                    # Get trust score
                    if self.trust_curve:
                        trust_score = self.trust_curve.functions.getTrustScore(strategy_id).call()
                        
                        # Store evaluation
                        self.state['strategy_evaluations'][str(strategy_id)] = trust_score / 100
            
            # In a real implementation, this would use the evaluation model
            # For now, we'll use a simple heuristic
            
            # Calculate average trust score
            if strategy_details:
                avg_trust_score = sum(self.state['strategy_evaluations'].get(str(s_id), 0.5) for s_id in strategy_ids) / len(strategy_ids)
            else:
                avg_trust_score = 0.5
            
            return avg_trust_score
            
        except Exception as e:
            logger.error(f"Error evaluating strategy proposal: {e}")
            return 0.0
    
    def _collaborate_on_strategy(self, partner: str, name: str, description: str, component_strategy_ids: List[int]):
        """
        Collaborate on strategy creation
        
        Args:
            partner: Partner agent address
            name: Strategy name
            description: Strategy description
            component_strategy_ids: List of component strategy IDs
        """
        if not self.swarm:
            logger.warning("Swarm contract not initialized, skipping collaboration")
            return
            
        try:
            # Create composite strategy
            tx = self.swarm.functions.createCompositeStrategy(
                name,
                description,
                component_strategy_ids
            ).build_transaction({
                'from': self.account_address,
                'gas': 500000,
                'maxFeePerGas': self.web3.to_wei(50, 'gwei'),
                'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei')
            })
            
            receipt = self._send_transaction(tx)
            
            if receipt and receipt.status == 1:
                logger.info(f"Successfully created composite strategy '{name}'")
                
                # Extract composite ID from event logs (mock implementation)
                composite_id = 1  # In a real implementation, extract from logs
                
                # Add to composed strategies
                self.state['composed_strategies'].append({
                    'composite_id': composite_id,
                    'name': name,
                    'description': description,
                    'component_strategy_ids': component_strategy_ids,
                    'partner': partner,
                    'creation_time': int(time.time())
                })
                self._save_state()
                
                # Notify partner
                notification_data = {
                    'notification': 'strategy_created',
                    'composite_id': composite_id,
                    'name': name,
                    'description': description,
                    'component_strategy_ids': component_strategy_ids,
                    'timestamp': int(time.time())
                }
                
                self._send_message(
                    partner,
                    'collaboration_notification',
                    notification_data
                )
            else:
                logger.error(f"Failed to create composite strategy '{name}'")
                
        except Exception as e:
            logger.error(f"Error collaborating on strategy: {e}")
    
    def _evaluate_marketplace_offer(self, strategy_id: int, price: int) -> bool:
        """
        Evaluate a marketplace offer
        
        Args:
            strategy_id: Strategy ID
            price: Price in wei
            
        Returns:
            Whether to purchase the strategy
        """
        try:
            # Check if price is within budget
            if price > self.config['swarm_parameters']['max_strategy_price']:
                logger.info(f"Strategy {strategy_id} price {price} exceeds budget {self.config['swarm_parameters']['max_strategy_price']}")
                return False
            
            # Check if we already own this strategy
            for owned in self.state['owned_strategies']:
                if owned['strategy_id'] == strategy_id:
                    logger.info(f"Already own strategy {strategy_id}")
                    return False
            
            # Get strategy details
            strategy = None
            if self.incubator:
                strategy = self.incubator.functions.getStrategy(strategy_id).call()
            
            # Get trust score
            trust_score = 0
            if self.trust_curve:
                trust_score = self.trust_curve.functions.getTrustScore(strategy_id).call()
            
            # Calculate value
            value = trust_score / 100  # Normalize to 0-1
            
            # Calculate maximum price willing to pay
            max_price = int(value * self.config['swarm_parameters']['max_strategy_price'])
            
            # Decide whether to purchase
            should_purchase = price <= max_price
            
            logger.info(f"Strategy {strategy_id} evaluation: value={value}, max_price={max_price}, offered_price={price}, should_purchase={should_purchase}")
            
            return should_purchase
            
        except Exception as e:
            logger.error(f"Error evaluating marketplace offer: {e}")
            return False
    
    def check_marketplace(self):
        """Check marketplace for interesting strategies"""
        if not self.swarm:
            logger.warning("Swarm contract not initialized, skipping marketplace check")
            return
            
        try:
            # Get all strategies from incubator
            strategy_count = self.incubator.functions.getStrategyCount().call()
            
            # Check each strategy for execution rights
            for strategy_id in range(1, strategy_count + 1):
                # Get execution rights details
                rights = self.swarm.functions.getExecutionRightsDetails(strategy_id).call()
                
                # Check if for sale and not expired
                if rights[3] and rights[2] > int(time.time()):  # isForSale and not expired
                    # Evaluate offer
                    should_purchase = self._evaluate_marketplace_offer(strategy_id, rights[1])
                    
                    if should_purchase:
                        # Purchase execution rights
                        tx = self.swarm.functions.purchaseExecutionRights(
                            strategy_id
                        ).build_transaction({
                            'from': self.account_address,
                            'gas': 300000,
                            'maxFeePerGas': self.web3.to_wei(50, 'gwei'),
                            'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei'),
                            'value': rights[1]
                        })
                        
                        receipt = self._send_transaction(tx)
                        
                        if receipt and receipt.status == 1:
                            logger.info(f"Successfully purchased execution rights for strategy {strategy_id}")
                            
                            # Add to owned strategies
                            self.state['owned_strategies'].append({
                                'strategy_id': strategy_id,
                                'purchase_price': rights[1],
                                'purchase_time': int(time.time()),
                                'seller': rights[0]
                            })
                            self._save_state()
            
            # Update last marketplace check time
            self.state['last_marketplace_check'] = int(time.time())
            self._save_state()
            
        except Exception as e:
            logger.error(f"Error checking marketplace: {e}")
    
    def list_strategy_for_sale(self, strategy_id: int, price: int, duration: int) -> bool:
        """
        List a strategy for sale on the marketplace
        
        Args:
            strategy_id: Strategy ID
            price: Price in wei
            duration: Duration in seconds
            
        Returns:
            Whether the listing was successful
        """
        if not self.swarm:
            logger.warning("Swarm contract not initialized, skipping listing")
            return False
            
        try:
            # Check if we own this strategy
            owns_strategy = False
            for owned in self.state['owned_strategies']:
                if owned['strategy_id'] == strategy_id:
                    owns_strategy = True
                    break
            
            if not owns_strategy:
                # Check if we're the proposer
                strategy = self.incubator.functions.getStrategy(strategy_id).call()
                if strategy[1] != self.account_address:  # proposer
                    logger.warning(f"Not the owner or proposer of strategy {strategy_id}")
                    return False
            
            # List for sale
            tx = self.swarm.functions.listExecutionRights(
                strategy_id,
                price,
                duration
            ).build_transaction({
                'from': self.account_address,
                'gas': 200000,
                'maxFeePerGas': self.web3.to_wei(50, 'gwei'),
                'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei')
            })
            
            receipt = self._send_transaction(tx)
            
            if receipt and receipt.status == 1:
                logger.info(f"Successfully listed strategy {strategy_id} for sale at price {price} for {duration} seconds")
                return True
            else:
                logger.error(f"Failed to list strategy {strategy_id} for sale")
                return False
                
        except Exception as e:
            logger.error(f"Error listing strategy for sale: {e}")
            return False
    
    def find_collaboration_opportunities(self):
        """Find collaboration opportunities with other agents"""
        if not self.swarm:
            logger.warning("Swarm contract not initialized, skipping collaboration search")
            return
            
        try:
            # Get all agents
            agent_addresses = self.swarm.functions.getAllAgents().call()
            
            # Filter out self and existing collaborators
            potential_collaborators = [
                addr for addr in agent_addresses
                if addr != self.account_address and addr not in self.state['collaborators']
            ]
            
            if not potential_collaborators:
                logger.info("No new potential collaborators found")
                return
            
            # Limit to a reasonable number
            max_to_contact = min(len(potential_collaborators), 3)
            
            # Get strategies from incubator
            approved_strategies = self.incubator.functions.getStrategiesByStatus(2).call()  # 2 = Approved
            
            if not approved_strategies:
                logger.info("No approved strategies available for collaboration")
                return
            
            # Select a few strategies to propose
            selected_strategies = approved_strategies[:3]
            
            # Contact potential collaborators
            for i in range(max_to_contact):
                collaborator = potential_collaborators[i]
                
                # Send collaboration request
                request_data = {
                    'type': 'strategy_composition',
                    'strategy_ids': selected_strategies,
                    'timestamp': int(time.time())
                }
                
                success = self._send_message(
                    collaborator,
                    'collaboration_request',
                    request_data
                )
                
                if success:
                    logger.info(f"Sent collaboration request to {collaborator}")
            
            # Update last collaboration check time
            self.state['last_collaboration_check'] = int(time.time())
            self._save_state()
            
        except Exception as e:
            logger.error(f"Error finding collaboration opportunities: {e}")
    
    def execute_owned_strategies(self):
        """Execute strategies owned by this agent"""
        if not self.swarm:
            logger.warning("Swarm contract not initialized, skipping strategy execution")
            return
            
        try:
            # Check each owned strategy
            for owned in self.state['owned_strategies']:
                strategy_id = owned['strategy_id']
                
                # Check if it's a composite strategy
                is_composite = False
                for composed in self.state['composed_strategies']:
                    if composed['composite_id'] == strategy_id:
                        is_composite = True
                        break
                
                if is_composite:
                    # Execute composite strategy
                    tx = self.swarm.functions.executeCompositeStrategy(
                        strategy_id,
                        self.web3.to_bytes(text="")  # Empty data for mock implementation
                    ).build_transaction({
                        'from': self.account_address,
                        'gas': 500000,
                        'maxFeePerGas': self.web3.to_wei(50, 'gwei'),
                        'maxPriorityFeePerGas': self.web3.to_wei(2, 'gwei')
                    })
                else:
                    # Get strategy address from incubator
                    strategy = self.incubator.functions.getStrategy(strategy_id).call()
                    strategy_address = strategy[0]
                    
                    # In a real implementation, this would execute the strategy
                    # For now, we'll just log it
                    logger.info(f"Would execute strategy {strategy_id} at address {strategy_address}")
                    continue
                
                receipt = self._send_transaction(tx)
                
                if receipt and receipt.status == 1:
                    logger.info(f"Successfully executed strategy {strategy_id}")
                else:
                    logger.error(f"Failed to execute strategy {strategy_id}")
                
        except Exception as e:
            logger.error(f"Error executing owned strategies: {e}")
    
    def run(self):
        """Run the agent's main loop"""
        try:
            # Check messages
            if int(time.time()) - self.state['last_message_check'] >= self.config['swarm_parameters']['message_check_interval']:
                logger.info("Checking messages...")
                self.check_messages()
            
            # Check marketplace
            if int(time.time()) - self.state['last_marketplace_check'] >= self.config['swarm_parameters']['marketplace_check_interval']:
                logger.info("Checking marketplace...")
                self.check_marketplace()
            
            # Find collaboration opportunities
            if int(time.time()) - self.state['last_collaboration_check'] >= self.config['swarm_parameters']['collaboration_interval']:
                logger.info("Finding collaboration opportunities...")
                self.find_collaboration_opportunities()
            
            # Execute owned strategies
            logger.info("Executing owned strategies...")
            self.execute_owned_strategies()
            
        except Exception as e:
            logger.error(f"Error in run: {e}")

def main():
    """Main entry point"""
    try:
        # Initialize agent
        agent = SwarmIntelligenceAgent()
        
        # Run agent
        while True:
            agent.run()
            
            # Sleep for a bit
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()
