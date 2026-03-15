import { useState, useEffect } from 'react';

// Helper function for creating mock hooks with realistic data
const useMockHook = <T>(
  dataFactory: () => T, 
  delay: number, 
  shouldError: boolean, 
  serviceName: string
) => {
  const [state, setState] = useState<{
    data: T | null;
    isLoading: boolean;
    error: Error | null;
  }>({
    data: null,
    isLoading: true,
    error: null
  });

  useEffect(() => {
    const timer = setTimeout(() => {
      if (shouldError) {
        setState({
          data: null,
          isLoading: false,
          error: new Error(`Failed to fetch from ${serviceName}. Please check your connection and try again.`)
        });
      } else {
        setState({
          data: dataFactory(),
          isLoading: false,
          error: null
        });
      }
    }, delay);

    return () => clearTimeout(timer);
  }, [dataFactory, delay, shouldError, serviceName]);

  return state;
};

// Enhanced system health with more realistic data
export const useSystemHealth = () => useMockHook(
  () => ({
    'Node.js Backend': 'Operational',
    'Postgres Database': 'Operational',
    'Python AI Agent': 'Operational',
    'MATLAB Bridge': 'Degraded', // This creates the issue mentioned
    'Blockchain Node': 'Operational',
    'Redis Cache': 'Operational',
    'WebSocket Server': 'Operational'
  }),
  1200,
  false,
  'System Health'
);

// Enhanced alerts with metadata
export const useSentinelAlerts = () => useMockHook(
  () => [
    {
      id: 1,
      source: 'OracleSentinel',
      message: 'ETH/USD price deviation detected: 1.7% above consensus',
      level: 'critical' as const,
      timestamp: Date.now() - 45000, // 45 seconds ago
      metadata: {
        pair: 'ETH/USD',
        deviation: 1.7,
        threshold: 1.5,
        exchanges: ['Binance', 'Coinbase', 'Kraken']
      }
    },
    {
      id: 2,
      source: 'MEVSentinel',
      message: 'Large sandwich opportunity: $547K USDC swap with 0.8% slippage',
      level: 'warning' as const,
      timestamp: Date.now() - 180000, // 3 minutes ago
      metadata: {
        pair: 'USDC/WETH',
        expectedProfit: 0.73,
        requiredCapital: 150
      }
    },
    {
      id: 3,
      source: 'GasSentinel',
      message: 'Gas price spike detected: 89 gwei (normal: 27 gwei)',
      level: 'info' as const,
      timestamp: Date.now() - 420000, // 7 minutes ago
      metadata: {
        currentGas: 89,
        normalGas: 27,
        trend: 'increasing'
      }
    },
    {
      id: 4,
      source: 'LiquidationSentinel',
      message: 'Large liquidation cascade approaching: $2.3M ETH positions at $1,820',
      level: 'warning' as const,
      timestamp: Date.now() - 600000, // 10 minutes ago
      metadata: {
        asset: 'ETH',
        liquidationPrice: 1820,
        totalValue: 2300000
      }
    }
  ],
  1800,
  false,
  'Sentinel Alerts'
);

// Enhanced AI strategy data
export const useAIStrategyData = () => useMockHook(
  () => ({
    confidence: 0.87,
    summary: 'High-confidence triangular arbitrage opportunity detected across Uniswap V3, SushiSwap, and Balancer. Current market volatility and gas conditions favor execution.',
    details: {
      pair: 'USDC/WETH/WBTC',
      potentialProfit: 1.23,
      requiredCapital: 180000,
      risk_assessment: 'Medium',
      market_conditions: 'Favorable - Medium volatility, normal gas prices, high liquidity',
      execution_time: '2-3 blocks',
      confidence_factors: [
        'Historical pattern match: 94%',
        'Liquidity sufficient: 98%',
        'Gas cost acceptable: 89%',
        'MEV competition: Low'
      ]
    }
  }),
  2200,
  false,
  'AI Strategy Data'
);

// Enhanced ZK proof data
export const useZKProofData = () => useMockHook(
  () => [
    {
      id: 'zk-proof-a4b8c1',
      status: 'Verified',
      verificationTime: 187,
      proofType: 'Arbitrage Privacy',
      timestamp: Date.now() - 30000
    },
    {
      id: 'zk-proof-d9e2f7',
      status: 'Verifying',
      verificationTime: -1,
      proofType: 'Transaction Hiding',
      timestamp: Date.now() - 15000
    },
    {
      id: 'zk-proof-g5h1i3',
      status: 'Verified',
      verificationTime: 143,
      proofType: 'Balance Privacy',
      timestamp: Date.now() - 60000
    },
    {
      id: 'zk-proof-j7k9m2',
      status: 'Failed',
      verificationTime: 89,
      proofType: 'MEV Protection',
      timestamp: Date.now() - 120000,
      error: 'Invalid witness'
    }
  ],
  2800,
  false,
  'ZK Proofs Service'
);

