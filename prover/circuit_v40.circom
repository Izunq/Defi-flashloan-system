pragma circom 2.0.0;

include "node_modules/circomlib/circuits/comparators.circom";
include "node_modules/circomlib/circuits/poseidon.circom";
include "node_modules/circomlib/circuits/bitify.circom";
include "node_modules/circomlib/circuits/mux1.circom";

// This circuit verifies that a strategy's parameters are the result of a specific RL model
// given a set of market conditions as input.

// Helper template to verify a single parameter is within the expected range
template ParameterInRange(nBits) {
    signal input parameter;
    signal input minValue;
    signal input maxValue;
    signal output isInRange;
    
    // Check parameter >= minValue
    component greaterThanMin = GreaterEqThan(nBits);
    greaterThanMin.in[0] <== parameter;
    greaterThanMin.in[1] <== minValue;
    
    // Check parameter <= maxValue
    component lessThanMax = LessEqThan(nBits);
    lessThanMax.in[0] <== parameter;
    lessThanMax.in[1] <== maxValue;
    
    // Parameter is in range if both conditions are true
    isInRange <== greaterThanMin.out * lessThanMax.out;
}

// Main circuit for ZK-RL verification
template ZKRLVerifier(nBits, nParams, nModelWeights) {
    // Public inputs
    signal input strategyId;
    signal input timestamp;
    
    // Private inputs
    signal input marketConditions[5]; // Array of market conditions
    signal input modelWeights[nModelWeights]; // RL model weights
    signal input modelOutput[nParams]; // Output from the RL model
    signal input actualParameters[nParams]; // Actual parameters used in the strategy
    
    // Output
    signal output validationHash;
    
    // 1. Verify that each parameter is within acceptable range of the model output
    component paramChecks[nParams];
    signal parametersValid;
    parametersValid <== 1;
    
    for (var i = 0; i < nParams; i++) {
        // Allow for small variations (±10%) between model output and actual parameters
        // This accounts for discretization and rounding in the actual implementation
        var tolerance = modelOutput[i] / 10;
        var minAllowed = modelOutput[i] - tolerance;
        var maxAllowed = modelOutput[i] + tolerance;
        
        paramChecks[i] = ParameterInRange(nBits);
        paramChecks[i].parameter <== actualParameters[i];
        paramChecks[i].minValue <== minAllowed;
        paramChecks[i].maxValue <== maxAllowed;
        
        // All parameters must be valid
        parametersValid *= paramChecks[i].isInRange;
    }
    
    // 2. Compute a hash of the model weights to verify the correct model was used
    component modelHasher = Poseidon(nModelWeights);
    for (var i = 0; i < nModelWeights; i++) {
        modelHasher.inputs[i] <== modelWeights[i];
    }
    signal modelHash;
    modelHash <== modelHasher.out;
    
    // 3. Compute a hash of the market conditions to verify the correct inputs were used
    component conditionsHasher = Poseidon(5);
    for (var i = 0; i < 5; i++) {
        conditionsHasher.inputs[i] <== marketConditions[i];
    }
    signal conditionsHash;
    conditionsHash <== conditionsHasher.out;
    
    // 4. Compute the final validation hash that combines all elements
    component finalHasher = Poseidon(5);
    finalHasher.inputs[0] <== strategyId;
    finalHasher.inputs[1] <== timestamp;
    finalHasher.inputs[2] <== modelHash;
    finalHasher.inputs[3] <== conditionsHash;
    finalHasher.inputs[4] <== parametersValid;
    
    validationHash <== finalHasher.out;
}

// Main component with practical sizes
component main {public [strategyId, timestamp]} = ZKRLVerifier(64, 5, 100);