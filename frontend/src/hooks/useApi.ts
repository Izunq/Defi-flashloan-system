import { useState, useEffect, useCallback, useRef } from 'react';
import type { SystemStatus, Opportunity, Trade, PnL, PoolStatus } from '../types';

const POLL_INTERVAL = 5000;

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function useApi() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [pnl, setPnl] = useState<PnL | null>(null);
  const [pool, setPool] = useState<PoolStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const pollAll = useCallback(async () => {
    try {
      const [s, oRaw, tRaw, p, pl] = await Promise.all([
        fetchJson<SystemStatus>('/api/status'),
        fetchJson<{ total_found: number; recent: Opportunity[] }>('/api/opportunities'),
        fetchJson<{ total_executed: number; total_successful: number; recent: Trade[] }>('/api/trades'),
        fetchJson<any>('/api/pnl'),
        fetchJson<PoolStatus>('/api/pool'),
      ]);

      if (!mountedRef.current) return;

      setStatus(s);
      setOpportunities(oRaw.recent);
      setTrades(tRaw.recent);
      setPnl({
        total_profit_wei: p.total_profit_wei?.toString() ?? '0',
        total_profit_usd: p.total_profit_usd ?? 0,
        total_gas_spent: p.total_gas_spent?.toString() ?? '0',
        net_profit: p.net_profit_usd ?? 0,
        trade_count: p.trade_count ?? 0,
      });
      setPool(pl);
      setError(null);
    } catch (err) {
      if (!mountedRef.current) return;
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    pollAll();
    const interval = setInterval(pollAll, POLL_INTERVAL);
    return () => {
      mountedRef.current = false;
      clearInterval(interval);
    };
  }, [pollAll]);

  return { status, opportunities, trades, pnl, pool, loading, error };
}
