pragma circom 2.0.0;

include "../node_modules/circomlib/circuits/comparators.circom";
include "../node_modules/circomlib/circuits/gates.circom";
include "../node_modules/circomlib/circuits/bitify.circom";

/*
 * Delta Neutral Compliance Circuit
 * 
 * This circuit verifies that a strategy maintains a delta-neutral position,
 * meaning that the net exposure to price movements is minimized.
 * 
 * Inputs:
 * - longPositions[n]: Array of long position values (in wei)
 * - shortPositions[n]: Array of short position values (in wei)
 * - maxImbalancePercentage: Maximum allowed imbalance (e.g., 500 = 5%)
 * 
 * Output:
 * - isCompliant: 1 if the strategy is delta-neutral within the allowed imbalance, 0 otherwise
 */
template DeltaNeutralCompliance(n) {
    signal input longPositions[n];
    signal input shortPositions[n];
    signal input maxImbalancePercentage; // In basis points (e.g., 500 = 5%)
    
    signal output isCompliant;
    
    // Calculate total long and short positions
    signal totalLong;
    signal totalShort;
    
    var sumLong = 0;
    var sumShort = 0;
    
    for (var i = 0; i < n; i++) {
        sumLong += longPositions[i];
        sumShort += shortPositions[i];
    }
    
    totalLong <== sumLong;
    totalShort <== sumShort;
    
    // Calculate absolute difference
    signal difference;
    signal absDifference;
    
    difference <== totalLong - totalShort;
    
    // Calculate absolute value of difference
    signal isNegative <-- difference < 0 ? 1 : 0;
    absDifference <-- isNegative == 1 ? -difference : difference;
    
    // Verify absolute value calculation
    signal checkNegative <== isNegative * (difference + absDifference);
    signal checkPositive <== (1 - isNegative) * (absDifference - difference);
    checkNegative === 0;
    checkPositive === 0;
    
    // Calculate total position size
    signal totalPosition <== totalLong + totalShort;
    
    // Calculate imbalance percentage (in basis points)
    signal imbalancePercentage <-- totalPosition > 0 ? (absDifference * 10000) / totalPosition : 0;
    
    // Verify imbalance percentage calculation
    signal imbalanceCheck <== imbalancePercentage * totalPosition - absDifference * 10000;
    imbalanceCheck === 0;
    
    // Check if imbalance is within allowed range
    signal isWithinRange <-- imbalancePercentage <= maxImbalancePercentage ? 1 : 0;
    
    // Verify the range check
    signal rangeCheck1 <== isWithinRange * (maxImbalancePercentage - imbalancePercentage + 1);
    signal rangeCheck2 <== (1 - isWithinRange) * (imbalancePercentage - maxImbalancePercentage);
    rangeCheck1 !== 0;
    rangeCheck2 !== 0;
    
    // Set output
    isCompliant <== isWithinRange;
}

/*
 * Main component for a strategy with up to 10 assets
 */
component main {public [maxImbalancePercentage]} = DeltaNeutralCompliance(10);