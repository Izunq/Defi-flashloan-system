const { ethers } = require('ethers');
const axios = require('axios');
const AIStrategyModel = require('../models/AIStrategyModel');

/**
 * Service for AI Strategy data
 */
class AIStrategyService {
  constructor() {
    this.provider = new ethers.providers.JsonRpcProvider(process.env.RPC_URL);
    this.aiModel = new AIStrategyModel();
    this.pythonAgentUrl = process.env.PYTHON_AGENT_URL || 'http://localhost:5000';
    
    // Initialize contract instances
    this.initializeContracts();
  }

  /**
   * Initialize contract instances
   */
  initializeContracts() {
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
    } catch (error) {
      console.error('Error initializing contracts:', error);
    }
  }

  /**
   * Get latest AI insights from Python agent
   * @returns {Promise<Array>} Array of AI insights
   */
  async getLatestInsights() {
    try {
      // Try to get insights from Python agent
      const response = await axios.get(`${this.pythonAgentUrl}/api/insights`);
      const insights = response.data;
      
      // Enrich insights with on-chain data
      const enrichedInsights = await this.enrichInsightsWithOnChainData(insights);
      
      // Store insights in database
      await this.aiModel.storeInsights(enrichedInsights);
      
      return enrichedInsights;
    } catch (error) {
      console.error('Error fetching insights from Python agent:', error);
      
      // Fall back to database if Python agent is unavailable
      return this.aiModel.getLatestInsights();
    }
  }

  /**
   * Enrich insights with on-chain data
   * @param {Array} insights - Array of AI insights
   * @returns {Promise<Array>} Enriched insights
   */
  async enrichInsightsWithOnChainData(insights) {
    if (!this.trustCurve || !this.executor) {
      return insights;
    }

    const enrichedInsights = [];

    for (const insight of insights) {
      try {
        // Get strategy address from executor
        const strategyAddress = await this.executor.getStrategyAddress(insight.strategyId);
        
        if (strategyAddress !== ethers.constants.AddressZero) {
          // Get trust score from TrustCurve
          const trustScore = await this.trustCurve.getTrustScore(insight.strategyId);
          
          // Get strategy scorecard
          const scorecard = await this.trustCurve.getStrategyScorecard(insight.strategyId);
          
          // Get strategy metrics from AIStrategyV35 contract
          const strategyAbi = require('../../abi/AIStrategyV35.json');
          const strategy = new ethers.Contract(strategyAddress, strategyAbi, this.provider);
          
          const metrics = await strategy.getPerformanceMetrics();
          
          // Enrich insight with on-chain data
          enrichedInsights.push({
            ...insight,
            trustScore: trustScore.toNumber(),
            totalExecutions: scorecard.totalExecutions.toNumber(),
            successfulExecutions: scorecard.successfulExecutions.toNumber(),
            winRate: scorecard.winRate,
            totalProfitVerified: ethers.utils.formatEther(scorecard.totalProfitVerified),
            lastVerifiedAt: new Date(scorecard.lastVerifiedAt.toNumber() * 1000),
            onChainMetrics: {
              totalExecutions: metrics._totalExecutions.toNumber(),
              successRate: metrics._successRate.toNumber(),
              totalProfit: ethers.utils.formatEther(metrics._totalProfit),
              trustScore: metrics._trustScore.toNumber()
            }
          });
        } else {
          enrichedInsights.push(insight);
        }
      } catch (error) {
        console.error(`Error enriching insight for strategy ${insight.strategyId}:`, error);
        enrichedInsights.push(insight);
      }
    }

    return enrichedInsights;
  }

  /**
   * Get strategy by ID
   * @param {string} strategyId - Strategy ID
   * @returns {Promise<Object>} Strategy data
   */
  async getStrategyById(strategyId) {
    try {
      // Check if strategy exists in database
      const storedStrategy = await this.aiModel.getStrategyById(strategyId);
      
      if (storedStrategy) {
        // Refresh on-chain data
        return this.refreshStrategyOnChainData(storedStrategy);
      }
      
      // If not in database, fetch from Python agent
      const response = await axios.get(`${this.pythonAgentUrl}/api/strategy/${strategyId}`);
      const strategy = response.data;
      
      // Enrich with on-chain data
      const enrichedStrategy = await this.refreshStrategyOnChainData(strategy);
      
      // Store in database
      await this.aiModel.storeStrategy(enrichedStrategy);
      
      return enrichedStrategy;
    } catch (error) {
      console.error(`Error fetching strategy ${strategyId}:`, error);
      throw error;
    }
  }

  /**
   * Refresh strategy on-chain data
   * @param {Object} strategy - Strategy data
   * @returns {Promise<Object>} Updated strategy data
   */
  async refreshStrategyOnChainData(strategy) {
    if (!this.trustCurve || !this.executor) {
      return strategy;
    }

    try {
      // Get strategy address from executor
      const strategyAddress = await this.executor.getStrategyAddress(strategy.strategyId);
      
      if (strategyAddress !== ethers.constants.AddressZero) {
        // Get trust score from TrustCurve
        const trustScore = await this.trustCurve.getTrustScore(strategy.strategyId);
        
        // Get strategy scorecard
        const scorecard = await this.trustCurve.getStrategyScorecard(strategy.strategyId);
        
        // Get strategy metrics from AIStrategyV35 contract
        const strategyAbi = require('../../abi/AIStrategyV35.json');
        const strategyContract = new ethers.Contract(strategyAddress, strategyAbi, this.provider);
        
        const metrics = await strategyContract.getPerformanceMetrics();
        const riskParams = await strategyContract.getRiskParameters();
        const strategyInfo = await strategyContract.getStrategyInfo();
        
        // Update strategy with on-chain data
        return {
          ...strategy,
          strategyAddress,
          name: strategyInfo._name,
          description: strategyInfo._description,
          trustScore: trustScore.toNumber(),
          totalExecutions: scorecard.totalExecutions.toNumber(),
          successfulExecutions: scorecard.successfulExecutions.toNumber(),
          winRate: scorecard.winRate,
          totalProfitVerified: ethers.utils.formatEther(scorecard.totalProfitVerified),
          lastVerifiedAt: new Date(scorecard.lastVerifiedAt.toNumber() * 1000),
          onChainMetrics: {
            totalExecutions: metrics._totalExecutions.toNumber(),
            successRate: metrics._successRate.toNumber(),
            totalProfit: ethers.utils.formatEther(metrics._totalProfit),
            trustScore: metrics._trustScore.toNumber()
          },
          riskParameters: {
            maxCapitalAtRisk: riskParams.maxCapitalAtRisk.toString(),
            minProfitThreshold: riskParams.minProfitThreshold.toString(),
            maxSlippage: riskParams.maxSlippage.toString(),
            maxGasPrice: riskParams.maxGasPrice.toString(),
            emergencyThreshold: riskParams.emergencyThreshold.toString()
          }
        };
      }
    } catch (error) {
      console.error(`Error refreshing on-chain data for strategy ${strategy.strategyId}:`, error);
    }
    
    return strategy;
  }

  /**
   * Get all strategies
   * @returns {Promise<Array>} Array of strategies
   */
  async getStrategies() {
    try {
      // Try to get strategies from Python agent
      const response = await axios.get(`${this.pythonAgentUrl}/api/strategies`);
      const strategies = response.data;
      
      // Store strategies in database
      await this.aiModel.storeStrategies(strategies);
      
      return strategies;
    } catch (error) {
      console.error('Error fetching strategies from Python agent:', error);
      
      // Fall back to database if Python agent is unavailable
      return this.aiModel.getStrategies();
    }
  }

  /**
   * Execute a strategy
   * @param {string} strategyId - Strategy ID
   * @param {Object} executionParams - Execution parameters
   * @returns {Promise<Object>} Execution result
   */
  async executeStrategy(strategyId, executionParams) {
    if (!this.executor) {
      throw new Error('Executor contract not initialized');
    }

    try {      // SECURITY: Use secure key management instead of direct private key access
      throw new Error('SECURITY ERROR: Direct private key usage is prohibited. Use secure key management.');
      // const wallet = new ethers.Wallet(process.env.SECURE_KEY, this.provider);
      
      // Connect executor contract with wallet
      const executorWithSigner = this.executor.connect(wallet);
      
      // Execute strategy
      const tx = await executorWithSigner.executeStrategy(
        strategyId,
        executionParams.maxCapital || ethers.constants.MaxUint256,
        executionParams.data || '0x'
      );
      
      // Wait for transaction to be mined
      const receipt = await tx.wait();
      
      // Parse logs for execution result
      const executionEvent = receipt.events.find(e => e.event === 'StrategyExecuted');
      
      if (executionEvent) {
        const [strategyIdEvent, success, profit, trustScore] = executionEvent.args;
        
        return {
          transactionHash: receipt.transactionHash,
          strategyId: strategyIdEvent.toString(),
          success,
          profit: ethers.utils.formatEther(profit),
          trustScore: trustScore.toNumber()
        };
      }
      
      return {
        transactionHash: receipt.transactionHash,
        strategyId,
        success: false,
        message: 'Execution event not found in transaction logs'
      };
    } catch (error) {
      console.error(`Error executing strategy ${strategyId}:`, error);
      throw error;
    }
  }
}

module.exports = AIStrategyService;