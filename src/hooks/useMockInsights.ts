import { useState, useEffect } from 'react';
import { Insight } from '../types';

export const useMockInsights = () => {
  const [insights] = useState<Insight[]>([
    {
      id: 'insight-1',
      title: 'High-Profit Arbitrage Window Detected',
      description: 'ETH/USDC spread on Uniswap vs SushiSwap shows 0.23% opportunity with low risk',
      confidence: 87,
      category: 'opportunity',
      timestamp: Date.now() - 180000,
      relatedStrategies: [1, 4]
    },
    {
      id: 'insight-2', 
      title: 'Gas Price Optimization Opportunity',
      description: 'Current gas prices 40% below daily average - optimal time for high-frequency strategies',
      confidence: 92,
      category: 'optimization',
      timestamp: Date.now() - 420000,
      relatedStrategies: [2, 1]
    },
    {
      id: 'insight-3',
      title: 'Risk Threshold Alert',
      description: 'Portfolio correlation to ETH exceeds recommended threshold of 70%',
      confidence: 95,
      category: 'risk',
      timestamp: Date.now() - 600000,
      relatedStrategies: [1, 2, 4]
    },
    {
      id: 'insight-4',
      title: 'Emerging DeFi Yield Opportunity',
      description: 'New liquidity pool on Curve showing 15.2% APY with moderate risk profile',
      confidence: 78,
      category: 'opportunity',
      timestamp: Date.now() - 900000,
      relatedStrategies: [5]
    },
    {
      id: 'insight-5',
      title: 'Market Volatility Trending Upward',
      description: 'ETH volatility increased 23% over 24h - favorable for MEV strategies',
      confidence: 85,
      category: 'trend',
      timestamp: Date.now() - 1200000,
      relatedStrategies: [2]
    }
  ]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // Simulate loading delay
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 900);

    return () => clearTimeout(timer);
  }, []);

  return { 
    data: insights, 
    isLoading, 
    error 
  };
};
