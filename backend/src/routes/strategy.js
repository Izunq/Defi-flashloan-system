const express = require('express');
const AIStrategyService = require('../services/AIStrategyService');
const ZKProofService = require('../services/ZKProofService');

const router = express.Router();
const aiService = new AIStrategyService();
const zkService = new ZKProofService();

/**
 * @route GET /api/strategy/:id
 * @desc Get comprehensive strategy data including proofs and metrics
 * @access Public
 */
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    // Get strategy data
    const strategy = await aiService.getStrategyById(id);
    
    if (!strategy) {
      return res.status(404).json({ error: 'Strategy not found' });
    }
    
    // Get latest proof for the strategy
    const proof = await zkService.getProofByStrategyId(id);
    
    // Get verification history
    const verifications = await zkService.getVerificationHistory(id);
    
    // Combine data
    const result = {
      ...strategy,
      proof,
      verifications: verifications.slice(0, 10) // Limit to 10 most recent
    };
    
    res.json(result);
  } catch (error) {
    console.error(`Error in /api/strategy/${req.params.id}:`, error);
    res.status(500).json({ error: 'Failed to fetch strategy data' });
  }
});

/**
 * @route GET /api/strategy/:id/history
 * @desc Get execution history for a strategy
 * @access Public
 */
router.get('/:id/history', async (req, res) => {
  try {
    const { id } = req.params;
    
    // This would be implemented with a dedicated ExecutionHistoryService
    // For now, we'll return a mock response
    res.json({
      strategyId: id,
      executions: [
        {
          timestamp: new Date(Date.now() - 3600000),
          success: true,
          profit: '12.45',
          gasUsed: '250000',
          transactionHash: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        },
        {
          timestamp: new Date(Date.now() - 7200000),
          success: true,
          profit: '8.32',
          gasUsed: '230000',
          transactionHash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
        },
        {
          timestamp: new Date(Date.now() - 10800000),
          success: false,
          profit: '0',
          gasUsed: '150000',
          transactionHash: '0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456'
        }
      ]
    });
  } catch (error) {
    console.error(`Error in /api/strategy/${req.params.id}/history:`, error);
    res.status(500).json({ error: 'Failed to fetch execution history' });
  }
});

/**
 * @route GET /api/strategy/:id/performance
 * @desc Get performance metrics for a strategy
 * @access Public
 */
router.get('/:id/performance', async (req, res) => {
  try {
    const { id } = req.params;
    const strategy = await aiService.getStrategyById(id);
    
    if (!strategy) {
      return res.status(404).json({ error: 'Strategy not found' });
    }
    
    // Calculate additional metrics
    const totalExecutions = strategy.onChainMetrics?.totalExecutions || 0;
    const successRate = strategy.onChainMetrics?.successRate || 0;
    const totalProfit = parseFloat(strategy.onChainMetrics?.totalProfit || 0);
    
    const performance = {
      strategyId: id,
      name: strategy.name,
      metrics: {
        ...strategy.onChainMetrics,
        averageProfitPerExecution: totalExecutions > 0 ? totalProfit / totalExecutions : 0,
        profitPerDay: totalProfit / (Math.max(1, Math.floor((Date.now() - new Date(strategy.lastVerifiedAt).getTime()) / (24 * 60 * 60 * 1000)))),
        riskAdjustedReturn: totalProfit * (successRate / 100)
      },
      trustScore: strategy.trustScore,
      riskParameters: strategy.riskParameters
    };
    
    res.json(performance);
  } catch (error) {
    console.error(`Error in /api/strategy/${req.params.id}/performance:`, error);
    res.status(500).json({ error: 'Failed to fetch performance metrics' });
  }
});

/**
 * @route POST /api/strategy/:id/simulate
 * @desc Simulate strategy execution
 * @access Private
 */
router.post('/:id/simulate', async (req, res) => {
  try {
    const { id } = req.params;
    const { parameters } = req.body;
    
    // Validate API key
    const apiKey = req.headers['x-api-key'];
    if (!apiKey || apiKey !== process.env.API_KEY) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    
    // This would be implemented with a dedicated SimulationService
    // For now, we'll return a mock response
    res.json({
      strategyId: id,
      simulationId: `sim_${Date.now()}`,
      timestamp: new Date(),
      result: {
        success: Math.random() > 0.2,
        estimatedProfit: (Math.random() * 20 + 5).toFixed(2),
        estimatedGas: Math.floor(Math.random() * 300000 + 100000),
        riskAssessment: Math.floor(Math.random() * 100)
      },
      parameters
    });
  } catch (error) {
    console.error(`Error in /api/strategy/${req.params.id}/simulate:`, error);
    res.status(500).json({ error: 'Failed to simulate strategy', message: error.message });
  }
});

module.exports = router;