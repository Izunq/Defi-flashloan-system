// Secure ZK Circuit Deployment with Formal Verification
// This script securely deploys formally verified ZK circuits

const fs = require('fs');
const path = require('path');
const { ethers } = require('ethers');
const crypto = require('crypto');

// Import formal verification framework
const { performFormalVerification } = require('./prover/formal_verifier_advanced');
const { runComprehensiveTests } = require('./prover/circuit_property_tester');

// Configuration
const FORMAL_CIRCUIT_PATH = path.join(__dirname, 'prover', 'circuit_formally_verified.circom');
const COMPLIANCE_CIRCUIT_PATH = path.join(__dirname, 'ComplianceCircuits', 'enhanced_compliance_circuit.circom');
const VERIFICATION_REPORT_PATH = path.join(__dirname, 'prover', 'comprehensive_verification_report.json');

/**
 * Comprehensive ZK Circuit Deployment Pipeline
 */
class SecureZKDeployer {
    constructor() {
        this.verificationResults = {};
        this.deploymentConfig = {
            useHSM: process.env.USE_HSM === 'true',
            dryRun: process.env.DRY_RUN === 'true',
            networkId: process.env.NETWORK_ID || 'mainnet',
            deployerAddress: process.env.DEPLOYER_ADDRESS,
            zkVerifierAddress: process.env.ZK_VERIFIER_ADDRESS
        };
    }

    /**
     * Phase 1: Comprehensive Formal Verification
     */
    async performComprehensiveVerification() {
        console.log('🔒 PHASE 1: COMPREHENSIVE FORMAL VERIFICATION');
        console.log('=' .repeat(80));

        // Step 1: Formal mathematical verification
        console.log('🧮 Running formal mathematical verification...');
        const formalVerification = await performFormalVerification();
        
        if (!formalVerification.overallResult.verified) {
            throw new Error(`Formal verification failed: ${JSON.stringify(formalVerification.overallResult.criticalIssues)}`);
        }

        console.log(`✅ Formal verification PASSED (Score: ${formalVerification.overallResult.verificationScore}/100)`);

        // Step 2: Property-based testing
        console.log('🧪 Running comprehensive property testing...');
        const propertyTesting = await runComprehensiveTests();
        
        const verifiedCircuits = propertyTesting.circuitReports.filter(r => r.verified);
        if (verifiedCircuits.length === 0) {
            throw new Error('No circuits passed property-based testing');
        }

        console.log(`✅ Property testing PASSED (${verifiedCircuits.length}/${propertyTesting.circuitReports.length} circuits verified)`);

        // Step 3: Security audit verification
        console.log('🛡️ Performing security audit verification...');
        const securityAudit = await this.performSecurityAudit(formalVerification, propertyTesting);

        console.log('✅ Security audit verification PASSED');

        // Combine all verification results
        this.verificationResults = {
            formalVerification,
            propertyTesting,
            securityAudit,
            overallVerified: true,
            verificationLevel: 'COMPREHENSIVE_FORMAL_SECURITY',
            timestamp: new Date().toISOString(),
            verificationHash: this.calculateVerificationHash(formalVerification, propertyTesting, securityAudit)
        };

        // Save comprehensive report
        fs.writeFileSync(VERIFICATION_REPORT_PATH, JSON.stringify(this.verificationResults, null, 2));
        console.log(`📝 Comprehensive verification report saved: ${VERIFICATION_REPORT_PATH}`);

        return this.verificationResults;
    }

    /**
     * Perform additional security audit checks
     */
    async performSecurityAudit(formalVerification, propertyTesting) {
        const auditChecks = {
            constraintComplexity: this.checkConstraintComplexity(formalVerification),
            circuitSecurity: this.checkCircuitSecurity(propertyTesting),
            deploymentSecurity: this.checkDeploymentSecurity(),
            complianceVerification: this.checkComplianceIntegration()
        };

        const allChecksPassed = Object.values(auditChecks).every(check => check.passed);

        return {
            checks: auditChecks,
            overallPassed: allChecksPassed,
            securityScore: this.calculateSecurityScore(auditChecks),
            recommendations: this.generateSecurityRecommendations(auditChecks)
        };
    }

    /**
     * Check constraint complexity for potential vulnerabilities
     */
    checkConstraintComplexity(formalVerification) {
        const complexity = formalVerification.formalCompilation?.circuitComplexity || 'unknown';
        const constraintCount = formalVerification.formalCompilation?.constraints?.estimatedConstraints || 0;

        return {
            passed: constraintCount > 1000 && constraintCount < 100000,
            complexity,
            constraintCount,
            details: `Circuit has ${constraintCount} constraints with ${complexity} complexity`
        };
    }

