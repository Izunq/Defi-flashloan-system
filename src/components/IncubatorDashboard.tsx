// filepath: c:\Users\mahia\New_Flashloan\src\components\IncubatorDashboard.tsx
import React, { useState, useEffect } from 'react';
import { useIncubatorData, Strategy, StrategyStatus } from '../hooks/useIncubatorData'; // Assuming this hook exists
import './IncubatorDashboard.css'; // Create this file for styles

// Helper to get status string
const getStatusString = (status: StrategyStatus): string => {
    return StrategyStatus[status];
};

interface StrategyItemProps {
    strategy: Strategy;
    isSelected: boolean;
    onSelect: (strategyId: string) => void;
}

// Production: StrategyItem uses <button> for accessibility and better semantics
const StrategyItem: React.FC<StrategyItemProps> = ({ strategy, isSelected, onSelect }) => {
    return (
    <li className={`strategy-item ${isSelected ? 'selected' : ''}`}>
        <button onClick={() => onSelect(strategy.id)} className="strategy-select-button">
        <div className="strategy-id">ID: {strategy.id}</div>
        <div className="strategy-address">Address: {strategy.strategyAddress}</div>
        <div className="strategy-status">Status: {getStatusString(strategy.status)}</div>
        <div className="strategy-proposer">Proposer: {strategy.proposer}</div>
        {strategy.isVariant && <div className="strategy-variant">Variant of: {strategy.baseStrategyId}</div>}
        <div className="strategy-score">Score: {strategy.performanceScore ?? 'N/A'}</div>
        </button>
    </li>
    );
};

const IncubatorDashboard: React.FC = () => {
    const { strategies, loading, error } = useIncubatorData(); // This hook would fetch real data
    const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);

    const handleSelectStrategy = (strategyId: string) => {
    setSelectedStrategyId(prevId => (prevId === strategyId ? null : strategyId));
    };

    if (loading) return <div className="loading">Loading strategies...</div>;
    if (error) return <div className="error">Error fetching strategies: {error}</div>;
    if (!strategies || strategies.length === 0) return <div className="no-strategies">No strategies found in the incubator.</div>;

    const selectedStrategy = strategies.find(s => s.id === selectedStrategyId);

    return (
    <div className="dashboard-container">
        <header className="dashboard-header">
        <h1>Strategy Incubator Dashboard V33</h1>
        </header>
        <main className="dashboard-main">
        <section className="strategy-list-section">
            <h2>Proposed Strategies</h2>
            {strategies.length > 0 ? (
            <ul className="strategy-list">
                {strategies.map((strategy) => (
                <StrategyItem
                    key={strategy.id}
                    strategy={strategy}
                    isSelected={selectedStrategyId === strategy.id}
                    onSelect={handleSelectStrategy}
                />
                ))}
            </ul>
            ) : (
            <p>No strategies proposed yet.</p>
            )}
        </section>
        
        <aside className="strategy-details-section">
            <h2>Strategy Details</h2>
            {selectedStrategy ? (
            <div className="strategy-details-content">
                <h3>Details for Strategy ID: {selectedStrategy.id}</h3>
                <p><strong>Address:</strong> {selectedStrategy.strategyAddress}</p>
                <p><strong>Status:</strong> {getStatusString(selectedStrategy.status)}</p>
                <p><strong>Proposer:</strong> {selectedStrategy.proposer}</p>
                <p><strong>Is Variant:</strong> {selectedStrategy.isVariant ? `Yes (Base ID: ${selectedStrategy.baseStrategyId})` : 'No'}</p>
                <p><strong>Proposed At:</strong> {new Date(selectedStrategy.proposalTimestamp * 1000).toLocaleString()}</p>
                <p><strong>Performance Score:</strong> {selectedStrategy.performanceScore ?? 'N/A'}</p>
                <p><strong>Tests Passed:</strong> {selectedStrategy.testsPassed ?? 0}</p>
                <p><strong>Tests Failed:</strong> {selectedStrategy.testsFailed ?? 0}</p>
                {/* Add more details and actions (e.g., buttons to approve, reject, test) here */}
                <div className="strategy-actions">
                <button onClick={() => alert(`Approving ${selectedStrategy.id}`)}>Approve</button>
                <button onClick={() => alert(`Rejecting ${selectedStrategy.id}`)}>Reject</button>
                <button onClick={() => alert(`Testing ${selectedStrategy.id}`)}>Run Test</button>
                </div>
            </div>
            ) : (
            <p>Select a strategy to see details.</p>
            )}
        </aside>
        </main>
        <footer className="dashboard-footer">
        <p>Advanced Flash Loan Arbitrage System - V33</p>
        </footer>
    </div>
    );
};

export default IncubatorDashboard;