const WebSocketService = require('./WebSocketService');

/**
 * Extended WebSocket Service for Sentinel Alerts
 * Handles sentinel alert message types and filtering
 */
class SentinelWebSocketService extends WebSocketService {
  constructor(wss) {
    super(wss);
    
    // Alert history storage
    this.alertHistory = [];
    this.maxAlertHistory = 100;
    
    // Alert channels
    this.alertChannels = {
      'sentinel_alerts': true,
      'oracle_alerts': true,
      'mev_alerts': true,
      'strategy_alerts': true
    };
    
    console.log('Sentinel WebSocket Service initialized');
  }
  
  /**
   * Override the handleClientMessage method to add sentinel alert handling
   * @param {string} clientId - Client identifier
   * @param {Object} data - Message data
   */
  handleClientMessage(clientId, data) {
    // First call the parent method to handle standard messages
    super.handleClientMessage(clientId, data);
    
    const client = this.clients.get(clientId);
    if (!client) return;
    
    // Handle sentinel-specific message types
    switch (data.type) {
      case 'subscribe_alerts':
        if (data.alertTypes && Array.isArray(data.alertTypes)) {
          // Store alert type subscriptions
          client.alertSubscriptions = data.alertTypes;
          console.log(`Client ${clientId} subscribed to alert types: ${data.alertTypes.join(', ')}`);
          
          // Send initial alert history for subscribed types
          this.sendAlertHistory(clientId, data.alertTypes);
        }
        break;
      
      case 'acknowledge_alert':
        if (data.alertId) {
          this.acknowledgeAlert(data.alertId, clientId);
          console.log(`Client ${clientId} acknowledged alert ${data.alertId}`);
        }
        break;
      
      case 'dismiss_alert':
        if (data.alertId) {
          this.dismissAlert(data.alertId, clientId);
          console.log(`Client ${clientId} dismissed alert ${data.alertId}`);
        }
        break;
      
      case 'get_alert_history':
        this.sendAlertHistory(clientId, data.alertTypes, data.limit || 50);
        break;
    }
  }
  
  /**
   * Send initial data for sentinel alert channels
   * @param {string} clientId - Client identifier
   * @param {string} channel - Channel name
   */
  async sendInitialData(clientId, channel) {
    // First call the parent method to handle standard channels
    await super.sendInitialData(clientId, channel);
    
    const client = this.clients.get(clientId);
    if (!client) return;
    
    // Handle sentinel-specific channels
    if (channel === 'sentinel_alerts') {
      // Send the most recent alerts (limited to 20)
      const recentAlerts = this.alertHistory.slice(0, 20);
      
      client.ws.send(JSON.stringify({
        type: 'data',
        channel: 'sentinel_alerts',
        alerts: recentAlerts
      }));
    }
  }
  
  /**
   * Process incoming sentinel alert
   * @param {Object} alert - Alert data
   */
  processAlert(alert) {
    // Add timestamp if not present
    if (!alert.timestamp) {
      alert.timestamp = Date.now();
    }
    
    // Add to history
    this.addToAlertHistory(alert);
    
    // Broadcast to appropriate channels
    this.broadcastAlert(alert);
    
    // Log high priority alerts
    if (alert.priority === 'high' || alert.priority === 'critical' || alert.priority === 'emergency') {
      console.warn(`HIGH PRIORITY ALERT: ${alert.source} - ${alert.title} - ${alert.message}`);
    }
  }
  
  /**
   * Add alert to history
   * @param {Object} alert - Alert data
   */
  addToAlertHistory(alert) {
    // Add to beginning of array (newest first)
    this.alertHistory.unshift(alert);
    
    // Trim history if needed
    if (this.alertHistory.length > this.maxAlertHistory) {
      this.alertHistory = this.alertHistory.slice(0, this.maxAlertHistory);
    }
  }
  
