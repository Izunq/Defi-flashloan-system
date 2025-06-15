const express = require('express');
const ZKProofService = require('../services/ZKProofService');
const rateLimit = require('express-rate-limit');
const { body, param, validationResult } = require('express-validator');
const { createHmac } = require('crypto');

const router = express.Router();
const zkService = new ZKProofService();

// Rate limiting middleware
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
  message: { error: 'Too many requests, please try again later' }
});

// Apply rate limiting to all routes
router.use(apiLimiter);

// API key validation middleware
const validateApiKey = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  
  if (!apiKey) {
    return res.status(401).json({ error: 'API key is required' });
  }
  
  // Use HMAC to validate the API key
  const hmac = createHmac('sha256', process.env.API_KEY_SECRET || 'default-secret');
  hmac.update(process.env.API_KEY_ID || 'default-id');
  const expectedApiKey = hmac.digest('hex');
  
  if (apiKey !== expectedApiKey && apiKey !== process.env.API_KEY) {
    return res.status(401).json({ error: 'Invalid API key' });
  }
  
  next();
};

// Validation middleware
const validateRequest = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  next();
};

/**
 * @route GET /api/zk/proofs
 * @desc Get latest ZK proofs
 * @access Public
 */
router.get('/proofs', async (req, res) => {
  try {
    const proofs = await zkService.getLatestProofs(req.ip);
    res.json(proofs);
  } catch (error) {
    console.error('Error in /api/zk/proofs:', error);
    
    if (error.message === 'Rate limit exceeded') {
      return res.status(429).json({ error: 'Rate limit exceeded' });
    }
    
    res.status(500).json({ error: 'Failed to fetch ZK proofs' });
  }
});

/**
 * @route GET /api/zk/proof/:id
 * @desc Get proof by strategy ID
 * @access Public
 */
router.get(
  '/proof/:id',
  [
    param('id').isInt().withMessage('Strategy ID must be an integer')
  ],
  validateRequest,
  async (req, res) => {
    try {
      const { id } = req.params;
      const proof = await zkService.getProofByStrategyId(id, req.ip);
      
      if (!proof) {
        return res.status(404).json({ error: 'Proof not found' });
      }
      
      res.json(proof);
    } catch (error) {
      console.error(`Error in /api/zk/proof/${req.params.id}:`, error);
      
      if (error.message === 'Rate limit exceeded') {
        return res.status(429).json({ error: 'Rate limit exceeded' });
      }
      
      res.status(500).json({ error: 'Failed to fetch proof' });
    }
  }
);

/**
 * @route POST /api/zk/verify
 * @desc Verify a ZK proof
 * @access Private
 */
router.post(
  '/verify',
  [
    validateApiKey,
    body('strategyId').isInt().withMessage('Strategy ID must be an integer'),
    body('publicInputs').isArray().withMessage('Public inputs must be an array'),
    body('proof').isString().withMessage('Proof must be a string')
  ],
  validateRequest,
  async (req, res) => {
    try {
      const { strategyId, publicInputs, proof } = req.body;
      
      const result = await zkService.verifyProof(strategyId, publicInputs, proof, req.ip);
      res.json(result);
    } catch (error) {
      console.error('Error in /api/zk/verify:', error);
      
      if (error.message === 'Rate limit exceeded') {
        return res.status(429).json({ error: 'Rate limit exceeded' });
      }
      
      res.status(500).json({ error: 'Failed to verify proof', message: error.message });
    }
  }
);

/**
 * @route POST /api/zk/submit
 * @desc Submit a new ZK proof
 * @access Private
 */
router.post(
  '/submit',
  [
    validateApiKey,
    body('strategyId').isInt().withMessage('Strategy ID must be an integer'),
    body('publicInputs').isArray().withMessage('Public inputs must be an array'),
    body('proof').isString().withMessage('Proof must be a string')
  ],
  validateRequest,
  async (req, res) => {
    try {
      const { strategyId, publicInputs, proof } = req.body;
      
      const result = await zkService.submitProof(strategyId, publicInputs, proof, req.ip);
      res.json(result);
    } catch (error) {
      console.error('Error in /api/zk/submit:', error);
      
      if (error.message === 'Rate limit exceeded') {
        return res.status(429).json({ error: 'Rate limit exceeded' });
      }
      
      res.status(500).json({ error: 'Failed to submit proof', message: error.message });
    }
  }
);

/**
 * @route GET /api/zk/verifications/:id
 * @desc Get verification history for a strategy
 * @access Public
 */
router.get(
  '/verifications/:id',
  [
    param('id').isInt().withMessage('Strategy ID must be an integer')
  ],
  validateRequest,
  async (req, res) => {
    try {
      const { id } = req.params;
      const verifications = await zkService.getVerificationHistory(id, req.ip);
      res.json(verifications);
    } catch (error) {
      console.error(`Error in /api/zk/verifications/${req.params.id}:`, error);
      
      if (error.message === 'Rate limit exceeded') {
        return res.status(429).json({ error: 'Rate limit exceeded' });
      }
      
      res.status(500).json({ error: 'Failed to fetch verification history' });
    }
  }
);

/**
 * @route GET /api/zk/submissions/:id
 * @desc Get submission history for a strategy
 * @access Public
 */
router.get(
  '/submissions/:id',
  [
    param('id').isInt().withMessage('Strategy ID must be an integer')
  ],
  validateRequest,
  async (req, res) => {
    try {
      const { id } = req.params;
      const submissions = await zkService.getSubmissionHistory(id, req.ip);
      res.json(submissions);
    } catch (error) {
      console.error(`Error in /api/zk/submissions/${req.params.id}:`, error);
      
      if (error.message === 'Rate limit exceeded') {
        return res.status(429).json({ error: 'Rate limit exceeded' });
      }
      
      res.status(500).json({ error: 'Failed to fetch submission history' });
    }
  }
);

/**
 * @route GET /api/zk/health
 * @desc Health check endpoint
 * @access Public
 */
router.get('/health', async (req, res) => {
  try {
    // Check if we can connect to the blockchain
    const blockNumber = await zkService.provider.getBlockNumber();
    
    res.json({
      status: 'ok',
      blockNumber,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error in /api/zk/health:', error);
    res.status(500).json({ error: 'Health check failed', message: error.message });
  }
});

module.exports = router;