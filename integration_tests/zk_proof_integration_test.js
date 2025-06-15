// ZK Proof Integration Test
// Tests the complete ZK proof generation, submission, and verification flow

const { ethers } = require('ethers');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
require('dotenv').config({ path: path.resolve(__dirname, '../.env.test') });

// Configuration
const RPC_URL = process.env.TEST_RPC_URL || 'http://localhost:8545';
const PRIVATE_KEY = process.env.TEST_PRIVATE_KEY;
const BACKEND_URL = process.env.TEST_BACKEND_URL || 'http://localhost:8080';
const API_KEY = process.env.TEST_API_KEY || 'test-api-key';

// Contract addresses (should be set in .env.test)
const TRUST_CURVE_ADDRESS = process.env.TEST_TRUST_CURVE_ADDRESS;
const AI_STRATEGY_ADDRESS = process.env.TEST_AI_STRATEGY_ADDRESS;
const ZK_VERIFIER_ADDRESS = process.env.TEST_ZK_VERIFIER_ADDRESS;

// Load contract ABIs
const trustCurveABI = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../abi/TrustCurve.json'), 'utf8'));
const aiStrategyABI = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../abi/AIStrategyV35.json'), 'utf8'));
const zkVerifierABI = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../abi/ZKVerifier.json'), 'utf8'));

// Initialize provider and signer
const provider = new ethers.providers.JsonRpcProvider(RPC_URL);
const wallet = new ethers.Wallet(PRIVATE_KEY, provider);

// Initialize contract instances
const trustCurve = new ethers.Contract(TRUST_CURVE_ADDRESS, trustCurveABI, wallet);
const aiStrategy = new ethers.Contract(AI_STRATEGY_ADDRESS, aiStrategyABI, wallet);
const zkVerifier = new ethers.Contract(ZK_VERIFIER_ADDRESS, zkVerifierABI, wallet);

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
        if (error.stack) {
            console.error(`  Stack: ${error.stack}`);
        }
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
    // Test TrustCurve contract
    const strategyId = 1;
    const scorecard = await trustCurve.getStrategyScorecard(strategyId);
    console.log(`  Strategy ${strategyId} trust score: ${scorecard.trustScore.toString()}`);
    
    // Test AIStrategy contract
    const strategyInfo = await aiStrategy.getStrategyInfo();
    console.log(`  Strategy name: ${strategyInfo._name}`);
    
    // Test ZKVerifier contract
    const verificationKeyHash = await zkVerifier.getVerificationKeyHash();
    console.log(`  Verification key hash: ${verificationKeyHash}`);
}

async function testZKProofGeneration() {
    // Run the Python script to generate a ZK proof
    console.log('  Generating ZK proof...');
    const result = execSync('python ../test_zk_proof.py --strategy-id 1 --profit 100.0 --intelligence 75', { encoding: 'utf8' });
    console.log(`  ${result}`);
    
    if (!result.includes('ZK proof generation PASSED')) {
        throw new Error('ZK proof generation failed');
    }
}

async function testZKProofSubmission() {
    // Generate a ZK proof
    console.log('  Generating ZK proof for submission...');
    const result = execSync('python ../test_zk_proof.py --strategy-id 1 --profit 100.0 --intelligence 75 --submit', { encoding: 'utf8' });
    console.log(`  ${result}`);
    
    if (!result.includes('Proof submission PASSED')) {
        throw new Error('ZK proof submission failed');
    }
}

async function testZKProofVerification() {
    // Generate and verify a ZK proof
    console.log('  Generating and verifying ZK proof...');
    const result = execSync('python ../test_zk_proof.py --strategy-id 1 --profit 100.0 --intelligence 75 --submit --verify', { encoding: 'utf8' });
    console.log(`  ${result}`);
    
    if (!result.includes('On-chain verification PASSED')) {
        throw new Error('ZK proof verification failed');
    }
}

