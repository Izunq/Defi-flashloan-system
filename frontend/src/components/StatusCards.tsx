import React from 'react';

interface StatusCardsProps {
    status: string;
    successCount: number;
    errorCount: number;
}

const cardStyle: React.CSSProperties = {
    backgroundColor: '#161b22',
    border: '1px solid #30363d',
    padding: '15px',
    borderRadius: '6px',
    textAlign: 'center',
};

const h3Style: React.CSSProperties = { marginTop: 0, color: '#8b949e' };
const pStyle: React.CSSProperties = { fontSize: '24px', margin: 0, fontWeight: 'bold', color: '#c9d1d9' };

/**
 * Component to display high-level system metrics
 */
export const StatusCards: React.FC<StatusCardsProps> = ({ status, successCount, errorCount }) => {
    return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px', marginBottom: '20px' }}>
            <div style={cardStyle}>
                <h3 style={h3Style}>System Status</h3>
                <p style={pStyle}>{status}</p>
            </div>
            <div style={cardStyle}>
                <h3 style={h3Style}>Successful Trades</h3>
                <p style={{...pStyle, color: '#3fb950'}}>{successCount}</p>
            </div>
            <div style={cardStyle}>
                <h3 style={h3Style}>Failed Trades</h3>
                <p style={{...pStyle, color: '#f85149'}}>{errorCount}</p>
            </div>
        </div>
    );
};