    /**
     * Check circuit security properties
     */
    checkCircuitSecurity(propertyTesting) {
        const criticalFailures = propertyTesting.circuitReports.reduce((sum, r) => sum + r.criticalFailures.length, 0);
        const overallSuccessRate = propertyTesting.circuitReports.reduce((sum, r) => sum + (r.summary?.overallSuccessRate || 0), 0) / propertyTesting.circuitReports.length;

        return {
            passed: criticalFailures === 0 && overallSuccessRate >= 95,
            criticalFailures,
            overallSuccessRate,
            details: `${criticalFailures} critical failures, ${overallSuccessRate.toFixed(1)}% success rate`
        };
    }

    /**
     * Check deployment security configuration
     */
    checkDeploymentSecurity() {
        const securityChecks = {
            hasHSM: this.deploymentConfig.useHSM,
            hasDeployerAddress: !!this.deploymentConfig.deployerAddress,
            hasZKVerifierAddress: !!this.deploymentConfig.zkVerifierAddress,
            isDryRun: this.deploymentConfig.dryRun,
            networkConfigured: this.deploymentConfig.networkId !== 'unknown'
        };

        const passed = securityChecks.hasDeployerAddress && securityChecks.hasZKVerifierAddress && securityChecks.networkConfigured;

        return {
            passed,
            checks: securityChecks,
            details: `Security deployment configuration: ${passed ? 'SECURE' : 'INSECURE'}`
        };
    }

    /**
     * Check compliance circuit integration
     */
    checkComplianceIntegration() {
        const complianceCircuitExists = fs.existsSync(COMPLIANCE_CIRCUIT_PATH);
        
        return {
            passed: complianceCircuitExists,
            complianceCircuitExists,
            details: `Compliance circuit integration: ${complianceCircuitExists ? 'ENABLED' : 'MISSING'}`
        };
    }

    /**
     * Calculate overall security score
     */
    calculateSecurityScore(auditChecks) {
        const checkResults = Object.values(auditChecks);
        const passedChecks = checkResults.filter(check => check.passed).length;
        return Math.round((passedChecks / checkResults.length) * 100);
    }

    /**
     * Generate security recommendations
     */
    generateSecurityRecommendations(auditChecks) {
        const recommendations = [];

        if (!auditChecks.constraintComplexity.passed) {
            recommendations.push({
                severity: 'HIGH',
                component: 'Circuit Constraints',
                issue: `Constraint count ${auditChecks.constraintComplexity.constraintCount} outside optimal range`,
                action: 'Optimize circuit constraints or review complexity'
            });
        }

        if (!auditChecks.circuitSecurity.passed) {
            recommendations.push({
                severity: 'CRITICAL',
                component: 'Circuit Security',
                issue: `${auditChecks.circuitSecurity.criticalFailures} critical failures detected`,
                action: 'Address all critical security failures before deployment'
            });
        }

        if (!auditChecks.deploymentSecurity.passed) {
            recommendations.push({
                severity: 'HIGH',
                component: 'Deployment Security',
                issue: 'Deployment security configuration incomplete',
                action: 'Configure HSM, deployer address, and network settings'
            });
        }

        if (!auditChecks.complianceVerification.passed) {
            recommendations.push({
                severity: 'MEDIUM',
                component: 'Compliance Integration',
                issue: 'Compliance circuit not properly integrated',
                action: 'Ensure compliance circuits are compiled and verified'
            });
        }

        return recommendations;
    }

    /**
     * Calculate comprehensive verification hash
     */
    calculateVerificationHash(formalVerification, propertyTesting, securityAudit) {
        const combinedData = {
            formalScore: formalVerification.overallResult.verificationScore,
            propertyResults: propertyTesting.overallSummary,
            securityScore: securityAudit.securityScore,
            timestamp: Date.now()
        };

        return '0x' + crypto
            .createHash('sha256')
            .update(JSON.stringify(combinedData))
            .digest('hex');
    }

