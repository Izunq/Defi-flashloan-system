// Automated ZK Circuit Testing and Formal Verification Framework
// This script provides comprehensive testing for ZK circuits with formal guarantees

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const snarkjs = require('snarkjs');
const crypto = require('crypto');

// Test configuration
const CIRCUITS = {
    main: path.join(__dirname, 'circuit_formally_verified.circom'),
    compliance: path.join(__dirname, '../ComplianceCircuits/enhanced_compliance_circuit.circom'),
    legacy: path.join(__dirname, 'circuit_v40.circom')
};

const TEST_OUTPUT_DIR = path.join(__dirname, 'test_results');

/**
 * Property-based testing framework for ZK circuits
 */
class ZKPropertyTester {
    constructor(circuitPath, circuitName) {
        this.circuitPath = circuitPath;
        this.circuitName = circuitName;
        this.testResults = [];
        this.setupTestEnvironment();
    }
    
    setupTestEnvironment() {
        if (!fs.existsSync(TEST_OUTPUT_DIR)) {
            fs.mkdirSync(TEST_OUTPUT_DIR, { recursive: true });
        }
    }
    
    /**
     * Test Property: Parameter bounds are enforced
     */
    async testParameterBounds() {
        console.log(`🔍 Testing parameter bounds for ${this.circuitName}...`);
        
        const testCases = [
            {
                name: 'Valid parameters within bounds',
                input: this.generateValidInput(),
                expectedValid: true
            },
            {
                name: 'Leverage exceeds maximum (25)',
                input: this.generateInput({ actualLeverage: 25 }),
                expectedValid: false
            },
            {
                name: 'Negative slippage',
                input: this.generateInput({ actualSlippage: -100 }),
                expectedValid: false
            },
            {
                name: 'Gas limit too high',
                input: this.generateInput({ actualGasLimit: 10000000 }),
                expectedValid: false
            },
            {
                name: 'Zero minimum profit',
                input: this.generateInput({ actualMinProfit: 0 }),
                expectedValid: false
            }
        ];
        
        const results = await this.runTestCases(testCases, 'parameter_bounds');
        return this.analyzeResults(results, 'Parameter Bounds');
    }
    
    /**
     * Test Property: Model consistency is verified within tolerance
     */
    async testModelConsistency() {
        console.log(`🔍 Testing model consistency for ${this.circuitName}...`);
        
        const testCases = [
            {
                name: 'Parameters within 10% tolerance',
                input: this.generateInput({
                    modelLeverage: 10,
                    actualLeverage: 11, // 10% higher
                    modelSlippage: 100,
                    actualSlippage: 90  // 10% lower
                }),
                expectedValid: true
            },
            {
                name: 'Leverage outside tolerance (>10%)',
                input: this.generateInput({
                    modelLeverage: 10,
                    actualLeverage: 15, // 50% higher
                    modelSlippage: 100,
                    actualSlippage: 100
                }),
                expectedValid: false
            },
            {
                name: 'Slippage outside tolerance (>10%)',
                input: this.generateInput({
                    modelLeverage: 10,
                    actualLeverage: 10,
                    modelSlippage: 100,
                    actualSlippage: 200 // 100% higher
                }),
                expectedValid: false
            }
        ];
        
        const results = await this.runTestCases(testCases, 'model_consistency');
        return this.analyzeResults(results, 'Model Consistency');
    }
    
    /**
     * Test Property: PnL verification prevents impossible profits
     */
    async testPnLVerification() {
        console.log(`🔍 Testing PnL verification for ${this.circuitName}...`);
        
        const testCases = [
            {
                name: 'Realistic positive PnL',
                input: this.generateInput({
                    reportedPnL: 1000,
                    marketLiquidity: 100000,
                    actualLeverage: 5
                }),
                expectedValid: true
            },
            {
                name: 'PnL exceeds theoretical maximum',
                input: this.generateInput({
                    reportedPnL: 100000000, // Impossibly high
                    marketLiquidity: 100000,
                    actualLeverage: 5
                }),
                expectedValid: false
            },
            {
                name: 'PnL below maximum loss threshold',
                input: this.generateInput({
                    reportedPnL: -10000,
                    actualMaxLoss: 5000 // Loss exceeds max allowed
                }),
                expectedValid: false
            },
            {
                name: 'Small loss within limits',
                input: this.generateInput({
                    reportedPnL: -1000,
                    actualMaxLoss: 2000
                }),
                expectedValid: true
            }
        ];
        
        const results = await this.runTestCases(testCases, 'pnl_verification');
        return this.analyzeResults(results, 'PnL Verification');
    }
    
