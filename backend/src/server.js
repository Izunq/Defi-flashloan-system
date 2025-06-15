const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const cors = require('cors');
const bodyParser = require('body-parser');
const { ethers } = require('ethers');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Import routes
const aiRoutes = require('./routes/ai');
const zkRoutes = require('./routes/zk');
const strategyRoutes = require('./routes/strategy');

// Import WebSocket service
const WebSocketService = require('./websocket/WebSocketService');

// Create Express app
const app = express();
const server = http.createServer(app);

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Routes
app.use('/api/ai', aiRoutes);
app.use('/api/zk', zkRoutes);
app.use('/api/strategy', strategyRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', version: 'v35' });
});

// Initialize WebSocket server
const wss = new WebSocket.Server({ server });
const wsService = new WebSocketService(wss);

// Start server
const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`WebSocket server initialized`);
});

// Handle graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    process.exit(0);
  });
});

module.exports = { app, server, wss };