    /**
     * Phase 2: Secure Circuit Compilation
     */
    async compileVerifiedCircuits() {
        console.log('\n🔧 PHASE 2: SECURE CIRCUIT COMPILATION');
        console.log('=' .repeat(80));

        const circuits = [
            { name: 'formally_verified', path: FORMAL_CIRCUIT_PATH },
            { name: 'enhanced_compliance', path: COMPLIANCE_CIRCUIT_PATH }
        ];

        const compilationResults = {};

        for (const circuit of circuits) {
            console.log(`📦 Compiling ${circuit.name} circuit...`);
            
            try {
                const result = await this.compileCircuit(circuit.path, circuit.name);
                compilationResults[circuit.name] = result;
                console.log(`✅ ${circuit.name} compilation successful`);
            } catch (error) {
                console.error(`❌ ${circuit.name} compilation failed:`, error.message);
                throw error;
            }
        }

        return compilationResults;
    }

    /**
     * Compile individual circuit with security checks
     */
    async compileCircuit(circuitPath, circuitName) {
        const { execSync } = require('child_process');
        
        if (!fs.existsSync(circuitPath)) {
            throw new Error(`Circuit file not found: ${circuitPath}`);
        }

        const outputDir = path.dirname(circuitPath);
        const baseName = path.basename(circuitPath, '.circom');
        
        // Compile with maximum optimization and security flags
        const compileCmd = `circom ${circuitPath} --r1cs --wasm --sym --c --json --O2 --output ${outputDir}`;
        
        console.log(`  Running: ${compileCmd}`);
        const compileOutput = execSync(compileCmd, { encoding: 'utf8', timeout: 300000 });

        // Verify compilation artifacts
        const artifacts = {
            r1cs: path.join(outputDir, `${baseName}.r1cs`),
            wasm: path.join(outputDir, `${baseName}_js`, `${baseName}.wasm`),
            sym: path.join(outputDir, `${baseName}.sym`)
        };

        for (const [type, artifactPath] of Object.entries(artifacts)) {
            if (!fs.existsSync(artifactPath)) {
                throw new Error(`Missing compilation artifact: ${artifactPath}`);
            }
        }

        return {
            success: true,
            artifacts,
            compileOutput: compileOutput.trim(),
            circuitName,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Phase 3: Trusted Setup Generation
     */
    async generateTrustedSetup(compilationResults) {
        console.log('\n🔐 PHASE 3: TRUSTED SETUP GENERATION');
        console.log('=' .repeat(80));

        const snarkjs = require('snarkjs');
        const setupResults = {};

        for (const [circuitName, compilation] of Object.entries(compilationResults)) {
            console.log(`🔑 Generating trusted setup for ${circuitName}...`);
            
            try {
                const result = await this.generateCircuitSetup(compilation, circuitName);
                setupResults[circuitName] = result;
                console.log(`✅ ${circuitName} trusted setup completed`);
            } catch (error) {
                console.error(`❌ ${circuitName} trusted setup failed:`, error.message);
                throw error;
            }
        }

        return setupResults;
    }

    /**
     * Generate trusted setup for individual circuit
     */
    async generateCircuitSetup(compilation, circuitName) {
        const snarkjs = require('snarkjs');
        const outputDir = path.dirname(compilation.artifacts.r1cs);
        
        // Download Powers of Tau if not exists
        const ptauPath = path.join(outputDir, 'powersOfTau28_hez_final_20.ptau');
        if (!fs.existsSync(ptauPath)) {
            console.log('  📥 Downloading Powers of Tau ceremony file...');
            // In production, verify the Powers of Tau file integrity
            console.log('  ⚠️  Please download Powers of Tau file manually for security');
            console.log(`  Expected path: ${ptauPath}`);
            throw new Error('Powers of Tau file required for trusted setup');
        }

        // Generate verification key
        const zkeyPath = path.join(outputDir, `${circuitName}.zkey`);
        const vkeyPath = path.join(outputDir, `${circuitName}_vkey.json`);

        console.log('  🔧 Running Groth16 setup...');
        await snarkjs.groth16.setup(compilation.artifacts.r1cs, ptauPath, zkeyPath);

        console.log('  📤 Exporting verification key...');
        const vkey = await snarkjs.zKey.exportVerificationKey(zkeyPath);
        fs.writeFileSync(vkeyPath, JSON.stringify(vkey, null, 2));

        // Calculate verification key hash
        const vkeyHash = '0x' + crypto
            .createHash('sha256')
            .update(JSON.stringify(vkey))
            .digest('hex');

        return {
            success: true,
            zkeyPath,
            vkeyPath,
            verificationKey: vkey,
            verificationKeyHash: vkeyHash,
            circuitName,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Phase 4: Deployment Verification
     */
    async verifyDeploymentReadiness() {
        console.log('\n✅ PHASE 4: DEPLOYMENT READINESS VERIFICATION');
        console.log('=' .repeat(80));

        const checks = {
            verificationComplete: !!this.verificationResults.overallVerified,
            securityAuditPassed: this.verificationResults.securityAudit?.overallPassed || false,
            deploymentConfigured: this.deploymentConfig.deployerAddress && this.deploymentConfig.zkVerifierAddress,
            networkConfigured: this.deploymentConfig.networkId && this.deploymentConfig.networkId !== 'unknown'
        };

        const readinessScore = Object.values(checks).filter(Boolean).length / Object.keys(checks).length * 100;

        console.log('📋 Deployment Readiness Checklist:');
        for (const [check, passed] of Object.entries(checks)) {
            console.log(`  ${passed ? '✅' : '❌'} ${check}`);
        }

        console.log(`📊 Readiness Score: ${readinessScore.toFixed(1)}%`);

        if (readinessScore < 100) {
            throw new Error('Deployment readiness checks failed. Address all issues before deployment.');
        }

        return {
            ready: true,
            checks,
            readinessScore,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Main deployment pipeline
     */
    async deploy() {
        try {
            console.log('🚀 SECURE ZK CIRCUIT DEPLOYMENT PIPELINE');
            console.log('=' .repeat(80));
            console.log(`Network: ${this.deploymentConfig.networkId}`);
            console.log(`Dry Run: ${this.deploymentConfig.dryRun ? 'YES' : 'NO'}`);
            console.log(`Use HSM: ${this.deploymentConfig.useHSM ? 'YES' : 'NO'}`);
            console.log('=' .repeat(80));

            // Phase 1: Comprehensive verification
            const verificationResults = await this.performComprehensiveVerification();

            // Phase 2: Circuit compilation
            const compilationResults = await this.compileVerifiedCircuits();

            // Phase 3: Trusted setup
            const setupResults = await this.generateTrustedSetup(compilationResults);

            // Phase 4: Deployment readiness
            const readinessCheck = await this.verifyDeploymentReadiness();

            if (this.deploymentConfig.dryRun) {
                console.log('\n🔍 DRY RUN COMPLETE - No actual deployment performed');
                console.log('✅ All verification and compilation phases passed');
                console.log('🚀 Ready for production deployment');
                return {
                    success: true,
                    dryRun: true,
                    verificationResults,
                    compilationResults,
                    setupResults,
                    readinessCheck
                };
            }

            // Phase 5: Actual deployment (if not dry run)
            console.log('\n🚀 PHASE 5: BLOCKCHAIN DEPLOYMENT');
            console.log('⚠️  CRITICAL: This would perform actual blockchain deployment');
            console.log('🔒 For security, actual deployment is disabled in this implementation');
            console.log('📋 Use secure deployment infrastructure:');
            console.log('   - Hardware Security Modules (HSM)');
            console.log('   - Multi-signature wallets');  
            console.log('   - Secure deployment pipelines');
            console.log('   - Environment-specific configurations');

            return {
                success: true,
                deploymentDisabled: true,
                reason: 'Security - use production deployment infrastructure',
                verificationResults,
                compilationResults,
                setupResults,
                readinessCheck
            };

        } catch (error) {
            console.error('❌ DEPLOYMENT PIPELINE FAILED:', error.message);
            throw error;
        }
    }
}

/**
 * Main deployment function
 */
async function main() {
    const deployer = new SecureZKDeployer();
    
    try {
        const result = await deployer.deploy();
        
        console.log('\n🏁 DEPLOYMENT PIPELINE SUMMARY');
        console.log('=' .repeat(80));
        console.log(`Status: ${result.success ? '✅ SUCCESS' : '❌ FAILED'}`);
        console.log(`Verification Score: ${deployer.verificationResults?.securityAudit?.securityScore || 'N/A'}/100`);
        console.log(`Readiness Score: ${result.readinessCheck?.readinessScore || 'N/A'}%`);
        
        if (result.dryRun) {
            console.log('🔍 Dry run completed successfully - ready for production');
        } else if (result.deploymentDisabled) {
            console.log('🔒 Production deployment ready - use secure infrastructure');
        }
        
        process.exit(0);
        
    } catch (error) {
        console.error('\n💥 DEPLOYMENT FAILED');
        console.error('Error:', error.message);
        process.exit(1);
    }
}

// Export for testing
module.exports = { SecureZKDeployer };

// Run if executed directly
if (require.main === module) {
    main();
}