// Enhanced risk metrics with more detail
export const useRiskMetrics = () => useMockHook(
  () => ({
    var: 12.54, // Value at Risk in ETH
    maxDrawdown: 0.152, // 15.2%
    exposure: 1247800, // Total exposure in USD
    sharpeRatio: 2.41,
    portfolioBeta: 1.23,
    correlationMatrix: {
      'ETH': 0.78,
      'BTC': 0.45,
      'Stablecoins': 0.12
    },
    riskScore: 73, // Out of 100
    leverage: 3.2,
    liquidationRisk: 'Low',
    stressTestResults: {
      '10% Market Drop': '-8.7 ETH',
      '25% Market Drop': '-23.4 ETH',
      'Black Monday Scenario': '-45.6 ETH'
    }
  }),
  1900,
  false,
  'Risk Metrics'
);

// Enhanced strategies with performance data
export const useStrategies = () => useMockHook(
  () => [
    {
      id: 1,
      name: 'Tri-Arbitrage V2',
      pnl: 14.23,
      active: true,
      risk_level: 'medium' as const,
      last_executed: Date.now() - 120000, // 2 minutes ago
      success_rate: 0.89,
      total_trades: 147,
      avg_profit: 0.097,
      max_loss: -0.34,
      description: 'Multi-DEX triangular arbitrage with MEV protection'
    },
    {
      id: 2,
      name: 'Flash-Mint Hedge',
      pnl: 5.12,
      active: false,
      risk_level: 'low' as const,
      last_executed: Date.now() - 3600000, // 1 hour ago
      success_rate: 0.94,
      total_trades: 89,
      avg_profit: 0.058,
      max_loss: -0.12,
      description: 'Flash loan arbitrage with automated hedging'
    },
    {
      id: 3,
      name: 'MEV Backrun',
      pnl: 8.87,
      active: true,
      risk_level: 'high' as const,
      last_executed: Date.now() - 45000, // 45 seconds ago
      success_rate: 0.76,
      total_trades: 203,
      avg_profit: 0.044,
      max_loss: -0.67,
      description: 'Backrunning MEV opportunities with dynamic gas pricing'
    },
    {
      id: 4,
      name: 'Yield Optimizer',
      pnl: 3.45,
      active: true,
      risk_level: 'low' as const,
      last_executed: Date.now() - 1800000, // 30 minutes ago
      success_rate: 0.98,
      total_trades: 34,
      avg_profit: 0.101,
      max_loss: -0.08,
      description: 'Automated yield farming optimization across protocols'
    },
    {
      id: 5,
      name: 'Options Arbitrage',
      pnl: -1.23,
      active: false,
      risk_level: 'high' as const,
      last_executed: Date.now() - 7200000, // 2 hours ago
      success_rate: 0.67,
      total_trades: 56,
      avg_profit: -0.022,
      max_loss: -0.89,
      description: 'Cross-platform options arbitrage (experimental)'
    }
  ],
  2400,
  false,
  'Strategies'
);

// App configuration
export const useAppConfig = () => ({
  apiBaseUrl: 'http://localhost:8083/api',
  webSocketUrl: 'ws://localhost:8083/ws',
  environment: 'development',
  version: '2.1.3',
  features: {
    zkProofs: true,
    aiAnalysis: true,
    mevProtection: true,
    matlabIntegration: true
  }
});

// Enhanced WebSocket hook
export const useWebSocket = (url: string) => {
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('connecting');
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  useEffect(() => {
    // Simulate WebSocket connection
    const timer = setTimeout(() => {
      if (Math.random() > 0.1) { // 90% success rate
        setConnectionStatus('connected');
        setReconnectAttempts(0);
        
        // Simulate periodic messages
        const messageInterval = setInterval(() => {
          setLastMessage({
            type: 'price_update',
            data: {
              pair: 'ETH/USD',
              price: 2000 + (Math.random() - 0.5) * 100,
              timestamp: Date.now()
            }
          });
        }, 5000);

        return () => clearInterval(messageInterval);
      } else {
        setConnectionStatus('error');
        setReconnectAttempts(prev => prev + 1);
      }
    }, 1500 + Math.random() * 1000);

    return () => clearTimeout(timer);
  }, [url, reconnectAttempts]);

  return { 
    connectionStatus, 
    lastMessage, 
    reconnectAttempts 
  };
};