  /**
   * Broadcast alert to subscribed clients
   * @param {Object} alert - Alert data
   */
  broadcastAlert(alert) {
    // Determine which channel to use based on alert source
    let channel = 'sentinel_alerts'; // Default channel
    
    if (alert.source === 'oracle') {
      channel = 'oracle_alerts';
    } else if (alert.source === 'mev') {
      channel = 'mev_alerts';
    } else if (alert.source === 'strategy') {
      channel = 'strategy_alerts';
    }
    
    // Broadcast to the specific channel
    this.broadcast(channel, { alert });
    
    // Also broadcast to the general sentinel_alerts channel
    if (channel !== 'sentinel_alerts') {
      this.broadcast('sentinel_alerts', { alert });
    }
  }
  
  /**
   * Send alert history to client
   * @param {string} clientId - Client identifier
   * @param {Array} alertTypes - Types of alerts to include
   * @param {number} limit - Maximum number of alerts to send
   */
  sendAlertHistory(clientId, alertTypes = null, limit = 50) {
    const client = this.clients.get(clientId);
    if (!client || client.ws.readyState !== WebSocket.OPEN) return;
    
    // Filter alerts by type if specified
    let filteredAlerts = this.alertHistory;
    if (alertTypes && Array.isArray(alertTypes) && alertTypes.length > 0) {
      filteredAlerts = this.alertHistory.filter(alert => 
        alertTypes.includes(alert.source)
      );
    }
    
    // Limit the number of alerts
    filteredAlerts = filteredAlerts.slice(0, limit);
    
    // Send to client
    client.ws.send(JSON.stringify({
      type: 'alert_history',
      alerts: filteredAlerts,
      timestamp: Date.now()
    }));
  }
  
  /**
   * Acknowledge an alert
   * @param {string} alertId - Alert identifier
   * @param {string} clientId - Client identifier
   */
  acknowledgeAlert(alertId, clientId) {
    // Find the alert in history
    const alertIndex = this.alertHistory.findIndex(a => a.alert_id === alertId);
    if (alertIndex >= 0) {
      // Update the alert
      this.alertHistory[alertIndex].acknowledged = true;
      this.alertHistory[alertIndex].acknowledgedBy = clientId;
      this.alertHistory[alertIndex].acknowledgedAt = Date.now();
      
      // Broadcast the update
      this.broadcast('sentinel_alerts', { 
        type: 'alert_update',
        alert: this.alertHistory[alertIndex]
      });
    }
  }
  
  /**
   * Dismiss an alert
   * @param {string} alertId - Alert identifier
   * @param {string} clientId - Client identifier
   */
  dismissAlert(alertId, clientId) {
    // Find the alert in history
    const alertIndex = this.alertHistory.findIndex(a => a.alert_id === alertId);
    if (alertIndex >= 0) {
      // Update the alert
      this.alertHistory[alertIndex].dismissed = true;
      this.alertHistory[alertIndex].dismissedBy = clientId;
      this.alertHistory[alertIndex].dismissedAt = Date.now();
      
      // Broadcast the update
      this.broadcast('sentinel_alerts', { 
        type: 'alert_update',
        alert: this.alertHistory[alertIndex]
      });
    }
  }
  
  /**
   * Override the setupWebSocketServer method to add sentinel channels
   */
  setupWebSocketServer() {
    super.setupWebSocketServer();
    
    // Modify the welcome message to include sentinel channels
    this.wss.on('connection', (ws, req) => {
      const clientId = this.generateClientId();
      const client = this.clients.get(clientId);
      
      if (client) {
        // Add sentinel channels to the welcome message
        ws.send(JSON.stringify({
          type: 'connection',
          message: 'Connected to V35 WebSocket Server with Sentinel Support',
          clientId,
          channels: [
            'ai_insights', 
            'zk_proofs', 
            'strategy_updates',
            'sentinel_alerts',
            'oracle_alerts',
            'mev_alerts',
            'strategy_alerts'
          ]
        }));
      }
    });
  }
}

module.exports = SentinelWebSocketService;