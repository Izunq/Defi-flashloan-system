import React from 'react';

// Define a more specific type for your events
interface AppEvent {
    timestamp: string;
    status: 'info' | 'success' | 'error' | 'security';
    message: string;
    [key: string]: any;
}

interface SecurityAlertsProps {
    events: AppEvent[];
}

/**
 * Component to display security-related alerts
 */
export const SecurityAlerts: React.FC<SecurityAlertsProps> = ({ events }) => {
    // We will define security events as events with status 'security'
    const securityEvents = events.filter(e => e.status === 'security');

    return (
        <div style={{marginTop: '20px'}}>
            <h2 style={{ color: '#e3b341' }}>Security Alerts</h2>
             <div style={{ border: '2px solid #e3b341', borderRadius: '6px', padding: '15px', background: 'rgba(227, 179, 65, 0.1)' }}>
                {securityEvents.length === 0 ? <p>No security alerts.</p> :
                    securityEvents.map((event, index) => (
                        <div key={index} style={{ color: '#e3b341', borderBottom: '1px solid rgba(227, 179, 65, 0.5)', padding: '8px 0' }}>
                            <strong>[{new Date(event.timestamp).toLocaleTimeString()}]</strong> {event.message}
                        </div>
                    ))
                }
            </div>
        </div>
    );
};