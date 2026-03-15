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
      const [s, o, t, p, pl] = await Promise.all([
        fetchJson<SystemStatus>('/api/status'),
        fetchJson<Opportunity[]>('/api/opportunities'),
        fetchJson<Trade[]>('/api/trades'),
        fetchJson<PnL>('/api/pnl'),
        fetchJson<PoolStatus>('/api/pool'),
      ]);

      if (!mountedRef.current) return;

      setStatus(s);
      setOpportunities(o);
      setTrades(t);
      setPnl(p);
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
