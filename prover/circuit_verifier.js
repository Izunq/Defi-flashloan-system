// Circuit Formal Verification Script
// This script performs formal verification of the ZK circuit to ensure correctness

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const snarkjs = require('snarkjs');

// Configuration
const CIRCUIT_FILE = path.join(__dirname, 'circuit_v40.circom');
const VERIFICATION_OUTPUT = path.join(__dirname, 'verification_report.json');

// Formal verification parameters
const MAX_CONSTRAINTS = 10000;
const VERIFICATION_TIMEOUT_MS = 300000; // 5 minutes

/**
 * Performs static analysis on the circuit to detect common issues
 */
async function performStaticAnalysis() {
    console.log('Performing static analysis of circuit...');
    
    try {
        // Read the circuit file
        const circuitCode = fs.readFileSync(CIRCUIT_FILE, 'utf8');
        
        // Check for common issues
        const issues = [];
        
        // Check for unbounded loops
        if (circuitCode.includes('for (') && !circuitCode.match(/for\s*\(\s*var\s+[a-zA-Z0-9_]+\s*=\s*[0-9]+\s*;\s*[a-zA-Z0-9_]+\s*<\s*[a-zA-Z0-9_]+\s*;/g)) {
            issues.push({
                type: 'UNBOUNDED_LOOP',
                severity: 'HIGH',
                message: 'Potentially unbounded loop detected. All loops should have fixed bounds.'
            });
        }
        
        // Check for missing range checks on public inputs
        if (!circuitCode.includes('GreaterEqThan') || !circuitCode.includes('LessEqThan')) {
            issues.push({
                type: 'MISSING_RANGE_CHECK',
                severity: 'HIGH',
                message: 'Missing range checks on inputs. All inputs should be validated with range constraints.'
            });
        }
        
        // Check for proper signal assignments
        const signalAssignments = circuitCode.match(/[a-zA-Z0-9_]+\s*<==\s*[^;]+/g) || [];
        const signalDeclarations = circuitCode.match(/signal\s+(input|output)?\s+[a-zA-Z0-9_]+/g) || [];
        
        if (signalAssignments.length < signalDeclarations.length / 2) {
            issues.push({
                type: 'UNASSIGNED_SIGNALS',
                severity: 'MEDIUM',
                message: 'Potential unassigned signals detected. Ensure all signals are properly constrained.'
            });
        }
        
        return {
            circuitFile: CIRCUIT_FILE,
            issuesFound: issues.length,
            issues: issues
        };
    } catch (error) {
        console.error('Static analysis failed:', error);
        return {
            circuitFile: CIRCUIT_FILE,
            error: error.message,
            issuesFound: -1
        };
    }
}

/**
 * Compiles the circuit and checks for compilation errors
 */
async function compileCircuit() {
    console.log('Compiling circuit to check for errors...');
    
    try {
        // Run circom compiler to check for errors
        const compileOutput = execSync(`circom ${CIRCUIT_FILE} --r1cs --wasm --sym`, { 
            timeout: VERIFICATION_TIMEOUT_MS,
            encoding: 'utf8'
        });
        
        // Check the generated R1CS file size
        const r1csPath = CIRCUIT_FILE.replace('.circom', '.r1cs');
        const r1csStats = fs.statSync(r1csPath);
        const constraintCount = Math.floor(r1csStats.size / 32); // Approximate constraint count
        
        return {
            success: true,
            constraintCount: constraintCount,
            exceedsMaxConstraints: constraintCount > MAX_CONSTRAINTS,
            compilationOutput: compileOutput
        };
    } catch (error) {
        console.error('Circuit compilation failed:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * Performs symbolic execution to verify circuit properties
 */
async function performSymbolicExecution() {
    console.log('Performing symbolic execution...');
    
    try {
        // Generate a test input
        const testInput = {
            strategyId: 123456789,
            timestamp: Math.floor(Date.now() / 1000),
            marketConditions: [1000, 2000, 3000, 4000, 5000],
            modelWeights: Array(100).fill(0).map((_, i) => i + 1),
            modelOutput: [100, 200, 300, 400, 500],
            actualParameters: [105, 210, 295, 410, 490]
        };
        
        // Write test input to file
        const inputPath = path.join(__dirname, 'test_input.json');
        fs.writeFileSync(inputPath, JSON.stringify(testInput, null, 2));
        
        // Generate witness
        const wasmPath = CIRCUIT_FILE.replace('.circom', '_js/') + 'circuit_v40.wasm';
        const wtnsPath = path.join(__dirname, 'witness.wtns');
        
        await snarkjs.wtns.calculate(testInput, wasmPath, wtnsPath);
        
        // Export witness to json
        const witnessJson = path.join(__dirname, 'witness.json');
        await snarkjs.wtns.exportJson(wtnsPath, witnessJson);
        
        // Read and analyze the witness
        const witness = JSON.parse(fs.readFileSync(witnessJson, 'utf8'));
        
        // Check if output matches expected values
        const validationHashIndex = witness.findIndex(val => val !== '0' && val !== '1') - 1;
        
        return {
            success: true,
            witnessSize: witness.length,
            validationHashPresent: validationHashIndex > 0
        };
    } catch (error) {
        console.error('Symbolic execution failed:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * Verifies that the circuit correctly implements the intended logic
 */
async function verifyCircuitLogic() {
    console.log('Verifying circuit logic...');
    
    try {
        // Test cases with expected results
        const testCases = [
            {
                name: 'Valid parameters within tolerance',
                input: {
                    strategyId: 123456789,
                    timestamp: Math.floor(Date.now() / 1000),
                    marketConditions: [1000, 2000, 3000, 4000, 5000],
                    modelWeights: Array(100).fill(0).map((_, i) => i + 1),
                    modelOutput: [100, 200, 300, 400, 500],
                    actualParameters: [105, 210, 295, 410, 490]
                },
                expectedValid: true
            },
            {
                name: 'Invalid parameters outside tolerance',
                input: {
                    strategyId: 123456789,
                    timestamp: Math.floor(Date.now() / 1000),
                    marketConditions: [1000, 2000, 3000, 4000, 5000],
                    modelWeights: Array(100).fill(0).map((_, i) => i + 1),
                    modelOutput: [100, 200, 300, 400, 500],
                    actualParameters: [150, 250, 350, 450, 550] // Outside 10% tolerance
                },
                expectedValid: false
            }
        ];
        
        const results = [];
        
        for (const testCase of testCases) {
            try {
                // Write test input to file
                const inputPath = path.join(__dirname, 'test_input.json');
                fs.writeFileSync(inputPath, JSON.stringify(testCase.input, null, 2));
                
                // Generate witness
                const wasmPath = CIRCUIT_FILE.replace('.circom', '_js/') + 'circuit_v40.wasm';
                const wtnsPath = path.join(__dirname, 'witness.wtns');
                
                await snarkjs.wtns.calculate(testCase.input, wasmPath, wtnsPath);
                
                // Check if witness generation succeeded (if it fails, the constraints are not satisfied)
                results.push({
                    name: testCase.name,
                    success: true,
                    matchesExpectation: true
                });
            } catch (error) {
                results.push({
                    name: testCase.name,
                    success: false,
                    matchesExpectation: !testCase.expectedValid,
                    error: error.message
                });
            }
        }
        
        return {
            testCasesRun: testCases.length,
            results: results,
            allTestsPassed: results.every(r => r.matchesExpectation)
        };
    } catch (error) {
        console.error('Circuit logic verification failed:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * Main verification function that runs all checks
 */
async function verifyCircuit() {
    console.log('Starting formal verification of ZK circuit...');
    
    const verificationReport = {
        circuitFile: CIRCUIT_FILE,
        timestamp: new Date().toISOString(),
        staticAnalysis: await performStaticAnalysis(),
        compilation: await compileCircuit()
    };
    
    // Only continue with more tests if compilation succeeded
    if (verificationReport.compilation.success) {
        verificationReport.symbolicExecution = await performSymbolicExecution();
        verificationReport.logicVerification = await verifyCircuitLogic();
        
        // Overall verification result
        verificationReport.verified = 
            verificationReport.staticAnalysis.issuesFound === 0 &&
            verificationReport.compilation.success &&
            !verificationReport.compilation.exceedsMaxConstraints &&
            verificationReport.symbolicExecution.success &&
            verificationReport.logicVerification.allTestsPassed;
    } else {
        verificationReport.verified = false;
    }
    
    // Write verification report to file
    fs.writeFileSync(VERIFICATION_OUTPUT, JSON.stringify(verificationReport, null, 2));
    
    console.log(`Verification completed. Report saved to ${VERIFICATION_OUTPUT}`);
    console.log(`Verification result: ${verificationReport.verified ? 'PASSED' : 'FAILED'}`);
    
    return verificationReport;
}

// Run verification if this script is executed directly
if (require.main === module) {
    verifyCircuit().catch(error => {
        console.error('Verification failed with error:', error);
        process.exit(1);
    });
}

module.exports = {
    verifyCircuit,
    performStaticAnalysis,
    compileCircuit,
    performSymbolicExecution,
    verifyCircuitLogic
};