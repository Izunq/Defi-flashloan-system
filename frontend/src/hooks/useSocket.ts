import { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';

const SOCKET_URL = 'http://127.0.0.1:5001';

/**
 * Custom hook for managing WebSocket connections
 * @returns The socket instance or null if not connected
 */
export const useSocket = () => {
    const [socket, setSocket] = useState<Socket | null>(null);

    useEffect(() => {
        // Create a new socket connection
        const newSocket = io(SOCKET_URL);
        setSocket(newSocket);

        // Clean up the socket connection when the component unmounts
        return () => {
            newSocket.close();
        };
    }, []);

    return socket;
};