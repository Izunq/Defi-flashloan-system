pragma circom 2.0.0;

include "../node_modules/circomlib/circuits/comparators.circom";
include "../node_modules/circomlib/circuits/gates.circom";
include "../node_modules/circomlib/circuits/bitify.circom";

/*
 * No Front-Running Compliance Circuit
 * 
 * This circuit verifies that a strategy does not front-run transactions
 * below a certain value threshold, protecting retail users.
 * 
 * Inputs:
 * - transactionValues[n]: Array of transaction values that were executed (in wei)
 * - transactionTimestamps[n]: Array of timestamps when transactions were executed
 * - pendingTxValues[m]: Array of pending transaction values that were visible before execution
 * - pendingTxTimestamps[m]: Array of timestamps when pending transactions were observed
 * - executionTimestamps[n]: Array of timestamps when the strategy executed its transactions
 * - minProtectionThreshold: Minimum transaction value to protect from front-running
 * 
 * Output:
 * - isCompliant: 1 if the strategy does not front-run protected transactions, 0 otherwise
 */
template NoFrontRunningCompliance(n, m) {
    signal input transactionValues[n];
    signal input transactionTimestamps[n];
    signal input pendingTxValues[m];
    signal input pendingTxTimestamps[m];
    signal input executionTimestamps[n];
    signal input minProtectionThreshold; // Minimum value to protect (e.g., 1 ETH in wei)
    
    signal output isCompliant;
    
    // Check each strategy transaction against pending transactions
    signal isFrontRunning[n];
    
    for (var i = 0; i < n; i++) {
        // Initialize as not front-running
        isFrontRunning[i] <-- 0;
        
        // Check against all pending transactions
        for (var j = 0; j < m; j++) {
            // Check if this is a potential front-running situation:
            // 1. Pending tx was observed before strategy execution
            // 2. Pending tx value is below protection threshold
            // 3. Strategy executed before the pending tx was confirmed
            
            signal isPendingBeforeExecution <-- pendingTxTimestamps[j] < executionTimestamps[i] ? 1 : 0;
            signal isBelowThreshold <-- pendingTxValues[j] <= minProtectionThreshold ? 1 : 0;
            signal isExecutedBeforePendingConfirmed <-- executionTimestamps[i] < transactionTimestamps[j] ? 1 : 0;
            
            // Verify the timestamp comparisons
            signal checkPendingBefore <== isPendingBeforeExecution * (executionTimestamps[i] - pendingTxTimestamps[j]);
            signal checkExecutedBefore <== isExecutedBeforePendingConfirmed * (transactionTimestamps[j] - executionTimestamps[i]);
            
            // If all conditions are true, this is front-running
            signal isFrontRunningThis <== isPendingBeforeExecution * isBelowThreshold * isExecutedBeforePendingConfirmed;
            
            // Update the front-running flag for this strategy transaction
            isFrontRunning[i] <-- isFrontRunning[i] == 1 || isFrontRunningThis == 1 ? 1 : 0;
            
            // Verify the OR operation
            signal checkOr <== isFrontRunning[i] * (1 - isFrontRunningThis) * (1 - isFrontRunning[i] + isFrontRunningThis);
            checkOr === 0;
        }
    }
    
    // Strategy is compliant if none of its transactions are front-running
    signal anyFrontRunning <-- 0;
    
    for (var i = 0; i < n; i++) {
        anyFrontRunning <-- anyFrontRunning == 1 || isFrontRunning[i] == 1 ? 1 : 0;
        
        // Verify the OR operation
        signal checkOr <== anyFrontRunning * (1 - isFrontRunning[i]) * (1 - anyFrontRunning + isFrontRunning[i]);
        checkOr === 0;
    }
    
    isCompliant <== 1 - anyFrontRunning;
}

/*
 * Main component for a strategy with up to 20 transactions and 50 pending transactions
 */
component main {public [minProtectionThreshold]} = NoFrontRunningCompliance(20, 50);