const express = require('express');
const AIStrategyService = require('../services/AIStrategyService');

const router = express.Router();
const aiService = new AIStrategyService();

/**
 * @route GET /api/ai/insights
 * @desc Get latest AI insights
 * @access Public
 */
router.get('/insights', async (req, res) => {
  try {
    const insights = await aiService.getLatestInsights();
    res.json(insights);
  } catch (error) {
    console.error('Error in /api/ai/insights:', error);
    res.status(500).json({ error: 'Failed to fetch AI insights' });
  }
});

/**
 * @route GET /api/ai/strategy/:id
 * @desc Get strategy by ID
 * @access Public
 */
router.get('/strategy/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const strategy = await aiService.getStrategyById(id);
    
    if (!strategy) {
      return res.status(404).json({ error: 'Strategy not found' });
    }
    
    res.json(strategy);
  } catch (error) {
    console.error(`Error in /api/ai/strategy/${req.params.id}:`, error);
    res.status(500).json({ error: 'Failed to fetch strategy' });
  }
});

/**
 * @route GET /api/ai/strategies
 * @desc Get all strategies
 * @access Public
 */
router.get('/strategies', async (req, res) => {
  try {
    const strategies = await aiService.getStrategies();
    res.json(strategies);
  } catch (error) {
    console.error('Error in /api/ai/strategies:', error);
    res.status(500).json({ error: 'Failed to fetch strategies' });
  }
});

/**
 * @route POST /api/ai/execute/:id
 * @desc Execute a strategy
 * @access Private
 */
router.post('/execute/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const executionParams = req.body;
    
    // Validate API key
    const apiKey = req.headers['x-api-key'];
    if (!apiKey || apiKey !== process.env.API_KEY) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    
    const result = await aiService.executeStrategy(id, executionParams);
    res.json(result);
  } catch (error) {
    console.error(`Error in /api/ai/execute/${req.params.id}:`, error);
    res.status(500).json({ error: 'Failed to execute strategy', message: error.message });
  }
});

/**
 * @route GET /api/ai/metrics/:id
 * @desc Get performance metrics for a strategy
 * @access Public
 */
router.get('/metrics/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const strategy = await aiService.getStrategyById(id);
    
    if (!strategy) {
      return res.status(404).json({ error: 'Strategy not found' });
    }
    
    res.json({
      strategyId: strategy.strategyId,
      name: strategy.name,
      trustScore: strategy.trustScore,
      metrics: strategy.onChainMetrics,
      riskParameters: strategy.riskParameters
    });
  } catch (error) {
    console.error(`Error in /api/ai/metrics/${req.params.id}:`, error);
    res.status(500).json({ error: 'Failed to fetch metrics' });
  }
});

module.exports = router;