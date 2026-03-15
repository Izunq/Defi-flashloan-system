import React from 'react';

interface Event {
    timestamp: string;
    status: 'info' | 'success' | 'error' | 'security';
    message: string;
    [key: string]: any;
}

interface EventLogProps {
    events: Event[];
}

const statusColors = {
    info: '#a371f7',
    success: '#3fb950',
    error: '#f85149',
    security: '#e3b341',
};

/**
 * Component to display a live feed of all system events
 */
export const EventLog: React.FC<EventLogProps> = ({ events }) => {
    return (
        <div>
            <h2 style={{ color: '#58a6ff' }}>Live Event Log</h2>
            <div style={{ backgroundColor: '#010409', border: '1px solid #30363d', padding: '15px', height: '40vh', overflowY: 'scroll', borderRadius: '6px' }}>
                {events.map((event, index) => (
                    <div key={index} style={{ padding: '5px', borderBottom: '1px dashed #30363d', color: statusColors[event.status] || '#c9d1d9' }}>
                        <span>[{new Date(event.timestamp).toLocaleTimeString()}]</span>
                        <span style={{ fontWeight: 'bold', margin: '0 10px' }}>[{event.status.toUpperCase()}]</span>
                        <span>{event.message}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};