// Load Testing Script for Flashloan System
// Tests system performance under high load

const axios = require('axios');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
require('dotenv').config({ path: path.resolve(__dirname, '../.env.test') });

// Configuration
const BACKEND_URL = process.env.TEST_BACKEND_URL || 'http://localhost:8080';
const WS_ENDPOINT = process.env.TEST_WS_ENDPOINT || 'ws://localhost:8080';
const NUM_WORKERS = process.env.NUM_WORKERS ? parseInt(process.env.NUM_WORKERS) : 4;
const REQUESTS_PER_WORKER = process.env.REQUESTS_PER_WORKER ? parseInt(process.env.REQUESTS_PER_WORKER) : 100;
const REQUEST_INTERVAL_MS = process.env.REQUEST_INTERVAL_MS ? parseInt(process.env.REQUEST_INTERVAL_MS) : 50;
const TEST_DURATION_SEC = process.env.TEST_DURATION_SEC ? parseInt(process.env.TEST_DURATION_SEC) : 60;

// Worker implementation
if (!isMainThread) {
    const { workerId, endpoint, requestsPerWorker, requestIntervalMs, testDurationSec } = workerData;
    
    const results = {
        workerId,
        requests: 0,
        successful: 0,
        failed: 0,
        latencies: [],
        errors: []
    };
    
    const endTime = Date.now() + (testDurationSec * 1000);
    
    async function makeRequest() {
        if (Date.now() >= endTime || results.requests >= requestsPerWorker) {
            parentPort.postMessage(results);
            return;
        }
        
        const startTime = Date.now();
        results.requests++;
        
        try {
            const response = await axios.get(`${endpoint}/api/strategies`);
            const latency = Date.now() - startTime;
            
            results.successful++;
            results.latencies.push(latency);
            
            if (results.requests % 10 === 0) {
                console.log(`Worker ${workerId}: Completed ${results.requests} requests`);
            }
        } catch (error) {
            results.failed++;
            results.errors.push({
                request: results.requests,
                error: error.message,
                time: new Date().toISOString()
            });
        }
        
        setTimeout(makeRequest, requestIntervalMs);
    }
    
    // Start making requests
    makeRequest();
}
// Main thread implementation
else {
    console.log(`Starting load test with ${NUM_WORKERS} workers`);
    console.log(`Each worker will make ${REQUESTS_PER_WORKER} requests with ${REQUEST_INTERVAL_MS}ms interval`);
    console.log(`Test will run for a maximum of ${TEST_DURATION_SEC} seconds`);
    
    const workers = [];
    const results = {
        startTime: new Date().toISOString(),
        endTime: null,
        totalRequests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        averageLatency: 0,
        p50Latency: 0,
        p95Latency: 0,
        p99Latency: 0,
        maxLatency: 0,
        requestsPerSecond: 0,
        workerResults: []
    };
    
    // Create workers
    for (let i = 0; i < NUM_WORKERS; i++) {
        const worker = new Worker(__filename, {
            workerData: {
                workerId: i,
                endpoint: BACKEND_URL,
                requestsPerWorker: REQUESTS_PER_WORKER,
                requestIntervalMs: REQUEST_INTERVAL_MS,
                testDurationSec: TEST_DURATION_SEC
            }
        });
        
        worker.on('message', (workerResult) => {
            results.workerResults.push(workerResult);
            
            // Check if all workers have completed
            if (results.workerResults.length === NUM_WORKERS) {
                processResults();
            }
        });
        
        worker.on('error', (error) => {
            console.error(`Worker ${i} error:`, error);
        });
        
        workers.push(worker);
    }
    
    function processResults() {
        results.endTime = new Date().toISOString();
        
        // Aggregate results
        const allLatencies = [];
        
        results.workerResults.forEach(workerResult => {
            results.totalRequests += workerResult.requests;
            results.successfulRequests += workerResult.successful;
            results.failedRequests += workerResult.failed;
            allLatencies.push(...workerResult.latencies);
        });
        
        // Sort latencies for percentile calculations
        allLatencies.sort((a, b) => a - b);
        
        // Calculate statistics
        const testDurationMs = new Date(results.endTime) - new Date(results.startTime);
        results.requestsPerSecond = (results.totalRequests / (testDurationMs / 1000)).toFixed(2);
        
        if (allLatencies.length > 0) {
            results.averageLatency = allLatencies.reduce((sum, latency) => sum + latency, 0) / allLatencies.length;
            results.p50Latency = allLatencies[Math.floor(allLatencies.length * 0.5)];
            results.p95Latency = allLatencies[Math.floor(allLatencies.length * 0.95)];
            results.p99Latency = allLatencies[Math.floor(allLatencies.length * 0.99)];
            results.maxLatency = allLatencies[allLatencies.length - 1];
        }
        
        // Print summary
        console.log('\nLoad Test Results:');
        console.log(`Total Requests: ${results.totalRequests}`);
        console.log(`Successful Requests: ${results.successfulRequests}`);
        console.log(`Failed Requests: ${results.failedRequests}`);
        console.log(`Requests Per Second: ${results.requestsPerSecond}`);
        console.log(`Average Latency: ${results.averageLatency.toFixed(2)}ms`);
        console.log(`Median Latency (P50): ${results.p50Latency}ms`);
        console.log(`95th Percentile Latency: ${results.p95Latency}ms`);
        console.log(`99th Percentile Latency: ${results.p99Latency}ms`);
        console.log(`Maximum Latency: ${results.maxLatency}ms`);
        
        // Write results to file
        fs.writeFileSync(
            path.resolve(__dirname, 'load-test-results.json'),
            JSON.stringify(results, null, 2)
        );
        
        console.log('\nTest completed. Results saved to load-test-results.json');
        process.exit(0);
    }
}