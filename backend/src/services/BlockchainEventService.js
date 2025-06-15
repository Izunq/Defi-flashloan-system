/**
 * Comprehensive Blockchain Event Listener Service
 * Monitors multiple chains and contracts for events
 */

const { ethers } = require('ethers');
const EventEmitter = require('events');
const logger = require('../utils/logger');
const db = require('../models/db');

// Load contract ABIs
const incubatorABI = require('../../abi/StrategyIncubatorV33.json');
const executorABI = require('../../abi/ArbitrageExecutorV33.json');
const factoryABI = require('../../abi/StrategyFactoryV33.json');
const strategyABI = require('../../abi/GenericStrategy.json');
const proofExecutorABI = require('../../abi/ProofAwareExecutorV35.json');
const trustCurveABI = require('../../abi/TrustCurve.json');

class BlockchainEventService extends EventEmitter {
    constructor() {
        super();
        this.providers = {};
        this.contracts = {};
        this.eventListeners = {};
        this.isInitialized = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 5000; // 5 seconds
        
        // Bind methods
        this.initialize = this.initialize.bind(this);
        this.setupProviders = this.setupProviders.bind(this);
        this.setupContracts = this.setupContracts.bind(this);
        this.setupEventListeners = this.setupEventListeners.bind(this);
        this.handleEvent = this.handleEvent.bind(this);
        this.reconnect = this.reconnect.bind(this);
        this.shutdown = this.shutdown.bind(this);
    }
    
