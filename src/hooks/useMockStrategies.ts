import { useState, useEffect } from 'react';
import { Strategy } from '../types';

export const useMockStrategies = () => {
  const [strategies] = useState<Strategy[]>([
    { 
      id: 1, 
      name: 'Tri-Arbitrage V2', 
      description: 'Advanced three-way arbitrage with ZK privacy',
      pnl: 14.23, 
      active: true, 
      risk_level: 'medium', 
      success_rate: 89,
      execution_count: 247,
      avg_profit_per_trade: 0.058,
      last_executed: Date.now() - 120000,
      gas_efficiency: 92,
      creator: 'Artemis AI',
      creation_date: Date.now() - 7200000,
      category: 'arbitrage',
      historical_performance: Array.from({length: 24}, (_, i) => ({
        timestamp: Date.now() - (23 - i) * 3600000,
        pnl: Math.random() * 0.5 + 0.3
      }))
    },
    { 
      id: 2, 
      name: 'MEV Backrun', 
      description: 'Backrunning MEV opportunities with advanced filtering',
      pnl: 8.91, 
      active: true, 
      risk_level: 'high', 
      success_rate: 76,
      execution_count: 89,
      avg_profit_per_trade: 0.1,
      last_executed: Date.now() - 45000,
      gas_efficiency: 78,
      creator: 'Community',
      creation_date: Date.now() - 14400000,
      category: 'mev',
      historical_performance: Array.from({length: 24}, (_, i) => ({
        timestamp: Date.now() - (23 - i) * 3600000,
        pnl: Math.random() * 0.8 + 0.1
      }))
    },
    { 
      id: 3, 
      name: 'Flash-Mint Hedge', 
      description: 'Delta-neutral positions using flash minting',
      pnl: 5.12, 
      active: false, 
      risk_level: 'low', 
      success_rate: 94,
      execution_count: 156,
      avg_profit_per_trade: 0.033,
      last_executed: Date.now() - 3600000,
      gas_efficiency: 88,
      creator: 'Artemis AI',
      creation_date: Date.now() - 21600000,
      category: 'yield',
      historical_performance: Array.from({length: 24}, (_, i) => ({
        timestamp: Date.now() - (23 - i) * 3600000,
        pnl: Math.random() * 0.3 + 0.1
      }))
    },
    { 
      id: 4, 
      name: 'Cross-DEX Arb', 
      description: 'Cross-exchange arbitrage with optimal routing',
      pnl: 3.45, 
      active: true, 
      risk_level: 'medium', 
      success_rate: 82,
      execution_count: 134,
      avg_profit_per_trade: 0.026,
      last_executed: Date.now() - 180000,
      gas_efficiency: 85,
      creator: 'Community',
      creation_date: Date.now() - 10800000,
      category: 'arbitrage',
      historical_performance: Array.from({length: 24}, (_, i) => ({
        timestamp: Date.now() - (23 - i) * 3600000,
        pnl: Math.random() * 0.4 + 0.05
      }))
    },
    { 
      id: 5, 
      name: 'Yield Optimizer', 
      description: 'Automated yield farming with compound optimization',
      pnl: 2.17, 
      active: true, 
      risk_level: 'low', 
      success_rate: 91,
      execution_count: 67,
      avg_profit_per_trade: 0.032,
      last_executed: Date.now() - 300000,
      gas_efficiency: 95,
      creator: 'Artemis AI',
      creation_date: Date.now() - 18000000,
      category: 'yield',
      historical_performance: Array.from({length: 24}, (_, i) => ({
        timestamp: Date.now() - (23 - i) * 3600000,
        pnl: Math.random() * 0.2 + 0.1
      }))
    }
  ]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // Simulate loading delay
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1200);

    return () => clearTimeout(timer);
  }, []);

  return { 
    data: strategies, 
    isLoading, 
    error 
  };
};
