import React, { useState, useEffect } from 'react';
import { useSocket } from './hooks/useSocket';
import { StatusCards } from './components/StatusCards';
import { EventLog } from './components/EventLog';
import { TransactionMonitor } from './components/TransactionMonitor';
import { SecurityAlerts } from './components/SecurityAlerts';

// Define the shape of our system's state
interface SystemState {
    status: string;
    events: any[];
    trade_counts: { success: number; error: number; info: number };
}

/**
 * Main Dashboard component that integrates all monitoring components
 */
export const Dashboard: React.FC = () => {
    const socket = useSocket();
    const [state, setState] = useState<SystemState>({
        status: 'Connecting...',
        events: [],
        trade_counts: { success: 0, error: 0, info: 0 },
    });

    useEffect(() => {
        if (!socket) return;

        // Listener for the full initial state
        socket.on('initial_state', (initialState: SystemState) => {
            console.log('Received initial state:', initialState);
            setState(initialState);
        });

        // Listener for live event updates
        socket.on('new_event', (event: any) => {
            console.log('Received new event:', event);
            setState(prevState => ({
                ...prevState,
                events: [event, ...prevState.events],
            }));
        });
        
        // Listener for summary status updates
        socket.on('status_update', (statusUpdate: {status: string, trade_counts: any}) => {
            console.log('Received status update:', statusUpdate);
            setState(prevState => ({
                ...prevState,
                status: statusUpdate.status,
                trade_counts: statusUpdate.trade_counts,
            }));
        });

        // Cleanup listeners on component unmount
        return () => {
            socket.off('initial_state');
            socket.off('new_event');
            socket.off('status_update');
        };
    }, [socket]);

    const mainStyle: React.CSSProperties = {
        fontFamily: "'Courier New', monospace",
        backgroundColor: '#0d1117',
        color: '#c9d1d9',
        padding: '20px',
        minHeight: '100vh',
    };

    return (
        <main style={mainStyle}>
            <h1>Arbitrage Bot Real-Time Dashboard</h1>
            <StatusCards 
                status={state.status}
                successCount={state.trade_counts.success}
                errorCount={state.trade_counts.error}
            />
            <SecurityAlerts events={state.events} />
            <TransactionMonitor events={state.events} />
            <EventLog events={state.events} />
        </main>
    );
};