    /**
     * Initialize the blockchain event service
     * @param {Object} config - Configuration object
     */
    async initialize(config) {
        try {
            logger.info('Initializing Blockchain Event Service');
            
            this.config = config;
            
            // Setup providers for each chain
            await this.setupProviders();
            
            // Setup contract instances
            await this.setupContracts();
            
            // Setup event listeners
            await this.setupEventListeners();
            
            this.isInitialized = true;
            this.reconnectAttempts = 0;
            
            logger.info('Blockchain Event Service initialized successfully');
            
            // Setup reconnection on provider disconnect
            Object.keys(this.providers).forEach(chainId => {
                const provider = this.providers[chainId];
                
                provider.on('error', (error) => {
                    logger.error(`Provider error on chain ${chainId}: ${error.message}`);
                    this.reconnect(chainId);
                });
                
                provider.on('disconnect', (code, reason) => {
                    logger.warn(`Provider disconnected on chain ${chainId}: ${reason} (${code})`);
                    this.reconnect(chainId);
                });
            });
            
            return true;
        } catch (error) {
            logger.error(`Failed to initialize Blockchain Event Service: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Setup providers for each chain
     */
    async setupProviders() {
        try {
            const chains = this.config.chains || [];
            
            for (const chain of chains) {
                logger.info(`Setting up provider for chain: ${chain.name} (${chain.chainId})`);
                
                // Create provider
                const provider = new ethers.providers.JsonRpcProvider(chain.rpcUrl);
                
                // Test connection
                const blockNumber = await provider.getBlockNumber();
                logger.info(`Connected to ${chain.name} at block ${blockNumber}`);
                
                // Store provider
                this.providers[chain.chainId] = provider;
            }
            
            logger.info(`Set up providers for ${Object.keys(this.providers).length} chains`);
        } catch (error) {
            logger.error(`Failed to setup providers: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Setup contract instances
     */
    async setupContracts() {
        try {
            this.contracts = {};
            
            // For each chain
            for (const chainId in this.providers) {
                const provider = this.providers[chainId];
                const chain = this.config.chains.find(c => c.chainId.toString() === chainId.toString());
                
                if (!chain) {
                    logger.warn(`No chain configuration found for chainId ${chainId}`);
                    continue;
                }
                
                logger.info(`Setting up contracts for chain: ${chain.name} (${chainId})`);
                
                // Initialize contracts object for this chain
                this.contracts[chainId] = {};
                
                // Setup each contract type
                const contractTypes = [
                    { name: 'incubator', abi: incubatorABI, address: chain.contracts?.incubator },
                    { name: 'executor', abi: executorABI, address: chain.contracts?.executor },
                    { name: 'factory', abi: factoryABI, address: chain.contracts?.factory },
                    { name: 'proofExecutor', abi: proofExecutorABI, address: chain.contracts?.proofExecutor },
                    { name: 'trustCurve', abi: trustCurveABI, address: chain.contracts?.trustCurve }
                ];
                
                for (const contractType of contractTypes) {
                    if (contractType.address) {
                        logger.info(`Setting up ${contractType.name} contract at ${contractType.address}`);
                        this.contracts[chainId][contractType.name] = new ethers.Contract(
                            contractType.address,
                            contractType.abi,
                            provider
                        );
                    } else {
                        logger.warn(`No address provided for ${contractType.name} on chain ${chain.name}`);
                    }
                }
                
                // Setup strategy contracts if available
                if (chain.contracts?.strategies && Array.isArray(chain.contracts.strategies)) {
                    this.contracts[chainId].strategies = [];
                    
                    for (const strategyAddress of chain.contracts.strategies) {
                        logger.info(`Setting up strategy contract at ${strategyAddress}`);
                        const strategyContract = new ethers.Contract(
                            strategyAddress,
                            strategyABI,
                            provider
                        );
                        this.contracts[chainId].strategies.push(strategyContract);
                    }
                    
                    logger.info(`Set up ${this.contracts[chainId].strategies.length} strategy contracts`);
                }
            }
            
            logger.info(`Set up contracts for ${Object.keys(this.contracts).length} chains`);
        } catch (error) {
            logger.error(`Failed to setup contracts: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Setup event listeners for all contracts
     */
    async setupEventListeners() {
        try {
            // Clear existing listeners
            this.removeAllListeners();
            
            // For each chain
            for (const chainId in this.contracts) {
                const chainContracts = this.contracts[chainId];
                const chain = this.config.chains.find(c => c.chainId.toString() === chainId.toString());
                
                if (!chain) {
                    logger.warn(`No chain configuration found for chainId ${chainId}`);
                    continue;
                }
                
                logger.info(`Setting up event listeners for chain: ${chain.name} (${chainId})`);
                
                // Initialize event listeners object for this chain
                if (!this.eventListeners[chainId]) {
                    this.eventListeners[chainId] = {};
                }
                
                // Setup listeners for Incubator contract
                if (chainContracts.incubator) {
                    this.setupContractListeners(
                        chainId,
                        'incubator',
                        chainContracts.incubator,
                        [
                            'StrategyProposed',
                            'StrategyApproved',
                            'StrategyRejected',
                            'StrategyDeployed',
                            'StrategyRetired'
                        ]
                    );
                }
                
                // Setup listeners for Executor contract
                if (chainContracts.executor) {
                    this.setupContractListeners(
                        chainId,
                        'executor',
                        chainContracts.executor,
                        [
                            'ArbitrageExecuted',
                            'ProfitGenerated',
                            'ExecutionFailed',
                            'FundsDeposited',
                            'FundsWithdrawn'
                        ]
                    );
                }
                
                // Setup listeners for Factory contract
                if (chainContracts.factory) {
                    this.setupContractListeners(
                        chainId,
                        'factory',
                        chainContracts.factory,
                        [
                            'StrategyCreated',
                            'StrategyUpdated',
                            'StrategyRemoved'
                        ]
                    );
                }
                
                // Setup listeners for ProofExecutor contract
                if (chainContracts.proofExecutor) {
                    this.setupContractListeners(
                        chainId,
                        'proofExecutor',
                        chainContracts.proofExecutor,
                        [
                            'ProofSubmitted',
                            'ProofVerified',
                            'ProofRejected',
                            'ArbitrageWithProofExecuted'
                        ]
                    );
                }
                
                // Setup listeners for TrustCurve contract
                if (chainContracts.trustCurve) {
                    this.setupContractListeners(
                        chainId,
                        'trustCurve',
                        chainContracts.trustCurve,
                        [
                            'TrustScoreUpdated',
                            'StrategyTrusted',
                            'StrategyUntrusted'
                        ]
                    );
                }
                
                // Setup listeners for Strategy contracts
                if (chainContracts.strategies && chainContracts.strategies.length > 0) {
                    for (let i = 0; i < chainContracts.strategies.length; i++) {
                        const strategyContract = chainContracts.strategies[i];
                        
                        this.setupContractListeners(
                            chainId,
                            `strategy_${i}`,
                            strategyContract,
                            [
                                'StrategyExecuted',
                                'ParametersUpdated',
                                'StatusChanged'
                            ]
                        );
                    }
                }
            }
            
            logger.info('Event listeners setup completed');
        } catch (error) {
            logger.error(`Failed to setup event listeners: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Setup listeners for a specific contract
     * @param {string} chainId - Chain ID
     * @param {string} contractName - Contract name
     * @param {ethers.Contract} contract - Contract instance
     * @param {string[]} eventNames - Event names to listen for
     */
    setupContractListeners(chainId, contractName, contract, eventNames) {
        try {
            // Initialize contract listeners
            if (!this.eventListeners[chainId][contractName]) {
                this.eventListeners[chainId][contractName] = {};
            }
            
            // Setup listeners for each event
            for (const eventName of eventNames) {
                logger.info(`Setting up listener for ${contractName}.${eventName} on chain ${chainId}`);
                
                // Create listener function
                const listener = (...args) => {
                    this.handleEvent(chainId, contractName, eventName, args);
                };
                
                // Register listener
                contract.on(eventName, listener);
                
                // Store listener reference
                this.eventListeners[chainId][contractName][eventName] = listener;
            }
            
            logger.info(`Set up ${eventNames.length} listeners for ${contractName} on chain ${chainId}`);
        } catch (error) {
            logger.error(`Failed to setup listeners for ${contractName}: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Handle blockchain event
     * @param {string} chainId - Chain ID
     * @param {string} contractName - Contract name
     * @param {string} eventName - Event name
     * @param {Array} args - Event arguments
     */
    async handleEvent(chainId, contractName, eventName, args) {
        try {
            const chain = this.config.chains.find(c => c.chainId.toString() === chainId.toString());
            const chainName = chain ? chain.name : chainId;
            
            logger.info(`Event received: ${contractName}.${eventName} on ${chainName}`);
            
            // Extract event data
            const eventData = {
                chainId,
                chainName,
                contractName,
                eventName,
                args,
                timestamp: new Date().toISOString()
            };
            
            // Store event in database
            await this.storeEvent(eventData);
            
            // Emit event for other services to consume
            this.emit('blockchain:event', eventData);
            this.emit(`blockchain:${chainId}:${contractName}:${eventName}`, eventData);
            
            // Handle specific events
            switch (eventName) {
                case 'StrategyProposed':
                    await this.handleStrategyProposed(chainId, args);
                    break;
                case 'StrategyDeployed':
                    await this.handleStrategyDeployed(chainId, args);
                    break;
                case 'ArbitrageExecuted':
                    await this.handleArbitrageExecuted(chainId, args);
                    break;
                case 'ProfitGenerated':
                    await this.handleProfitGenerated(chainId, args);
                    break;
                case 'ProofVerified':
                    await this.handleProofVerified(chainId, args);
                    break;
                default:
                    // No special handling for other events
                    break;
            }
        } catch (error) {
            logger.error(`Failed to handle event ${contractName}.${eventName}: ${error.message}`);
        }
    }
    
    /**
     * Store event in database
     * @param {Object} eventData - Event data
     */
    async storeEvent(eventData) {
        try {
            // Store in database
            await db.collection('blockchain_events').insertOne({
                ...eventData,
                createdAt: new Date()
            });
            
            logger.debug(`Stored event in database: ${eventData.contractName}.${eventData.eventName}`);
        } catch (error) {
            logger.error(`Failed to store event in database: ${error.message}`);
        }
    }
    
    /**
     * Handle StrategyProposed event
     * @param {string} chainId - Chain ID
     * @param {Array} args - Event arguments
     */
    async handleStrategyProposed(chainId, args) {
        try {
            const [proposer, strategyId, name, description] = args;
            
            logger.info(`Strategy proposed: ${name} (ID: ${strategyId}) by ${proposer}`);
            
            // Store strategy in database
            await db.collection('strategies').updateOne(
                { chainId, strategyId: strategyId.toString() },
                {
                    $set: {
                        chainId,
                        strategyId: strategyId.toString(),
                        name,
                        description,
                        proposer,
                        status: 'proposed',
                        updatedAt: new Date()
                    },
                    $setOnInsert: {
                        createdAt: new Date()
                    }
                },
                { upsert: true }
            );
            
            // Notify other services
            this.emit('strategy:proposed', {
                chainId,
                strategyId: strategyId.toString(),
                name,
                description,
                proposer
            });
        } catch (error) {
            logger.error(`Failed to handle StrategyProposed event: ${error.message}`);
        }
    }
    
    /**
     * Handle StrategyDeployed event
     * @param {string} chainId - Chain ID
     * @param {Array} args - Event arguments
     */
    async handleStrategyDeployed(chainId, args) {
        try {
            const [strategyId, strategyAddress, deployer] = args;
            
            logger.info(`Strategy deployed: ID ${strategyId} at ${strategyAddress} by ${deployer}`);
            
            // Update strategy in database
            await db.collection('strategies').updateOne(
                { chainId, strategyId: strategyId.toString() },
                {
                    $set: {
                        address: strategyAddress,
                        deployer,
                        status: 'deployed',
                        deployedAt: new Date(),
                        updatedAt: new Date()
                    }
                }
            );
            
            // Add strategy contract to listeners
            const chain = this.config.chains.find(c => c.chainId.toString() === chainId.toString());
            if (chain) {
                const provider = this.providers[chainId];
                
                // Create contract instance
                const strategyContract = new ethers.Contract(
                    strategyAddress,
                    strategyABI,
                    provider
                );
                
                // Add to contracts list
                if (!this.contracts[chainId].strategies) {
                    this.contracts[chainId].strategies = [];
                }
                this.contracts[chainId].strategies.push(strategyContract);
                
                // Setup listeners
                const strategyIndex = this.contracts[chainId].strategies.length - 1;
                this.setupContractListeners(
                    chainId,
                    `strategy_${strategyIndex}`,
                    strategyContract,
                    [
                        'StrategyExecuted',
                        'ParametersUpdated',
                        'StatusChanged'
                    ]
                );
                
                logger.info(`Added listeners for new strategy at ${strategyAddress}`);
            }
            
            // Notify other services
            this.emit('strategy:deployed', {
                chainId,
                strategyId: strategyId.toString(),
                address: strategyAddress,
                deployer
            });
        } catch (error) {
            logger.error(`Failed to handle StrategyDeployed event: ${error.message}`);
        }
    }
    
    /**
     * Handle ArbitrageExecuted event
     * @param {string} chainId - Chain ID
     * @param {Array} args - Event arguments
     */
    async handleArbitrageExecuted(chainId, args) {
        try {
            const [executor, strategyAddress, profitAmount, tokenAddress] = args;
            
            logger.info(`Arbitrage executed by ${executor} using strategy ${strategyAddress}`);
            logger.info(`Profit: ${ethers.utils.formatEther(profitAmount)} of token ${tokenAddress}`);
            
            // Store execution in database
            await db.collection('executions').insertOne({
                chainId,
                executor,
                strategyAddress,
                profitAmount: profitAmount.toString(),
                tokenAddress,
                timestamp: new Date()
            });
            
            // Notify other services
            this.emit('arbitrage:executed', {
                chainId,
                executor,
                strategyAddress,
                profitAmount: profitAmount.toString(),
                tokenAddress
            });
        } catch (error) {
            logger.error(`Failed to handle ArbitrageExecuted event: ${error.message}`);
        }
    }
    
    /**
     * Handle ProfitGenerated event
     * @param {string} chainId - Chain ID
     * @param {Array} args - Event arguments
     */
    async handleProfitGenerated(chainId, args) {
        try {
            const [strategyAddress, profitAmount, tokenAddress] = args;
            
            logger.info(`Profit generated by strategy ${strategyAddress}`);
            logger.info(`Amount: ${ethers.utils.formatEther(profitAmount)} of token ${tokenAddress}`);
            
            // Store profit in database
            await db.collection('profits').insertOne({
                chainId,
                strategyAddress,
                profitAmount: profitAmount.toString(),
                tokenAddress,
                timestamp: new Date()
            });
            
            // Update strategy stats
            await db.collection('strategy_stats').updateOne(
                { chainId, strategyAddress },
                {
                    $inc: {
                        totalProfits: parseFloat(ethers.utils.formatEther(profitAmount)),
                        executionCount: 1
                    },
                    $set: {
                        lastProfit: parseFloat(ethers.utils.formatEther(profitAmount)),
                        lastProfitAt: new Date(),
                        updatedAt: new Date()
                    },
                    $setOnInsert: {
                        createdAt: new Date()
                    }
                },
                { upsert: true }
            );
            
            // Notify other services
            this.emit('profit:generated', {
                chainId,
                strategyAddress,
                profitAmount: profitAmount.toString(),
                tokenAddress
            });
        } catch (error) {
            logger.error(`Failed to handle ProfitGenerated event: ${error.message}`);
        }
    }
    
    /**
     * Handle ProofVerified event
     * @param {string} chainId - Chain ID
     * @param {Array} args - Event arguments
     */
    async handleProofVerified(chainId, args) {
        try {
            const [proofId, verifier, strategyAddress] = args;
            
            logger.info(`Proof ${proofId} verified by ${verifier} for strategy ${strategyAddress}`);
            
            // Store proof verification in database
            await db.collection('proofs').updateOne(
                { chainId, proofId: proofId.toString() },
                {
                    $set: {
                        verifier,
                        strategyAddress,
                        status: 'verified',
                        verifiedAt: new Date(),
                        updatedAt: new Date()
                    },
                    $setOnInsert: {
                        createdAt: new Date()
                    }
                },
                { upsert: true }
            );
            
            // Notify other services
            this.emit('proof:verified', {
                chainId,
                proofId: proofId.toString(),
                verifier,
                strategyAddress
            });
        } catch (error) {
            logger.error(`Failed to handle ProofVerified event: ${error.message}`);
        }
    }
    
    /**
     * Reconnect to a chain
     * @param {string} chainId - Chain ID
     */
    async reconnect(chainId) {
        try {
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                logger.error(`Maximum reconnect attempts (${this.maxReconnectAttempts}) reached for chain ${chainId}`);
                return;
            }
            
            this.reconnectAttempts++;
            
            logger.info(`Attempting to reconnect to chain ${chainId} (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            // Wait before reconnecting
            await new Promise(resolve => setTimeout(resolve, this.reconnectDelay));
            
            // Find chain config
            const chain = this.config.chains.find(c => c.chainId.toString() === chainId.toString());
            
            if (!chain) {
                logger.error(`No chain configuration found for chainId ${chainId}`);
                return;
            }
            
            // Create new provider
            const provider = new ethers.providers.JsonRpcProvider(chain.rpcUrl);
            
            // Test connection
            const blockNumber = await provider.getBlockNumber();
            logger.info(`Reconnected to ${chain.name} at block ${blockNumber}`);
            
            // Replace provider
            this.providers[chainId] = provider;
            
            // Recreate contracts
            await this.setupContracts();
            
            // Recreate event listeners
            await this.setupEventListeners();
            
            // Reset reconnect attempts on success
            this.reconnectAttempts = 0;
            
            logger.info(`Successfully reconnected to chain ${chainId}`);
        } catch (error) {
            logger.error(`Failed to reconnect to chain ${chainId}: ${error.message}`);
            
            // Try again with exponential backoff
            this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 60000); // Max 1 minute
            setTimeout(() => this.reconnect(chainId), this.reconnectDelay);
        }
    }
    
    /**
     * Shutdown the service
     */
    async shutdown() {
        logger.info('Shutting down Blockchain Event Service');
        
        // Remove all listeners
        for (const chainId in this.eventListeners) {
            for (const contractName in this.eventListeners[chainId]) {
                for (const eventName in this.eventListeners[chainId][contractName]) {
                    const listener = this.eventListeners[chainId][contractName][eventName];
                    const contract = this.contracts[chainId][contractName];
                    
                    if (contract && contract.removeListener) {
                        contract.removeListener(eventName, listener);
                    }
                }
            }
        }
        
        // Clear providers
        this.providers = {};
        this.contracts = {};
        this.eventListeners = {};
        this.isInitialized = false;
        
        logger.info('Blockchain Event Service shut down successfully');
    }
}

// Export singleton instance
module.exports = new BlockchainEventService();