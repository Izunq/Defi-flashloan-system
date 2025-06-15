const { ethers } = require('ethers');
const axios = require('axios');
const crypto = require('crypto');
const ZKProofModel = require('../models/ZKProofModel');
const { SecretManagerServiceClient } = require('@google-cloud/secret-manager');

/**
 * Service for ZK Proof data with enhanced security
 */
class ZKProofService {
  constructor() {
    // Initialize provider with fallback mechanism
    this.initializeProvider();
    
    // Initialize database model
    this.zkModel = new ZKProofModel();
    
    // Initialize Python agent URL with environment variable
    this.pythonAgentUrl = process.env.PYTHON_AGENT_URL || 'http://localhost:5000';
    
    // Initialize secret manager for secure key management
    this.secretManager = new SecretManagerServiceClient();
    
    // Initialize contract instances
    this.initializeContracts();
    
    // Rate limiting
    this.requestCounts = {};
    this.rateLimitWindow = 60 * 1000; // 1 minute
    this.rateLimitMax = 10; // 10 requests per minute
    
    // Clean up rate limiting data periodically
    setInterval(() => this.cleanupRateLimitData(), 5 * 60 * 1000); // Every 5 minutes
  }

  /**
   * Initialize provider with fallback mechanism
   */
  async initializeProvider() {
    try {
      // Primary provider
      this.provider = new ethers.providers.JsonRpcProvider(process.env.RPC_URL);
      
      // Fallback providers
      this.fallbackProviders = [];
      if (process.env.FALLBACK_RPC_URL_1) {
        this.fallbackProviders.push(new ethers.providers.JsonRpcProvider(process.env.FALLBACK_RPC_URL_1));
      }
      if (process.env.FALLBACK_RPC_URL_2) {
        this.fallbackProviders.push(new ethers.providers.JsonRpcProvider(process.env.FALLBACK_RPC_URL_2));
      }
      
      // Test primary provider
      await this.provider.getBlockNumber();
      console.log('Primary provider connected successfully');
    } catch (error) {
      console.error('Error initializing primary provider:', error);
      
      // Try fallback providers
      for (const fallbackProvider of this.fallbackProviders) {
        try {
          await fallbackProvider.getBlockNumber();
          console.log('Fallback provider connected successfully');
          this.provider = fallbackProvider;
          break;
        } catch (fallbackError) {
          console.error('Error initializing fallback provider:', fallbackError);
        }
      }
    }
  }

  /**
   * Initialize contract instances
   */
  async initializeContracts() {
    try {
      if (process.env.TRUST_CURVE_ADDRESS) {
        const trustCurveAbi = require('../../abi/TrustCurve.json');
        this.trustCurve = new ethers.Contract(
          process.env.TRUST_CURVE_ADDRESS,
          trustCurveAbi,
          this.provider
        );
      }

      if (process.env.PROOF_EXECUTOR_ADDRESS) {
        const executorAbi = require('../../abi/ProofAwareExecutorV35.json');
        this.executor = new ethers.Contract(
          process.env.PROOF_EXECUTOR_ADDRESS,
          executorAbi,
          this.provider
        );
      }
      
      if (process.env.ZK_VERIFIER_ADDRESS) {
        const verifierAbi = require('../../abi/ZKVerifier.json');
        this.zkVerifier = new ethers.Contract(
          process.env.ZK_VERIFIER_ADDRESS,
          verifierAbi,
          this.provider
        );
      }
    } catch (error) {
      console.error('Error initializing contracts:', error);
    }
  }

  /**
   * Apply rate limiting
   * @param {string} ip - IP address
   * @returns {boolean} - Whether the request is allowed
   */
  applyRateLimit(ip) {
    const now = Date.now();
    
    if (!this.requestCounts[ip]) {
      this.requestCounts[ip] = {
        count: 1,
        firstRequest: now
      };
      return true;
    }
    
    const windowStart = now - this.rateLimitWindow;
    
    if (this.requestCounts[ip].firstRequest < windowStart) {
      // Reset window
      this.requestCounts[ip] = {
        count: 1,
        firstRequest: now
      };
      return true;
    }
    
    if (this.requestCounts[ip].count >= this.rateLimitMax) {
      return false;
    }
    
    this.requestCounts[ip].count++;
    return true;
  }
  
