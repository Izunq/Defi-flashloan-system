// =================================================================================================
// ZK Witness Generator for Arbitrage Proof System
// This script generates a witness for the ZK circuit based on input data
// =================================================================================================

const fs = require('fs');
const snarkjs = require('snarkjs');

// Check if input file path is provided
if (process.argv.length < 4) {
    console.error('Usage: node generate_witness.js input.json witness.wtns');
    process.exit(1);
}

const inputPath = process.argv[2];
const witnessPath = process.argv[3];

async function generateWitness() {
    try {
        // Read input file
        const inputData = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
        
        // Validate input data
        if (!inputData.hasOwnProperty('pnl') || !inputData.hasOwnProperty('model_id')) {
            throw new Error('Input must contain pnl and model_id fields');
        }
        
        // Load the wasm file (compiled circuit)
        const { proof, publicSignals } = await snarkjs.groth16.fullProve(
            inputData,
            __dirname + '/circuit.wasm',
            __dirname + '/circuit_final.zkey'
        );
        
        // Write the witness to the output file
        fs.writeFileSync(witnessPath, JSON.stringify(publicSignals));
        
        console.log('Witness generated successfully');
    } catch (error) {
        console.error('Error generating witness:', error);
        process.exit(1);
    }
}

generateWitness().then(() => {
    process.exit(0);
});