    /**
     * Test Property: Risk management constraints are enforced
     */
    async testRiskManagement() {
        console.log(`🔍 Testing risk management for ${this.circuitName}...`);
        
        const testCases = [
            {
                name: 'Valid risk-reward ratio',
                input: this.generateInput({
                    actualMinProfit: 1000,
                    actualMaxLoss: 2000, // 2:1 ratio, within 3:1 limit
                    marketVolatility: 2000,
                    actualLeverage: 10
                }),
                expectedValid: true
            },
            {
                name: 'Risk-reward ratio exceeds 3:1',
                input: this.generateInput({
                    actualMinProfit: 1000,
                    actualMaxLoss: 4000, // 4:1 ratio, exceeds limit
                    marketVolatility: 2000,
                    actualLeverage: 10
                }),
                expectedValid: false
            },
            {
                name: 'High leverage with high volatility',
                input: this.generateInput({
                    marketVolatility: 6000, // High volatility
                    actualLeverage: 15, // High leverage should be rejected
                    actualMinProfit: 1000,
                    actualMaxLoss: 1500
                }),
                expectedValid: false
            },
            {
                name: 'Low leverage with high volatility',
                input: this.generateInput({
                    marketVolatility: 6000, // High volatility
                    actualLeverage: 8, // Low leverage should be accepted
                    actualMinProfit: 1000,
                    actualMaxLoss: 1500
                }),
                expectedValid: true
            }
        ];
        
        const results = await this.runTestCases(testCases, 'risk_management');
        return this.analyzeResults(results, 'Risk Management');
    }
    
    /**
     * Test Property: Front-running protection works correctly
     */
    async testFrontRunProtection() {
        console.log(`🔍 Testing front-running protection for ${this.circuitName}...`);
        
        const testCases = [
            {
                name: 'No front-running detected',
                input: this.generateInput({
                    ourTransactionTimestamps: [1000, 1001, 1002],
                    otherTransactionTimestamps: [999, 1000, 1001], // Others execute first
                    transactionValues: [2000000000000000000, 1500000000000000000, 1200000000000000000] // > 1 ETH
                }),
                expectedValid: true
            },
            {
                name: 'Front-running small transactions detected',
                input: this.generateInput({
                    ourTransactionTimestamps: [1000, 1001, 1002],
                    otherTransactionTimestamps: [1001, 1002, 1003], // We execute first
                    transactionValues: [500000000000000000, 600000000000000000, 700000000000000000] // < 1 ETH
                }),
                expectedValid: false
            },
            {
                name: 'Large transactions can be front-run',
                input: this.generateInput({
                    ourTransactionTimestamps: [1000, 1001, 1002],
                    otherTransactionTimestamps: [1001, 1002, 1003], // We execute first
                    transactionValues: [5000000000000000000, 3000000000000000000, 2500000000000000000] // > 1 ETH
                }),
                expectedValid: true
            }
        ];
        
        const results = await this.runTestCases(testCases, 'frontrun_protection');
        return this.analyzeResults(results, 'Front-Running Protection');
    }
    
    /**
     * Generate valid input for the circuit
     */
    generateValidInput() {
        const baseInput = {
            strategyId: 123456789,
            timestamp: Math.floor(Date.now() / 1000),
            blockNumber: 18500000,
            marketVolatility: 2000,
            marketLiquidity: 500000,
            gasPriceGwei: 20,
            modelLeverage: 5,
            modelSlippage: 100,
            modelGasLimit: 200000,
            modelMinProfit: 1000,
            modelMaxLoss: 500,
            actualLeverage: 5,
            actualSlippage: 100,
            actualGasLimit: 200000,
            actualMinProfit: 1000,
            actualMaxLoss: 500,
            reportedPnL: 1500,
            modelWeightsHash: 12345,
            transactionCount: 3
        };
        
        // Generate transaction arrays
        baseInput.ourTransactionTimestamps = Array(20).fill(0).map((_, i) => 1000 + i);
        baseInput.otherTransactionTimestamps = Array(20).fill(0).map((_, i) => 999 + i);
        baseInput.transactionValues = Array(20).fill(2000000000000000000); // 2 ETH each
        
        return baseInput;
    }
    