  /**
   * Clean up rate limiting data
   */
  cleanupRateLimitData() {
    const now = Date.now();
    const windowStart = now - this.rateLimitWindow;
    
    for (const ip in this.requestCounts) {
      if (this.requestCounts[ip].firstRequest < windowStart) {
        delete this.requestCounts[ip];
      }
    }
  }

  /**
   * Get latest ZK proofs
   * @param {string} ip - IP address for rate limiting
   * @returns {Promise<Array>} Array of ZK proofs
   */
  async getLatestProofs(ip) {
    // Apply rate limiting
    if (!this.applyRateLimit(ip)) {
      throw new Error('Rate limit exceeded');
    }
    
    try {
      // Try to get proofs from Python agent
      const response = await axios.get(`${this.pythonAgentUrl}/api/proofs`, {
        timeout: 5000 // 5 second timeout
      });
      const proofs = response.data;
      
      // Enrich proofs with on-chain data
      const enrichedProofs = await this.enrichProofsWithOnChainData(proofs);
      
      // Store proofs in database
      await this.zkModel.storeProofs(enrichedProofs);
      
      return enrichedProofs;
    } catch (error) {
      console.error('Error fetching proofs from Python agent:', error);
      
      // Fall back to database if Python agent is unavailable
      return this.zkModel.getLatestProofs();
    }
  }

  /**
   * Enrich proofs with on-chain data
   * @param {Array} proofs - Array of ZK proofs
   * @returns {Promise<Array>} Enriched proofs
   */
  async enrichProofsWithOnChainData(proofs) {
    if (!this.trustCurve || !this.executor) {
      return proofs;
    }

    const enrichedProofs = [];

    for (const proof of proofs) {
      try {
        // Get strategy address from executor
        const strategyAddress = await this.executor.getStrategyAddress(proof.strategyId);
        
        if (strategyAddress !== ethers.constants.AddressZero) {
          // Get strategy scorecard from TrustCurve
          const scorecard = await this.trustCurve.getStrategyScorecard(proof.strategyId);
          
          // Get strategy info from AIStrategyV35 contract
          const strategyAbi = require('../../abi/AIStrategyV35.json');
          const strategy = new ethers.Contract(strategyAddress, strategyAbi, this.provider);
          
          const strategyInfo = await strategy.getStrategyInfo();
          const zkProofStatus = await strategy.getZKProofStatus();
          
          // Enrich proof with on-chain data
          enrichedProofs.push({
            ...proof,
            strategyName: strategyInfo._name || proof.strategyName,
            strategyAddress,
            lastVerifiedAt: new Date(scorecard.lastVerifiedAt.toNumber() * 1000),
            onChainVerification: {
              isValid: scorecard.lastVerifiedAt.toNumber() > 0,
              timestamp: scorecard.lastVerifiedAt.toNumber(),
              totalProfitVerified: ethers.utils.formatEther(scorecard.totalProfitVerified),
              winRate: scorecard.winRate
            },
            zkProofStatus: {
              proofHash: zkProofStatus._proofHash,
              timestamp: zkProofStatus._timestamp.toNumber(),
              verified: zkProofStatus._verified,
              verifier: zkProofStatus._verifier,
              expirationTime: zkProofStatus._expirationTime.toNumber(),
              isValid: zkProofStatus._isValid
            }
          });
        } else {
          enrichedProofs.push(proof);
        }
      } catch (error) {
        console.error(`Error enriching proof for strategy ${proof.strategyId}:`, error);
        enrichedProofs.push(proof);
      }
    }

    return enrichedProofs;
  }

