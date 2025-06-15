// Blockchain Integration Test
// Tests interaction with actual blockchain contracts

const { ethers } = require('ethers');
const axios = require('axios');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env.test') });

// Configuration
const RPC_URL = process.env.TEST_RPC_URL || 'http://localhost:8545';
const PRIVATE_KEY = process.env.TEST_PRIVATE_KEY;
const BACKEND_URL = process.env.TEST_BACKEND_URL || 'http://localhost:8080';
const WS_ENDPOINT = process.env.TEST_WS_ENDPOINT || 'ws://localhost:8080';

// Contract addresses (should be set in .env.test)
const INCUBATOR_ADDRESS = process.env.TEST_INCUBATOR_ADDRESS;
const EXECUTOR_ADDRESS = process.env.TEST_EXECUTOR_ADDRESS;
const FACTORY_ADDRESS = process.env.TEST_FACTORY_ADDRESS;

// Load contract ABIs
const incubatorABI = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../abi/StrategyIncubatorV33.json'), 'utf8'));
const executorABI = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../abi/ArbitrageExecutorV33.json'), 'utf8'));
const factoryABI = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../abi/StrategyFactoryV33.json'), 'utf8'));

// Initialize provider and signer
const provider = new ethers.providers.JsonRpcProvider(RPC_URL);
const wallet = new ethers.Wallet(PRIVATE_KEY, provider);

// Initialize contract instances
const incubator = new ethers.Contract(INCUBATOR_ADDRESS, incubatorABI, wallet);
const executor = new ethers.Contract(EXECUTOR_ADDRESS, executorABI, wallet);
const factory = new ethers.Contract(FACTORY_ADDRESS, factoryABI, wallet);

// Test results
const testResults = {
    total: 0,
    passed: 0,
    failed: 0,
    skipped: 0,
    results: []
};

// Test utilities
function logTest(name, result, error = null) {
    const status = result ? 'PASSED' : 'FAILED';
    console.log(`[${status}] ${name}`);
    if (error) {
        console.error(`  Error: ${error.message}`);
    }
    
    testResults.total++;
    if (result) {
        testResults.passed++;
    } else {
        testResults.failed++;
    }
    
    testResults.results.push({
        name,
        status,
        error: error ? error.message : null
    });
}

async function runTest(name, testFn) {
    try {
        await testFn();
        logTest(name, true);
    } catch (error) {
        logTest(name, false, error);
    }
}

// Tests
async function testBlockchainConnection() {
    const blockNumber = await provider.getBlockNumber();
    if (blockNumber <= 0) {
        throw new Error('Could not get block number');
    }
    console.log(`  Current block number: ${blockNumber}`);
}

async function testContractInteraction() {
    // Test read-only function on Incubator
    const strategyCount = await incubator.getStrategyCount();
    console.log(`  Strategy count: ${strategyCount.toString()}`);
    
    // Test read-only function on Executor
    const owner = await executor.owner();
    console.log(`  Executor owner: ${owner}`);
    
    // Test read-only function on Factory
    const factoryOwner = await factory.owner();
    console.log(`  Factory owner: ${factoryOwner}`);
}

async function testBackendAPI() {
    // Test health endpoint
    const healthResponse = await axios.get(`${BACKEND_URL}/health`);
    if (healthResponse.status !== 200 || healthResponse.data.status !== 'ok') {
        throw new Error(`Health check failed: ${JSON.stringify(healthResponse.data)}`);
    }
    console.log(`  Backend version: ${healthResponse.data.version}`);
    
    // Test strategies endpoint
    const strategiesResponse = await axios.get(`${BACKEND_URL}/api/strategies`);
    if (strategiesResponse.status !== 200) {
        throw new Error('Failed to get strategies');
    }
    console.log(`  Retrieved ${strategiesResponse.data.length} strategies`);
}

async function testWebSocketConnection() {
    return new Promise((resolve, reject) => {
        const ws = new WebSocket(WS_ENDPOINT);
        
        const timeout = setTimeout(() => {
            ws.close();
            reject(new Error('WebSocket connection timeout'));
        }, 5000);
        
        ws.on('open', () => {
            console.log('  WebSocket connection established');
            ws.send(JSON.stringify({ type: 'subscribe', channel: 'strategies' }));
        });
        
        ws.on('message', (data) => {
            console.log(`  Received WebSocket message: ${data}`);
            clearTimeout(timeout);
            ws.close();
            resolve();
        });
        
        ws.on('error', (error) => {
            clearTimeout(timeout);
            reject(error);
        });
    });
}

// Main test runner
async function runTests() {
    console.log('Starting blockchain integration tests...');
    
    await runTest('Blockchain Connection', testBlockchainConnection);
    await runTest('Contract Interaction', testContractInteraction);
    await runTest('Backend API', testBackendAPI);
    await runTest('WebSocket Connection', testWebSocketConnection);
    
    // Print summary
    console.log('\nTest Summary:');
    console.log(`Total: ${testResults.total}`);
    console.log(`Passed: ${testResults.passed}`);
    console.log(`Failed: ${testResults.failed}`);
    console.log(`Skipped: ${testResults.skipped}`);
    
    // Write results to file
    fs.writeFileSync(
        path.resolve(__dirname, 'test-results.json'),
        JSON.stringify(testResults, null, 2)
    );
    
    // Exit with appropriate code
    process.exit(testResults.failed > 0 ? 1 : 0);
}

// Run tests
runTests().catch(error => {
    console.error('Test runner error:', error);
    process.exit(1);
});