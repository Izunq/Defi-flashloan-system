import React from 'react';

interface Event {
    timestamp: string;
    status: 'info' | 'success' | 'error';
    message: string;
    tx_hash?: string;
}

interface TransactionMonitorProps {
    events: Event[];
}

/**
 * Component to display a table of blockchain transactions
 */
export const TransactionMonitor: React.FC<TransactionMonitorProps> = ({ events }) => {
    // Filter for events with a tx_hash
    const txEvents = events.filter(e => e.tx_hash);

    return (
        <div style={{marginTop: '20px'}}>
            <h2 style={{ color: '#58a6ff' }}>Transaction Monitor</h2>
            <div style={{ backgroundColor: '#161b22', border: '1px solid #30363d', borderRadius: '6px', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ backgroundColor: '#010409' }}>
                            <th style={{ padding: '10px', textAlign: 'left' }}>Time</th>
                            <th style={{ padding: '10px', textAlign: 'left' }}>Status</th>
                            <th style={{ padding: '10px', textAlign: 'left' }}>Description</th>
                            <th style={{ padding: '10px', textAlign: 'left' }}>Transaction Hash</th>
                        </tr>
                    </thead>
                    <tbody>
                        {txEvents.length === 0 ? (
                            <tr>
                                <td colSpan={4} style={{ padding: '20px', textAlign: 'center' }}>No transactions yet</td>
                            </tr>
                        ) : (
                            txEvents.map((event, index) => (
                                <tr key={index} style={{ borderTop: '1px solid #30363d' }}>
                                    <td style={{ padding: '10px' }}>{new Date(event.timestamp).toLocaleTimeString()}</td>
                                    <td style={{ padding: '10px', color: event.status === 'success' ? '#3fb950' : '#f85149' }}>{event.status}</td>
                                    <td style={{ padding: '10px' }}>{event.message}</td>
                                    <td style={{ padding: '10px' }}>
                                        <a href={`https://etherscan.io/tx/${event.tx_hash}`} target="_blank" rel="noopener noreferrer" style={{ color: '#58a6ff' }}>
                                            {event.tx_hash?.substring(0, 12)}...
                                        </a>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};