  /**
   * Get proof by strategy ID
   * @param {string} strategyId - Strategy ID
   * @param {string} ip - IP address for rate limiting
   * @returns {Promise<Object>} Proof data
   */
  async getProofByStrategyId(strategyId, ip) {
    // Apply rate limiting
    if (!this.applyRateLimit(ip)) {
      throw new Error('Rate limit exceeded');
    }
    
    try {
      // Check if proof exists in database
      const storedProof = await this.zkModel.getProofByStrategyId(strategyId);
      
      if (storedProof) {
        // Refresh on-chain data
        return this.refreshProofOnChainData(storedProof);
      }
      
      // If not in database, fetch from Python agent
      const response = await axios.get(`${this.pythonAgentUrl}/api/proof/${strategyId}`, {
        timeout: 5000 // 5 second timeout
      });
      const proof = response.data;
      
      // Enrich with on-chain data
      const enrichedProof = await this.refreshProofOnChainData(proof);
      
      // Store in database
      await this.zkModel.storeProof(enrichedProof);
      
      return enrichedProof;
    } catch (error) {
      console.error(`Error fetching proof for strategy ${strategyId}:`, error);
      throw error;
    }
  }

  /**
   * Refresh proof on-chain data
   * @param {Object} proof - Proof data
   * @returns {Promise<Object>} Updated proof data
   */
  async refreshProofOnChainData(proof) {
    if (!this.trustCurve || !this.executor) {
      return proof;
    }

    try {
      // Get strategy address from executor
      const strategyAddress = await this.executor.getStrategyAddress(proof.strategyId);
      
      if (strategyAddress !== ethers.constants.AddressZero) {
        // Get strategy scorecard from TrustCurve
        const scorecard = await this.trustCurve.getStrategyScorecard(proof.strategyId);
        
        // Get strategy info from AIStrategyV35 contract
        const strategyAbi = require('../../abi/AIStrategyV35.json');
        const strategy = new ethers.Contract(strategyAddress, strategyAbi, this.provider);
        
        const strategyInfo = await strategy.getStrategyInfo();
        const zkProofStatus = await strategy.getZKProofStatus();
        
        // Update proof with on-chain data
        return {
          ...proof,
          strategyName: strategyInfo._name || proof.strategyName,
          strategyAddress,
          lastVerifiedAt: new Date(scorecard.lastVerifiedAt.toNumber() * 1000),
          onChainVerification: {
            isValid: scorecard.lastVerifiedAt.toNumber() > 0,
            timestamp: scorecard.lastVerifiedAt.toNumber(),
            totalProfitVerified: ethers.utils.formatEther(scorecard.totalProfitVerified),
            winRate: scorecard.winRate
          },
          zkProofStatus: {
            proofHash: zkProofStatus._proofHash,
            timestamp: zkProofStatus._timestamp.toNumber(),
            verified: zkProofStatus._verified,
            verifier: zkProofStatus._verifier,
            expirationTime: zkProofStatus._expirationTime.toNumber(),
            isValid: zkProofStatus._isValid
          }
        };
      }
    } catch (error) {
      console.error(`Error refreshing on-chain data for proof of strategy ${proof.strategyId}:`, error);
    }
    
    return proof;
  }

  /**
   * Get private key securely from secret manager
   * @returns {Promise<string>} Private key
   */  async getPrivateKey() {
    // SECURITY: This method has been disabled to prevent private key exposure
    throw new Error('SECURITY ERROR: Direct private key access is prohibited. Use secure key management.');
    
    // The following code has been disabled for security reasons:
    /*
    try {
      const name = `projects/${process.env.GCP_PROJECT_ID}/secrets/${process.env.SECURE_KEY_SECRET_NAME}/versions/latest`;
      const [version] = await this.secretManager.accessSecretVersion({ name });
      return version.payload.data.toString();
    } catch (error) {
      console.error('Error accessing secret:', error);
      
      // Fallback to environment variable if secret manager fails
      if (process.env.SECURE_KEY) {
        return process.env.SECURE_KEY;
      }
      
      throw new Error('Failed to retrieve secure key');
    }
    */
  }

