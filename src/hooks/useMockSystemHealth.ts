import { useState, useEffect } from 'react';
import { SystemHealth } from '../types';

export const useMockSystemHealth = () => {
  const [systemHealth] = useState<SystemHealth>({
    'Oracle Service': 'Operational',
    'MEV Sentinel': 'Operational', 
    'Risk Engine': 'Operational',
    'Gas Sentinel': 'Operational',
    'MATLAB Bridge': 'Degraded',
    'Database Cluster': 'Operational',
    'Trading Engine': 'Operational',
    'AI Analytics': 'Operational'
  });

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // Simulate loading delay
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  return { 
    data: systemHealth, 
    isLoading, 
    error 
  };
};