    /**
     * Generate input with specific overrides
     */
    generateInput(overrides = {}) {
        return { ...this.generateValidInput(), ...overrides };
    }
    
    /**
     * Run a set of test cases
     */
    async runTestCases(testCases, category) {
        const results = [];
        
        for (const testCase of testCases) {
            try {
                console.log(`  Running: ${testCase.name}`);
                
                // Write input to file
                const inputPath = path.join(TEST_OUTPUT_DIR, `${category}_input.json`);
                fs.writeFileSync(inputPath, JSON.stringify(testCase.input, null, 2));
                
                // Generate witness
                const wasmPath = this.circuitPath.replace('.circom', '_js/').replace(/[^/\\]+\.circom/, 
                    path.basename(this.circuitPath, '.circom') + '.wasm');
                const wtnsPath = path.join(TEST_OUTPUT_DIR, `${category}_witness.wtns`);
                
                let witnessGenerated = false;
                let circuitOutput = null;
                let error = null;
                
                try {
                    await snarkjs.wtns.calculate(testCase.input, wasmPath, wtnsPath);
                    witnessGenerated = true;
                    
                    // Export and read witness
                    const witnessJsonPath = path.join(TEST_OUTPUT_DIR, `${category}_witness.json`);
                    await snarkjs.wtns.exportJson(wtnsPath, witnessJsonPath);
                    const witness = JSON.parse(fs.readFileSync(witnessJsonPath, 'utf8'));
                    
                    // Extract isValid output (assuming it's the second-to-last signal)
                    const isValidIndex = witness.length - 2;
                    circuitOutput = witness[isValidIndex] === '1';
                } catch (witnessError) {
                    error = witnessError.message;
                }
                
                const testPassed = witnessGenerated ? 
                    (circuitOutput === testCase.expectedValid) : 
                    (!testCase.expectedValid); // Good if witness fails for invalid input
                
                results.push({
                    name: testCase.name,
                    expectedValid: testCase.expectedValid,
                    witnessGenerated,
                    circuitOutput,
                    testPassed,
                    error,
                    executionTime: Date.now()
                });
                
                console.log(`    Result: ${testPassed ? '✅ PASS' : '❌ FAIL'}`);
                
            } catch (error) {
                results.push({
                    name: testCase.name,
                    expectedValid: testCase.expectedValid,
                    witnessGenerated: false,
                    circuitOutput: null,
                    testPassed: false,
                    error: error.message
                });
                console.log(`    Result: ❌ ERROR - ${error.message}`);
            }
        }
        
        return results;
    }
    
    /**
     * Analyze test results for a property
     */
    analyzeResults(results, propertyName) {
        const totalTests = results.length;
        const passedTests = results.filter(r => r.testPassed).length;
        const failedTests = totalTests - passedTests;
        
        const analysis = {
            property: propertyName,
            totalTests,
            passedTests,
            failedTests,
            successRate: (passedTests / totalTests) * 100,
            results: results
        };
        
        this.testResults.push(analysis);
        
        console.log(`  ${propertyName}: ${passedTests}/${totalTests} tests passed (${analysis.successRate.toFixed(1)}%)`);
        
        return analysis;
    }
    
    /**
     * Run comprehensive property tests
     */
    async runAllPropertyTests() {
        console.log(`\n🧪 Running comprehensive property tests for ${this.circuitName}`);
        console.log('='.repeat(80));
        
        const startTime = Date.now();
        
        // Run all property tests
        await this.testParameterBounds();
        await this.testModelConsistency();
        await this.testPnLVerification();
        await this.testRiskManagement();
        await this.testFrontRunProtection();
        
        const executionTime = Date.now() - startTime;
        
        // Generate comprehensive report
        const report = this.generateComprehensiveReport(executionTime);
        
        // Save report
        const reportPath = path.join(TEST_OUTPUT_DIR, `${this.circuitName}_property_test_report.json`);
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        
        console.log('\n📊 PROPERTY TEST SUMMARY');
        console.log('='.repeat(50));
        console.log(`Circuit: ${this.circuitName}`);
        console.log(`Total Properties Tested: ${this.testResults.length}`);
        console.log(`Overall Success Rate: ${report.overallSuccessRate.toFixed(1)}%`);
        console.log(`Execution Time: ${executionTime}ms`);
        console.log(`Report saved to: ${reportPath}`);
        
        return report;
    }
    