  /**
   * Verify a ZK proof cryptographically
   * @param {Array} publicInputs - Public inputs for the proof
   * @param {string} proof - The proof data
   * @returns {Promise<boolean>} Whether the proof is valid
   */
  async verifyProofCryptographically(publicInputs, proof) {
    if (!this.zkVerifier) {
      throw new Error('ZK Verifier contract not initialized');
    }
    
    try {
      // Verify the proof using the ZK verifier contract
      const isValid = await this.zkVerifier.verifyProof(publicInputs, proof);
      return isValid;
    } catch (error) {
      console.error('Error verifying proof cryptographically:', error);
      return false;
    }
  }

  /**
   * Verify a ZK proof on-chain
   * @param {string} strategyId - Strategy ID
   * @param {Array} publicInputs - Public inputs for the proof
   * @param {string} proof - The proof data
   * @param {string} ip - IP address for rate limiting
   * @returns {Promise<Object>} Verification result
   */
  async verifyProof(strategyId, publicInputs, proof, ip) {
    // Apply rate limiting
    if (!this.applyRateLimit(ip)) {
      throw new Error('Rate limit exceeded');
    }
    
    if (!this.executor) {
      throw new Error('Executor contract not initialized');
    }

    try {
      // First verify the proof cryptographically
      const isProofValid = await this.verifyProofCryptographically(publicInputs, proof);
      
      if (!isProofValid) {
        throw new Error('Proof is not cryptographically valid');
      }
      
      // Get strategy address from executor
      const strategyAddress = await this.executor.getStrategyAddress(strategyId);
      
      if (strategyAddress === ethers.constants.AddressZero) {
        throw new Error(`Strategy ${strategyId} not found`);
      }
      
      // Get wallet from private key
      // const privateKey = await this.getPrivateKey();
      // SECURITY: Direct private key usage disabled
throw new Error('SECURITY ERROR: Direct private key usage is prohibited. Use secure key management.');
// const wallet = new ethers.Wallet(secureKey, this.provider);
      
      // Connect strategy contract with wallet
      const strategyAbi = require('../../abi/AIStrategyV35.json');
      const strategy = new ethers.Contract(strategyAddress, strategyAbi, this.provider);
      // const strategyWithSigner = strategy.connect(wallet);
      
      // Submit the proof first
      const submitTx = await strategyWithSigner.submitZKProof(publicInputs, proof);
      await submitTx.wait();
      
      // Generate proof hash
      const proofHash = ethers.utils.keccak256(
        ethers.utils.defaultAbiCoder.encode(
          ['uint256[]', 'bytes'],
          [publicInputs, proof]
        )
      );
      
      // Verify the proof
      const tx = await strategyWithSigner.verifyZKProof(publicInputs, proof);
      
      // Wait for transaction to be mined
      const receipt = await tx.wait();
      
      // Parse logs for verification result
      const verificationEvent = receipt.events.find(e => e.event === 'ZKProofVerified');
      
      if (verificationEvent) {
        const [strategyIdEvent, proofHashEvent, verifiedEvent, verifierEvent] = verificationEvent.args;
        
        // Store verification result in database
        const verificationResult = {
          transactionHash: receipt.transactionHash,
          strategyId: strategyIdEvent.toString(),
          proofHash: proofHashEvent,
          isValid: verifiedEvent,
          verifier: verifierEvent,
          timestamp: Math.floor(Date.now() / 1000)
        };
        
        await this.zkModel.storeVerification(verificationResult);
        
        return verificationResult;
      }
      
      return {
        transactionHash: receipt.transactionHash,
        strategyId,
        proofHash,
        success: false,
        message: 'Verification event not found in transaction logs'
      };
    } catch (error) {
      console.error(`Error verifying proof for strategy ${strategyId}:`, error);
      throw error;
    }
  }

