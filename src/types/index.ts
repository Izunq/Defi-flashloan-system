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
    id: string;
    address: string;
    status: StrategyStatus;
    proposer: string;
    reputation: number;
    report: StrategyReport | null;
    proposalTimestamp: number;
    testsPassed: number;
    testsFailed: number;
}