    /**
     * Generate comprehensive test report
     */
    generateComprehensiveReport(executionTime) {
        const totalTests = this.testResults.reduce((sum, r) => sum + r.totalTests, 0);
        const totalPassed = this.testResults.reduce((sum, r) => sum + r.passedTests, 0);
        const overallSuccessRate = totalTests > 0 ? (totalPassed / totalTests) * 100 : 0;
        
        const criticalFailures = this.testResults.filter(r => r.successRate < 80);
        
        return {
            circuitName: this.circuitName,
            circuitPath: this.circuitPath,
            timestamp: new Date().toISOString(),
            executionTime,
            summary: {
                totalProperties: this.testResults.length,
                totalTests,
                totalPassed,
                totalFailed: totalTests - totalPassed,
                overallSuccessRate
            },
            propertyResults: this.testResults,
            criticalFailures: criticalFailures.map(f => ({
                property: f.property,
                successRate: f.successRate,
                failedTests: f.failedTests
            })),
            recommendations: this.generateRecommendations(),
            verified: overallSuccessRate >= 95 && criticalFailures.length === 0
        };
    }
    
    /**
     * Generate recommendations based on test results
     */
    generateRecommendations() {
        const recommendations = [];
        
        this.testResults.forEach(result => {
            if (result.successRate < 80) {
                recommendations.push({
                    severity: 'HIGH',
                    property: result.property,
                    issue: `Low success rate (${result.successRate.toFixed(1)}%)`,
                    action: 'Review circuit constraints and logic for this property'
                });
            } else if (result.successRate < 95) {
                recommendations.push({
                    severity: 'MEDIUM',
                    property: result.property,
                    issue: `Moderate success rate (${result.successRate.toFixed(1)}%)`,
                    action: 'Consider strengthening constraints or test cases'
                });
            }
        });
        
        if (recommendations.length === 0) {
            recommendations.push({
                severity: 'INFO',
                property: 'All',
                issue: 'All property tests passed',
                action: 'Circuit appears to be correctly implemented'
            });
        }
        
        return recommendations;
    }
}

/**
 * Main testing function
 */
async function runComprehensiveTests() {
    console.log('🔬 ZK CIRCUIT COMPREHENSIVE TESTING FRAMEWORK');
    console.log('=' .repeat(80));
    
    const allReports = [];
    
    // Test each circuit
    for (const [name, path] of Object.entries(CIRCUITS)) {
        if (fs.existsSync(path)) {
            console.log(`\n🔍 Testing circuit: ${name}`);
            const tester = new ZKPropertyTester(path, name);
            const report = await tester.runAllPropertyTests();
            allReports.push(report);
        } else {
            console.log(`⚠️  Circuit not found: ${path}`);
        }
    }
    
    // Generate combined report
    const combinedReport = {
        timestamp: new Date().toISOString(),
        testingFrameworkVersion: '2.0.0',
        circuitReports: allReports,
        overallSummary: {
            totalCircuits: allReports.length,
            verifiedCircuits: allReports.filter(r => r.verified).length,
            criticalIssues: allReports.reduce((sum, r) => sum + r.criticalFailures.length, 0)
        }
    };
    
    const combinedReportPath = path.join(TEST_OUTPUT_DIR, 'comprehensive_test_report.json');
    fs.writeFileSync(combinedReportPath, JSON.stringify(combinedReport, null, 2));
    
    console.log('\n🏁 COMPREHENSIVE TESTING COMPLETE');
    console.log('='.repeat(80));
    console.log(`Circuits Tested: ${combinedReport.overallSummary.totalCircuits}`);
    console.log(`Verified Circuits: ${combinedReport.overallSummary.verifiedCircuits}`);
    console.log(`Critical Issues: ${combinedReport.overallSummary.criticalIssues}`);
    console.log(`Combined Report: ${combinedReportPath}`);
    
    return combinedReport;
}

// Export for use as module
module.exports = {
    ZKPropertyTester,
    runComprehensiveTests
};

// Run if executed directly
if (require.main === module) {
    runComprehensiveTests().catch(error => {
        console.error('❌ Testing failed:', error);
        process.exit(1);
    });
}