async function testBackendAPI() {
    // Test health endpoint
    const healthResponse = await axios.get(`${BACKEND_URL}/api/zk/health`);
    if (healthResponse.status !== 200 || healthResponse.data.status !== 'ok') {
        throw new Error(`Health check failed: ${JSON.stringify(healthResponse.data)}`);
    }
    console.log(`  Backend health: ${healthResponse.data.status}`);
    console.log(`  Backend block number: ${healthResponse.data.blockNumber}`);
    
    // Test proofs endpoint
    const proofsResponse = await axios.get(`${BACKEND_URL}/api/zk/proofs`);
    if (proofsResponse.status !== 200) {
        throw new Error('Failed to get proofs');
    }
    console.log(`  Retrieved ${proofsResponse.data.length} proofs`);
}

async function testEndToEndFlow() {
    // Strategy ID to use for the test
    const strategyId = 1;
    
    // Step 1: Generate a ZK proof
    console.log('  Step 1: Generating ZK proof...');
    const genResult = execSync(`python ../test_zk_proof.py --strategy-id ${strategyId} --profit 100.0 --intelligence 75`, { encoding: 'utf8' });
    if (!genResult.includes('ZK proof generation PASSED')) {
        throw new Error('ZK proof generation failed');
    }
    
    // Step 2: Submit the proof to the backend
    console.log('  Step 2: Submitting proof to backend...');
    const submitResult = execSync(`python ../test_zk_proof.py --strategy-id ${strategyId} --profit 100.0 --intelligence 75 --submit`, { encoding: 'utf8' });
    if (!submitResult.includes('Proof submission PASSED')) {
        throw new Error('ZK proof submission failed');
    }
    
    // Step 3: Verify the proof on-chain
    console.log('  Step 3: Verifying proof on-chain...');
    const verifyResult = execSync(`python ../test_zk_proof.py --strategy-id ${strategyId} --profit 100.0 --intelligence 75 --verify`, { encoding: 'utf8' });
    if (!verifyResult.includes('On-chain verification PASSED')) {
        throw new Error('ZK proof verification failed');
    }
    
    // Step 4: Check that the proof is recorded in TrustCurve
    console.log('  Step 4: Checking TrustCurve record...');
    const scorecard = await trustCurve.getStrategyScorecard(strategyId);
    if (scorecard.lastVerifiedAt.toNumber() === 0) {
        throw new Error('Proof not recorded in TrustCurve');
    }
    console.log(`  Strategy ${strategyId} last verified at: ${new Date(scorecard.lastVerifiedAt.toNumber() * 1000).toISOString()}`);
    console.log(`  Strategy ${strategyId} trust score: ${scorecard.trustScore.toString()}`);
    
    // Step 5: Check that the proof is recorded in AIStrategy
    console.log('  Step 5: Checking AIStrategy record...');
    const zkProofStatus = await aiStrategy.getZKProofStatus();
    if (!zkProofStatus._verified) {
        throw new Error('Proof not recorded in AIStrategy');
    }
    console.log(`  Proof verified: ${zkProofStatus._verified}`);
    console.log(`  Proof expiration: ${new Date(zkProofStatus._expirationTime.toNumber() * 1000).toISOString()}`);
    
    // Step 6: Check that the proof is available via the API
    console.log('  Step 6: Checking API record...');
    const proofResponse = await axios.get(`${BACKEND_URL}/api/zk/proof/${strategyId}`);
    if (proofResponse.status !== 200) {
        throw new Error('Failed to get proof from API');
    }
    console.log(`  Proof retrieved from API: ${proofResponse.data.strategyId}`);
    console.log(`  Proof is valid: ${proofResponse.data.zkProofStatus?.isValid}`);
}

// Main test runner
async function runTests() {
    console.log('Starting ZK proof integration tests...');
    
    await runTest('Blockchain Connection', testBlockchainConnection);
    await runTest('Contract Interaction', testContractInteraction);
    await runTest('Backend API', testBackendAPI);
    await runTest('ZK Proof Generation', testZKProofGeneration);
    await runTest('ZK Proof Submission', testZKProofSubmission);
    await runTest('ZK Proof Verification', testZKProofVerification);
    await runTest('End-to-End Flow', testEndToEndFlow);
    
    // Print summary
    console.log('\nTest Summary:');
    console.log(`Total: ${testResults.total}`);
    console.log(`Passed: ${testResults.passed}`);
    console.log(`Failed: ${testResults.failed}`);
    console.log(`Skipped: ${testResults.skipped}`);
    
    // Write results to file
    fs.writeFileSync(
        path.resolve(__dirname, 'zk-proof-test-results.json'),
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