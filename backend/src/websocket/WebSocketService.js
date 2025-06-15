const { ethers } = require('ethers');
const AIStrategyService = require('../services/AIStrategyService');
const ZKProofService = require('../services/ZKProofService');

/**
 * WebSocket Service for real-time updates
 */
class WebSocketService {
  constructor(wss) {
    this.wss = wss;
    this.clients = new Map();
    this.aiStrategyService = new AIStrategyService();
    this.zkProofService = new ZKProofService();
    
    this.setupWebSocketServer();
    this.setupPeriodicUpdates();
    this.setupBlockchainListeners();
  }

  /**
   * Set up WebSocket server event handlers
   */
  setupWebSocketServer() {
    this.wss.on('connection', (ws, req) => {
      const clientId = this.generateClientId();
      this.clients.set(clientId, {
        ws,
        subscriptions: new Set(),
      });

      console.log(`Client connected: ${clientId}`);

      // Handle messages from clients
      ws.on('message', (message) => {
        try {
          const data = JSON.parse(message);
          this.handleClientMessage(clientId, data);
        } catch (error) {
          console.error('Error parsing message:', error);
          ws.send(JSON.stringify({ error: 'Invalid message format' }));
        }
      });

      // Handle client disconnection
      ws.on('close', () => {
        console.log(`Client disconnected: ${clientId}`);
        this.clients.delete(clientId);
      });

      // Send welcome message
      ws.send(JSON.stringify({
        type: 'connection',
        message: 'Connected to V35 WebSocket Server',
        clientId,
        channels: ['ai_insights', 'zk_proofs', 'strategy_updates']
      }));
    });
  }

  /**
   * Handle messages from clients
   * @param {string} clientId - Client identifier
   * @param {Object} data - Message data
   */
  handleClientMessage(clientId, data) {
    const client = this.clients.get(clientId);
    if (!client) return;

    switch (data.type) {
      case 'subscribe':
        if (data.channel) {
          client.subscriptions.add(data.channel);
          console.log(`Client ${clientId} subscribed to ${data.channel}`);
          
          // Send initial data for the channel
          this.sendInitialData(clientId, data.channel);
        }
        break;
      
      case 'unsubscribe':
        if (data.channel) {
          client.subscriptions.delete(data.channel);
          console.log(`Client ${clientId} unsubscribed from ${data.channel}`);
        }
        break;
      
      case 'ping':
        client.ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
        break;
      
      default:
        console.log(`Unknown message type: ${data.type}`);
    }
  }

  /**
   * Send initial data for a channel to a client
   * @param {string} clientId - Client identifier
   * @param {string} channel - Channel name
   */
  async sendInitialData(clientId, channel) {
    const client = this.clients.get(clientId);
    if (!client) return;

    try {
      switch (channel) {
        case 'ai_insights':
          const insights = await this.aiStrategyService.getLatestInsights();
          client.ws.send(JSON.stringify({
            type: 'data',
            channel: 'ai_insights',
            insights
          }));
          break;
        
        case 'zk_proofs':
          const proofs = await this.zkProofService.getLatestProofs();
          client.ws.send(JSON.stringify({
            type: 'data',
            channel: 'zk_proofs',
            proofs
          }));
          break;
        
        case 'strategy_updates':
          const strategies = await this.aiStrategyService.getStrategies();
          client.ws.send(JSON.stringify({
            type: 'data',
            channel: 'strategy_updates',
            strategies
          }));
          break;
      }
    } catch (error) {
      console.error(`Error sending initial data for ${channel}:`, error);
    }
  }

  /**
   * Broadcast data to all clients subscribed to a channel
   * @param {string} channel - Channel name
   * @param {Object} data - Data to broadcast
   */
  broadcast(channel, data) {
    this.clients.forEach((client, clientId) => {
      if (client.subscriptions.has(channel) && client.ws.readyState === WebSocket.OPEN) {
        client.ws.send(JSON.stringify({
          type: 'data',
          channel,
          ...data
        }));
      }
    });
  }

  /**
   * Set up periodic updates for real-time data
   */
  setupPeriodicUpdates() {
    // Update AI insights every 10 seconds
    setInterval(async () => {
      try {
        const insights = await this.aiStrategyService.getLatestInsights();
        this.broadcast('ai_insights', { insights });
      } catch (error) {
        console.error('Error updating AI insights:', error);
      }
    }, 10000);

    // Update ZK proofs every 30 seconds
    setInterval(async () => {
      try {
        const proofs = await this.zkProofService.getLatestProofs();
        this.broadcast('zk_proofs', { proofs });
      } catch (error) {
        console.error('Error updating ZK proofs:', error);
      }
    }, 30000);
  }

  /**
   * Set up blockchain event listeners
   */
  setupBlockchainListeners() {
    try {
      const provider = new ethers.providers.JsonRpcProvider(process.env.RPC_URL);
      
      // Listen for TrustCurve contract events
      if (process.env.TRUST_CURVE_ADDRESS) {
        const trustCurveAbi = require('../../abi/TrustCurve.json');
        const trustCurve = new ethers.Contract(
          process.env.TRUST_CURVE_ADDRESS,
          trustCurveAbi,
          provider
        );

        // Listen for TrustScoreUpdated events
        trustCurve.on('TrustScoreUpdated', async (strategyId, newScore, event) => {
          console.log(`Trust score updated for strategy ${strategyId}: ${newScore}`);
          
          // Get updated strategy data and broadcast
          const strategy = await this.aiStrategyService.getStrategyById(strategyId.toString());
          this.broadcast('strategy_updates', { 
            type: 'trust_score_update',
            strategy 
          });
        });

        // Listen for ZKVerificationUpdated events
        trustCurve.on('ZKVerificationUpdated', async (strategyId, isValid, event) => {
          console.log(`ZK verification updated for strategy ${strategyId}: ${isValid}`);
          
          // Get updated proof data and broadcast
          const proof = await this.zkProofService.getProofByStrategyId(strategyId.toString());
          this.broadcast('zk_proofs', { 
            type: 'verification_update',
            proof 
          });
        });
      }

      // Listen for ProofAwareExecutor contract events
      if (process.env.PROOF_EXECUTOR_ADDRESS) {
        const executorAbi = require('../../abi/ProofAwareExecutorV35.json');
        const executor = new ethers.Contract(
          process.env.PROOF_EXECUTOR_ADDRESS,
          executorAbi,
          provider
        );

        // Listen for StrategyExecuted events
        executor.on('StrategyExecuted', async (strategyId, success, profit, event) => {
          console.log(`Strategy ${strategyId} executed: success=${success}, profit=${profit}`);
          
          // Get updated strategy data and broadcast
          const strategy = await this.aiStrategyService.getStrategyById(strategyId.toString());
          this.broadcast('strategy_updates', { 
            type: 'execution_update',
            strategy 
          });
        });
      }
    } catch (error) {
      console.error('Error setting up blockchain listeners:', error);
    }
  }

  /**
   * Generate a unique client ID
   * @returns {string} Client ID
   */
  generateClientId() {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

module.exports = WebSocketService;