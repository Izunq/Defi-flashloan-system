export interface SystemStatus {
  uptime: number;
  chain_id: number;
  block_number: number;
  gas_price: number;
  is_scanning: boolean;
  is_executing: boolean;
}

export interface Opportunity {
  pair: string;
  dex_a: string;
  dex_b: string;
  price_a: number;
  price_b: number;
  spread_pct: number;
  amount_in: string;
  timestamp: number;
}

export interface Trade {
  tx_hash: string;
  success: boolean;
  profit_actual: string;
  gas_used: number;
  gas_price: number;
  timestamp: number;
  error: string | null;
}

export interface PnL {
  total_profit_wei: string;
  total_profit_usd: number;
  total_gas_spent: string;
  net_profit: number;
  trade_count: number;
}

export interface PoolStatus {
  tvl: string;
  provider_count: number;
  total_profit: string;
  utilization: number;
  provider_share_bps: number;
  mudarib_share_bps: number;
}
