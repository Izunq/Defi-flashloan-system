import { useState, useEffect } from 'react';
import { Alert } from '../types';

export const useMockAlerts = () => {
  const [alerts] = useState<Alert[]>([
    {
      id: 1,
      source: 'Oracle Sentinel',
      message: 'ETH/USD oracle deviation detected: 1.7% above market average',
      level: 'critical',
      timestamp: Date.now() - 300000,
      metadata: { 
        pair: 'ETH/USD', 
        deviation: 1.7, 
        threshold: 1.5,
        impact: 'high',
        affectedStrategies: ['Tri-Arbitrage V2', 'Cross-DEX Arb'],
        suggestedActions: ['Pause affected strategies', 'Switch to backup oracle']
      }
    },
    {
      id: 2,
      source: 'Risk Engine',
      message: 'Portfolio exposure approaching warning threshold: 78% ETH correlation',
      level: 'warning',
      timestamp: Date.now() - 900000,
      metadata: {
        impact: 'medium',
        affectedStrategies: ['MEV Backrun', 'Yield Optimizer'],
        suggestedActions: ['Consider diversification', 'Implement hedging']
      }
    },
    {
      id: 3,
      source: 'Gas Sentinel',
      message: 'Gas prices elevated: 65 gwei (normal: 25 gwei)',
      level: 'info',
      timestamp: Date.now() - 600000,
      metadata: {
        impact: 'low',
        suggestedActions: ['Monitor gas efficiency', 'Consider L2 alternatives']
      }
    },
    {
      id: 4,
      source: 'MEV Sentinel',
      message: 'High-value MEV opportunity detected: potential 2.3 ETH profit',
      level: 'info',
      timestamp: Date.now() - 1200000,
      metadata: {
        impact: 'high',
        suggestedActions: ['Execute MEV strategy', 'Monitor competition']
      }
    }
  ]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // Simulate loading delay
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 800);

    return () => clearTimeout(timer);
  }, []);

  return { 
    data: alerts, 
    isLoading, 
    error 
  };
};
