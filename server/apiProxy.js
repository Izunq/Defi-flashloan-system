/**
 * API Proxy Server
 * 
 * This server acts as a secure proxy between the frontend and external APIs.
 * It keeps API keys and sensitive credentials on the server side.
 */

const express = require('express');
const axios = require('axios');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { createProxyMiddleware } = require('http-proxy-middleware');

// Load environment variables
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Security middleware
app.use(helmet()); // Set security headers
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Rate limiting to prevent abuse
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  standardHeaders: true,
  legacyHeaders: false,
  message: 'Too many requests from this IP, please try again after 15 minutes'
});
app.use(apiLimiter);

// Parse JSON request body
app.use(express.json());

// API configuration
const API_URL = process.env.API_URL || 'http://localhost:8080';
const API_KEY = process.env.API_KEY; // Stored securely on the server

// Middleware to log requests
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.originalUrl}`);
  next();
});

// Middleware to add API key to requests
const addApiKey = (req, res, next) => {
  if (!API_KEY) {
    return res.status(500).json({ error: 'API key not configured on server' });
  }
  req.headers['x-api-key'] = API_KEY;
  next();
};

// AI Insights endpoint
app.get('/api/ai/insights', addApiKey, async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/api/ai/insights`, {
      headers: {
        'x-api-key': API_KEY
      }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching AI insights:', error);
    res.status(error.response?.status || 500).json({
      error: 'Failed to fetch AI insights',
      details: error.response?.data || error.message
    });
  }
});

// ZK Proofs endpoint
app.get('/api/zk/proofs', addApiKey, async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/api/zk/proofs`, {
      headers: {
        'x-api-key': API_KEY
      }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching ZK proofs:', error);
    res.status(error.response?.status || 500).json({
      error: 'Failed to fetch ZK proofs',
      details: error.response?.data || error.message
    });
  }
});

// Submit ZK Proof endpoint
app.post('/api/zk/submit', addApiKey, async (req, res) => {
  try {
    const response = await axios.post(
      `${API_URL}/api/zk/submit`,
      req.body,
      {
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY
        }
      }
    );
    res.json(response.data);
  } catch (error) {
    console.error('Error submitting ZK proof:', error);
    res.status(error.response?.status || 500).json({
      error: 'Failed to submit ZK proof',
      details: error.response?.data || error.message
    });
  }
});

// Verify ZK Proof endpoint
app.post('/api/zk/verify', addApiKey, async (req, res) => {
  try {
    const response = await axios.post(
      `${API_URL}/api/zk/verify`,
      req.body,
      {
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY
        }
      }
    );
    res.json(response.data);
  } catch (error) {
    console.error('Error verifying ZK proof:', error);
    res.status(error.response?.status || 500).json({
      error: 'Failed to verify ZK proof',
      details: error.response?.data || error.message
    });
  }
});

// Strategy metrics endpoint
app.get('/api/strategy/:strategyId/metrics', addApiKey, async (req, res) => {
  try {
    const { strategyId } = req.params;
    const response = await axios.get(`${API_URL}/api/strategy/${strategyId}/metrics`, {
      headers: {
        'x-api-key': API_KEY
      }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching strategy metrics:', error);
    res.status(error.response?.status || 500).json({
      error: 'Failed to fetch strategy metrics',
      details: error.response?.data || error.message
    });
  }
});

// Risk parameters endpoint
app.get('/api/strategy/:strategyId/risk', addApiKey, async (req, res) => {
  try {
    const { strategyId } = req.params;
    const response = await axios.get(`${API_URL}/api/strategy/${strategyId}/risk`, {
      headers: {
        'x-api-key': API_KEY
      }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching risk parameters:', error);
    res.status(error.response?.status || 500).json({
      error: 'Failed to fetch risk parameters',
      details: error.response?.data || error.message
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Start the server
app.listen(PORT, () => {
  console.log(`API Proxy Server running on port ${PORT}`);
});