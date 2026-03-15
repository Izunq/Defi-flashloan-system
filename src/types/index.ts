export const STRATEGY_STATUS = {
    APPROVED: 'Approved',
    LIVE_TESTING: 'LiveTesting',
    PROPOSED: 'Proposed',
    REJECTED: 'Rejected',
    SLASHED: 'Slashed',
} as const;

type ValueOf<T> = T[keyof T];
export type StrategyStatus = ValueOf<typeof STRATEGY_STATUS>;

export interface StrategyReport {
    aiConfidenceScore: number;
    simulatedProfit: number;
}

export interface Strategy {
    id: number;
    name: string;
    description?: string;
    pnl: number;
    active: boolean;
    risk_level: 'low' | 'medium' | 'high';
    success_rate?: number;
    execution_count?: number;
    avg_profit_per_trade?: number;
    last_executed?: number;
    gas_efficiency?: number;
    creator?: string;
    creation_date?: number;
    category?: 'arbitrage' | 'yield' | 'mev' | 'cross-chain' | 'other';
    historical_performance?: {
        timestamp: number;
        pnl: number;
    }[];
    address?: string;
    status?: StrategyStatus;
    proposer?: string;
    reputation?: number;
    report?: StrategyReport | null;
    proposalTimestamp?: number;
    testsPassed?: number;
    testsFailed?: number;
}

export interface Alert {
    id: number;
    source: string;
    message: string;
    level: 'critical' | 'warning' | 'info';
    timestamp: number;
    isRead?: boolean;
    isAcknowledged?: boolean;
    metadata?: {
        pair?: string;
        deviation?: number;
        threshold?: number;
        exchanges?: string[];
        impact?: 'high' | 'medium' | 'low';
        affectedStrategies?: string[];
        suggestedActions?: string[];
    };
}

export interface ChatMessage {
    id: string;
    text: string;
    sender: 'user' | 'ai';
    timestamp: number;
    isProcessing?: boolean;
    attachments?: {
        type: 'chart' | 'strategy' | 'alert' | 'code';
        data: any;
    }[];
}

export interface Insight {
    id: string;
    title: string;
    description: string;
    confidence: number;
    category: 'opportunity' | 'risk' | 'optimization' | 'trend';
    timestamp: number;
    relatedStrategies?: number[];
}

export interface SystemHealth {
    [service: string]: 'Operational' | 'Degraded' | 'Outage';
}

export interface SystemMetrics {
    cpu_usage: number;
    memory_usage: number;
    network_latency: number;
    active_connections: number;
    transactions_per_minute: number;
    uptime: number;
    historical_data: {
        timestamp: number;
        transactions: number;
        success_rate: number;
    }[];
}
