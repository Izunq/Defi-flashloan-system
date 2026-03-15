import { useState, useEffect, useCallback } from 'react';

// Types for Sentinel Alerts
export interface SentinelAlert {
  alert_id: string;
  source: string;  // "oracle", "mev", "strategy"
  priority: string;  // "low", "medium", "high", "critical", "emergency"
  title: string;
  message: string;
  timestamp: number;
  details: Record<string, any>;
  recommended_actions: string[];
  acknowledged: boolean;
  resolved: boolean;
  resolution_time?: number;
  resolution_details?: string;
  // UI state properties
  dismissed?: boolean;
  dismissedBy?: string;
  dismissedAt?: number;
  acknowledgedBy?: string;
  acknowledgedAt?: number;
}

export interface SentinelAlertsData {
  alerts: SentinelAlert[];
  loading: boolean;
  error: string | null;
  acknowledgeAlert: (alertId: string) => void;
  dismissAlert: (alertId: string) => void;
  fetchAlertHistory: (limit?: number) => void;
  filterAlerts: (sources?: string[], priorities?: string[]) => SentinelAlert[];
  getAlertById: (alertId: string) => SentinelAlert | undefined;
  hasActiveAlerts: (minPriority?: string) => boolean;
}

// WebSocket endpoint for real-time updates
const WS_ENDPOINT = process.env.REACT_APP_WS_ENDPOINT || 'ws://localhost:8083';

