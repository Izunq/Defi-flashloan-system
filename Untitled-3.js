// =================================================================================================
// PROJECT: ADVANCED FLASH LOAN ARBITRAGE SYSTEM - V33 (FINALIZED FRONTEND)
// =================================================================================================

// =================================================================================================
// FILE: src/components/IncubatorDashboard.tsx (Finalized)
// =================================================================================================
/*
import React, { useState, useEffect, useMemo, FC } from 'react';
import { useIncubatorData } from '../hooks/useIncubatorData';
import { Strategy } from '../types';
import BacktestReportViewer from './BacktestReportViewer';

// A new, dedicated component for rendering a single strategy item in the list
const StrategyItem: FC<{ strategy: Strategy; isVariant?: boolean; isSelected: boolean; onSelect: (id: string) => void; }> = 
({ strategy, isVariant = false, isSelected, onSelect }) => (
    <li
        key={strategy.id}
        className={`strategy-item ${isSelected ? 'selected' : ''}`}
        style={{ marginLeft: isVariant ? '2rem' : '0' }}
        onClick={() => onSelect(strategy.id)}
    >
        <span className="address">{isVariant ? '↳ ' : ''}{strategy.address.substring(0, 6)}...{strategy.address.substring(38)}</span>
        <span className={`status status-${strategy.status}`}>{strategy.status}</span>
    </li>
);

const IncubatorDashboard: React.FC = () => {
    const { strategies, isLoading, error } = useIncubatorData();
    const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);

    const strategyTree = useMemo(() => {
        // ... same logic from previous turn ...
    }, [strategies]);

    // ... useEffect to select first strategy ...
    const selectedStrategy = strategies.find(s => s.id === selectedStrategyId);

    return (
        <div className="dashboard-grid">
            <div className="panel">
                <h2>Incubated Strategies</h2>
                {isLoading ? <div className="loading">Loading...</div> : (
                    <ul className="strategy-list">
                        {strategyTree.baseStrategies.map(base => (
                            <React.Fragment key={base.id}>
                                <StrategyItem
                                    strategy={base}
                                    isSelected={selectedStrategyId === base.id}
                                    onSelect={setSelectedStrategyId}
                                />
                                {strategyTree.tree[base.id]?.map(variant => (
                                    <StrategyItem
                                        key={variant.id}
                                        strategy={variant}
                                        isVariant={true}
                                        isSelected={selectedStrategyId === variant.id}
                                        onSelect={setSelectedStrategyId}
                                    />
                                ))}
                            </React.Fragment>
                        ))}
                    </ul>
                )}
            </div>
            <BacktestReportViewer strategy={selectedStrategy} />
        </div>
    );
};

export default IncubatorDashboard;
*/
