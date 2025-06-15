const axios = require('axios');
const WebSocket = require('ws');

// Configuration
const API_URL = process.env.API_URL || 'http://localhost:8080';
const WS_URL = process.env.WS_URL || 'ws://localhost:8080';
const API_KEY = process.env.API_KEY || 'your_api_key_here';

// Test REST API endpoints
async function testRestAPI() {
  console.log('Testing REST API endpoints...');
  
  try {
    // Test health endpoint
    console.log('\nTesting health endpoint...');
    const healthResponse = await axios.get(`${API_URL}/health`);
    console.log('Health check:', healthResponse.data);
    
    // Test AI insights endpoint
    console.log('\nTesting AI insights endpoint...');
    const insightsResponse = await axios.get(`${API_URL}/api/ai/insights`);
    console.log(`Received ${insightsResponse.data.length} insights`);
    console.log('First insight:', insightsResponse.data[0]);
    
    // Test ZK proofs endpoint
    console.log('\nTesting ZK proofs endpoint...');
    const proofsResponse = await axios.get(`${API_URL}/api/zk/proofs`);
    console.log(`Received ${proofsResponse.data.length} proofs`);
    console.log('First proof:', proofsResponse.data[0]);
    
    // Test strategy endpoint
    console.log('\nTesting strategy endpoint...');
    const strategyResponse = await axios.get(`${API_URL}/api/strategy/1`);
    console.log('Strategy data:', strategyResponse.data);
    
    // Test strategy performance endpoint
    console.log('\nTesting strategy performance endpoint...');
    const performanceResponse = await axios.get(`${API_URL}/api/strategy/1/performance`);
    console.log('Performance data:', performanceResponse.data);
    
    // Test strategy history endpoint
    console.log('\nTesting strategy history endpoint...');
    const historyResponse = await axios.get(`${API_URL}/api/strategy/1/history`);
    console.log('History data:', historyResponse.data);
    
    // Test strategy simulation endpoint
    console.log('\nTesting strategy simulation endpoint...');
    const simulationResponse = await axios.post(
      `${API_URL}/api/strategy/1/simulate`,
      { parameters: { maxCapital: '1000000000000000000', slippage: 50 } },
      { headers: { 'x-api-key': API_KEY } }
    );
    console.log('Simulation result:', simulationResponse.data);
    
    console.log('\nAll REST API tests completed successfully!');
  } catch (error) {
    console.error('Error testing REST API:', error.response?.data || error.message);
  }
}

// Test WebSocket connections
function testWebSocket() {
  console.log('\nTesting WebSocket connections...');
  
  const ws = new WebSocket(WS_URL);
  
  ws.on('open', () => {
    console.log('WebSocket connected');
    
    // Subscribe to channels
    ws.send(JSON.stringify({ type: 'subscribe', channel: 'ai_insights' }));
    ws.send(JSON.stringify({ type: 'subscribe', channel: 'zk_proofs' }));
    ws.send(JSON.stringify({ type: 'subscribe', channel: 'strategy_updates' }));
    
    // Send ping
    ws.send(JSON.stringify({ type: 'ping' }));
    
    console.log('Subscribed to channels, waiting for messages...');
    
    // Close connection after 10 seconds
    setTimeout(() => {
      console.log('Closing WebSocket connection...');
      ws.close();
    }, 10000);
  });
  
  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data);
      console.log('Received message:', message);
    } catch (error) {
      console.error('Error parsing message:', error);
    }
  });
  
  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
  
  ws.on('close', () => {
    console.log('WebSocket disconnected');
    console.log('\nAll WebSocket tests completed!');
  });
}

// Run tests
async function runTests() {
  await testRestAPI();
  testWebSocket();
}

runTests();