export const useSentinelAlerts = (): SentinelAlertsData => {
  const [alerts, setAlerts] = useState<SentinelAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [socket, setSocket] = useState<WebSocket | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    // Only connect in production environment
    if (process.env.NODE_ENV !== 'production') {
      // Load mock data in development
      loadMockAlerts();
      return;
    }

    try {
      const ws = new WebSocket(WS_ENDPOINT);
      
      ws.onopen = () => {
        console.log('WebSocket connected for sentinel alerts');
        ws.send(JSON.stringify({ type: 'subscribe', channel: 'sentinel_alerts' }));
        
        // Subscribe to specific alert types
        ws.send(JSON.stringify({ 
          type: 'subscribe_alerts', 
          alertTypes: ['oracle', 'mev', 'strategy'] 
        }));
        
        // Request alert history
        ws.send(JSON.stringify({ 
          type: 'get_alert_history', 
          limit: 50 
        }));
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.channel === 'sentinel_alerts' && data.alert) {
            // Single new alert
            handleNewAlert(data.alert);
          } else if (data.type === 'alert_history' && Array.isArray(data.alerts)) {
            // Alert history
            setAlerts(data.alerts);
            setLoading(false);
          } else if (data.type === 'alert_update' && data.alert) {
            // Alert update (acknowledgment, dismissal, resolution)
            updateAlert(data.alert);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Failed to connect to alert service');
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      
      setSocket(ws);
      
      return () => {
        ws.close();
      };
    } catch (err) {
      console.error('Error setting up WebSocket:', err);
      setError('Failed to initialize alert service');
      setLoading(false);
    }
  }, []);

  // Handle new alert
  const handleNewAlert = useCallback((alert: SentinelAlert) => {
    setAlerts(prevAlerts => {
      // Check if alert already exists
      const existingIndex = prevAlerts.findIndex(a => a.alert_id === alert.alert_id);
      
      if (existingIndex >= 0) {
        // Update existing alert
        const updatedAlerts = [...prevAlerts];
        updatedAlerts[existingIndex] = alert;
        return updatedAlerts;
      } else {
        // Add new alert at the beginning
        return [alert, ...prevAlerts];
      }
    });
    
    setLoading(false);
  }, []);

  // Update an existing alert
  const updateAlert = useCallback((updatedAlert: SentinelAlert) => {
    setAlerts(prevAlerts => {
      return prevAlerts.map(alert => 
        alert.alert_id === updatedAlert.alert_id ? updatedAlert : alert
      );
    });
  }, []);

  // Load mock alerts for development
  const loadMockAlerts = useCallback(() => {
    const mockAlerts: SentinelAlert[] = [
      {
        alert_id: "oracle-1",
        source: "oracle",
        priority: "high",
        title: "Oracle Alert: PRICE_DEVIATION",
        message: "Oracle anomaly detected for ETH with 5.75% deviation",
        timestamp: Date.now() - 300000, // 5 minutes ago
        details: {
          asset: "ETH",
          price: 2850.25,
          expected_price: 3020.50,
          deviation: 5.75,
          source: "chainlink",
          confidence: 0.92,
          alert_type: "PRICE_DEVIATION",
          false_positive_probability: 0.08
        },
        recommended_actions: [
          "Verify price across multiple sources",
          "Temporarily increase slippage tolerance",
          "Monitor for further deviations"
        ],
        acknowledged: false,
        resolved: false
      },
      {
        alert_id: "mev-1",
        source: "mev",
        priority: "critical",
        title: "MEV Alert: SANDWICH_ATTACK",
        message: "MEV attack detected: SANDWICH_ATTACK",
        timestamp: Date.now() - 600000, // 10 minutes ago
        details: {
          attack_type: "SANDWICH_ATTACK",
          profit: 0.35,
          gas_used: 250000,
          attacker: "${CONTRACT_ADDRESS}",
          victim: "${CONTRACT_ADDRESS}",
          confidence: 0.95
        },
        recommended_actions: [
          "Pause affected strategy",
          "Increase gas price for pending transactions",
          "Implement private transaction routing"
        ],
        acknowledged: true,
        acknowledgedBy: "operator",
        acknowledgedAt: Date.now() - 540000, // 9 minutes ago
        resolved: false
      },
      {
        alert_id: "strategy-1",
        source: "strategy",
        priority: "medium",
        title: "Strategy Alert: Flash Arbitrage V2",
        message: "Abnormal execution time detected for strategy Flash Arbitrage V2",
        timestamp: Date.now() - 1800000, // 30 minutes ago
        details: {
          strategy_id: "flash_arb_v2",
          execution_time: 45,
          baseline_time: 25,
          deviation: 80,
          gas_used: 350000,
          profit: 0.12
        },
        recommended_actions: [
          "Review recent code changes",
          "Check for network congestion",
          "Monitor next execution"
        ],
        acknowledged: true,
        acknowledgedBy: "system",
        acknowledgedAt: Date.now() - 1700000,
        resolved: true,
        resolution_time: Date.now() - 1500000,
        resolution_details: "Network congestion resolved, execution times returned to normal"
      }
    ];
    
    setAlerts(mockAlerts);
    setLoading(false);
  }, []);

  // Acknowledge an alert
  const acknowledgeAlert = useCallback((alertId: string) => {
    // Update local state
    setAlerts(prevAlerts => {
      return prevAlerts.map(alert => {
        if (alert.alert_id === alertId) {
          return {
            ...alert,
            acknowledged: true,
            acknowledgedBy: 'user',
            acknowledgedAt: Date.now()
          };
        }
        return alert;
      });
    });
    
    // Send to server if connected
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'acknowledge_alert',
        alertId
      }));
    }
  }, [socket]);

  // Dismiss an alert
  const dismissAlert = useCallback((alertId: string) => {
    // Update local state
    setAlerts(prevAlerts => {
      return prevAlerts.map(alert => {
        if (alert.alert_id === alertId) {
          return {
            ...alert,
            dismissed: true,
            dismissedBy: 'user',
            dismissedAt: Date.now()
          };
        }
        return alert;
      });
    });
    
    // Send to server if connected
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'dismiss_alert',
        alertId
      }));
    }
  }, [socket]);

  // Fetch alert history
  const fetchAlertHistory = useCallback((limit: number = 50) => {
    setLoading(true);
    
    if (process.env.NODE_ENV !== 'production') {
      // Reload mock data in development
      loadMockAlerts();
      return;
    }
    
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'get_alert_history',
        limit
      }));
    } else {
      setError('Not connected to alert service');
      setLoading(false);
    }
  }, [socket, loadMockAlerts]);

  // Filter alerts by source and priority
  const filterAlerts = useCallback((sources?: string[], priorities?: string[]): SentinelAlert[] => {
    return alerts.filter(alert => {
      const sourceMatch = !sources || sources.length === 0 || sources.includes(alert.source);
      const priorityMatch = !priorities || priorities.length === 0 || priorities.includes(alert.priority);
      return sourceMatch && priorityMatch && !alert.dismissed;
    });
  }, [alerts]);

  // Get alert by ID
  const getAlertById = useCallback((alertId: string): SentinelAlert | undefined => {
    return alerts.find(alert => alert.alert_id === alertId);
  }, [alerts]);

  // Check if there are active alerts of at least the specified priority
  const hasActiveAlerts = useCallback((minPriority?: string): boolean => {
    const priorityLevels = {
      'low': 1,
      'medium': 2,
      'high': 3,
      'critical': 4,
      'emergency': 5
    };
    
    const minLevel = minPriority ? priorityLevels[minPriority as keyof typeof priorityLevels] || 1 : 1;
    
    return alerts.some(alert => {
      const alertLevel = priorityLevels[alert.priority as keyof typeof priorityLevels] || 1;
      return !alert.dismissed && !alert.resolved && alertLevel >= minLevel;
    });
  }, [alerts]);

  return {
    alerts,
    loading,
    error,
    acknowledgeAlert,
    dismissAlert,
    fetchAlertHistory,
    filterAlerts,
    getAlertById,
    hasActiveAlerts
  };
};

export default useSentinelAlerts;