  /**
   * Submit a new ZK proof
   * @param {string} strategyId - Strategy ID
   * @param {Array} publicInputs - Public inputs for the proof
   * @param {string} proof - The proof data
   * @param {string} ip - IP address for rate limiting
   * @returns {Promise<Object>} Submission result
   */
  async submitProof(strategyId, publicInputs, proof, ip) {
    // Apply rate limiting
    if (!this.applyRateLimit(ip)) {
      throw new Error('Rate limit exceeded');
    }
    
    if (!this.executor) {
      throw new Error('Executor contract not initialized');
    }

    try {
      // First verify the proof cryptographically
      const isProofValid = await this.verifyProofCryptographically(publicInputs, proof);
      
      if (!isProofValid) {
        throw new Error('Proof is not cryptographically valid');
      }
      
      // Get strategy address from executor
      const strategyAddress = await this.executor.getStrategyAddress(strategyId);
      
      if (strategyAddress === ethers.constants.AddressZero) {
        throw new Error(`Strategy ${strategyId} not found`);
      }
      
      // Get wallet from private key
      // const privateKey = await this.getPrivateKey();
      // SECURITY: Direct private key usage disabled
throw new Error('SECURITY ERROR: Direct private key usage is prohibited. Use secure key management.');
// const wallet = new ethers.Wallet(secureKey, this.provider);
      
      // Connect strategy contract with wallet
      const strategyAbi = require('../../abi/AIStrategyV35.json');
      const strategy = new ethers.Contract(strategyAddress, strategyAbi, this.provider);
      // const strategyWithSigner = strategy.connect(wallet);
      
      // Submit proof
      const tx = await strategyWithSigner.submitZKProof(publicInputs, proof);
      
      // Wait for transaction to be mined
      const receipt = await tx.wait();
      
      // Parse logs for submission result
      const submissionEvent = receipt.events.find(e => e.event === 'ZKProofSubmitted');
      
      if (submissionEvent) {
        const [strategyIdEvent, proofHashEvent, timestampEvent, expirationTimeEvent] = submissionEvent.args;
        
        // Store submission result in database
        const submissionResult = {
          transactionHash: receipt.transactionHash,
          strategyId: strategyIdEvent.toString(),
          proofHash: proofHashEvent,
          timestamp: timestampEvent.toNumber(),
          expirationTime: expirationTimeEvent.toNumber()
        };
        
        await this.zkModel.storeSubmission(submissionResult);
        
        return submissionResult;
      }
      
      return {
        transactionHash: receipt.transactionHash,
        strategyId,
        success: false,
        message: 'Submission event not found in transaction logs'
      };
    } catch (error) {
      console.error(`Error submitting proof for strategy ${strategyId}:`, error);
      throw error;
    }
  }
  
  /**
   * Get verification history for a strategy
   * @param {string} strategyId - Strategy ID
   * @param {string} ip - IP address for rate limiting
   * @returns {Promise<Array>} Verification history
   */
  async getVerificationHistory(strategyId, ip) {
    // Apply rate limiting
    if (!this.applyRateLimit(ip)) {
      throw new Error('Rate limit exceeded');
    }
    
    try {
      return await this.zkModel.getVerificationHistory(strategyId);
    } catch (error) {
      console.error(`Error fetching verification history for strategy ${strategyId}:`, error);
      throw error;
    }
  }
  
  /**
   * Get submission history for a strategy
   * @param {string} strategyId - Strategy ID
   * @param {string} ip - IP address for rate limiting
   * @returns {Promise<Array>} Submission history
   */
  async getSubmissionHistory(strategyId, ip) {
    // Apply rate limiting
    if (!this.applyRateLimit(ip)) {
      throw new Error('Rate limit exceeded');
    }
    
    try {
      return await this.zkModel.getSubmissionHistory(strategyId);
    } catch (error) {
      console.error(`Error fetching submission history for strategy ${strategyId}:`, error);
      throw error;
    }
  }
}

module.exports = ZKProofService;