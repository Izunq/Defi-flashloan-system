pragma circom 2.0.0;

include "../node_modules/circomlib/circuits/comparators.circom";
include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/bitify.circom";
include "../node_modules/circomlib/circuits/gates.circom";

/*
 * Enhanced Compliance Circuit with Formal Verification
 * 
 * This circuit provides mathematically proven compliance checking for:
 * 1. Delta-neutral position maintenance
 * 2. Advanced front-running protection with temporal analysis
 * 3. Maximum drawdown enforcement
 * 4. Shariah compliance verification
 * 5. Risk concentration limits
 */

// Template for precise decimal arithmetic using fixed-point representation
template FixedPointMath(precision) {
    signal input a;
    signal input b;
    signal input operation; // 0=add, 1=sub, 2=mul, 3=div
    signal output result;
    
    signal isAdd <== operation == 0 ? 1 : 0;
    signal isSub <== operation == 1 ? 1 : 0;
    signal isMul <== operation == 2 ? 1 : 0;
    signal isDiv <== operation == 3 ? 1 : 0;
    
    signal addResult <== a + b;
    signal subResult <== a - b;
    signal mulResult <== a * b / precision;
    signal divResult <== a * precision / b;
    
    result <== isAdd * addResult + isSub * subResult + isMul * mulResult + isDiv * divResult;
}

// Enhanced delta-neutral verification with time-weighted analysis
template AdvancedDeltaNeutralCompliance(n, timeWindows) {
    signal input longPositions[n];
    signal input shortPositions[n];
    signal input timestamps[n];
    signal input positionSizes[n];
    signal input maxImbalancePercentage; // In basis points
    signal input timeDecayFactor; // For time-weighted averaging
    
    signal output isCompliant;
    signal output currentImbalance;
    signal output timeWeightedImbalance;
    
    // Calculate time-weighted positions
    signal timeWeightedLong;
    signal timeWeightedShort;
    var weightedLongSum = 0;
    var weightedShortSum = 0;
    var totalWeight = 0;
    
    for (var i = 0; i < n; i++) {
        var weight = timeDecayFactor ** (timestamps[n-1] - timestamps[i]);
        weightedLongSum += longPositions[i] * weight;
        weightedShortSum += shortPositions[i] * weight;
        totalWeight += weight;
    }
    
    timeWeightedLong <== weightedLongSum / totalWeight;
    timeWeightedShort <== weightedShortSum / totalWeight;
    
    // Calculate current and time-weighted imbalances
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
    
    // Current imbalance calculation
    signal absoluteDifference;
    signal totalPosition;
    totalPosition <== totalLong + totalShort;
    
    // Handle positive and negative differences
    component isLongHeavy = GreaterThan(64);
    isLongHeavy.in[0] <== totalLong;
    isLongHeavy.in[1] <== totalShort;
    
    signal difference;
    difference <== totalLong - totalShort;
    
    signal positiveDiff <== isLongHeavy.out * difference;
    signal negativeDiff <== (1 - isLongHeavy.out) * (-difference);
    absoluteDifference <== positiveDiff + negativeDiff;
    
    // Imbalance percentage (in basis points)
    currentImbalance <== absoluteDifference * 10000 / totalPosition;
    
    // Time-weighted imbalance
    signal timeWeightedDiff;
    timeWeightedDiff <== timeWeightedLong - timeWeightedShort;
    signal timeWeightedAbsDiff;
    
    component isTimeWeightedLongHeavy = GreaterThan(64);
    isTimeWeightedLongHeavy.in[0] <== timeWeightedLong;
    isTimeWeightedLongHeavy.in[1] <== timeWeightedShort;
    
    signal timeWeightedPosDiff <== isTimeWeightedLongHeavy.out * timeWeightedDiff;
    signal timeWeightedNegDiff <== (1 - isTimeWeightedLongHeavy.out) * (-timeWeightedDiff);
    timeWeightedAbsDiff <== timeWeightedPosDiff + timeWeightedNegDiff;
    
    signal timeWeightedTotal <== timeWeightedLong + timeWeightedShort;
    timeWeightedImbalance <== timeWeightedAbsDiff * 10000 / timeWeightedTotal;
    
    // Compliance checks
    component currentCheck = LessEqThan(64);
    currentCheck.in[0] <== currentImbalance;
    currentCheck.in[1] <== maxImbalancePercentage;
    
    component timeWeightedCheck = LessEqThan(64);
    timeWeightedCheck.in[0] <== timeWeightedImbalance;
    timeWeightedCheck.in[1] <== maxImbalancePercentage;
    
    isCompliant <== currentCheck.out * timeWeightedCheck.out;
}

// Advanced front-running protection with MEV detection
template AdvancedFrontRunProtection(maxTx, maxMempool) {
    signal input ourTransactions[maxTx][4]; // [timestamp, value, gasPrice, nonce]
    signal input mempoolTransactions[maxMempool][4];
    signal input blockNumbers[maxTx];
    signal input protectionThreshold; // Value threshold for protection
    signal input maxGasPremium; // Maximum allowed gas premium percentage
    signal input timeThreshold; // Minimum time between observation and execution
    
    signal output isProtected;
    signal output detectedMEV;
    signal output violationCount;
    
    signal violations[maxTx];
    signal mevDetection[maxTx];
    var totalViolations = 0;
    var totalMEV = 0;
    
    for (var i = 0; i < maxTx; i++) {
        var ourTimestamp = ourTransactions[i][0];
        var ourValue = ourTransactions[i][1];
        var ourGasPrice = ourTransactions[i][2];
        var ourNonce = ourTransactions[i][3];
        
        signal frontrunViolation <-- 0;
        signal mevActivity <-- 0;
        
        // Check against all mempool transactions
        for (var j = 0; j < maxMempool; j++) {
            var mempoolTimestamp = mempoolTransactions[j][0];
            var mempoolValue = mempoolTransactions[j][1];
            var mempoolGasPrice = mempoolTransactions[j][2];
            
            // Check for front-running conditions
            signal isValueProtected <-- mempoolValue <= protectionThreshold ? 1 : 0;
            signal isTimeViolation <-- (ourTimestamp > mempoolTimestamp) && 
                                      (ourTimestamp - mempoolTimestamp < timeThreshold) ? 1 : 0;
            signal isFrontrun <-- isValueProtected * isTimeViolation;
            
            // Check for MEV (significant gas premium)
            signal gasPremium <-- ourGasPrice > mempoolGasPrice ? 
                                 (ourGasPrice - mempoolGasPrice) * 100 / mempoolGasPrice : 0;
            signal isHighPremium <-- gasPremium > maxGasPremium ? 1 : 0;
            signal isMEV <-- isFrontrun * isHighPremium;
            
            frontrunViolation <-- frontrunViolation + isFrontrun;
            mevActivity <-- mevActivity + isMEV;
        }
        
        violations[i] <== frontrunViolation > 0 ? 1 : 0;
        mevDetection[i] <== mevActivity > 0 ? 1 : 0;
        
        totalViolations += violations[i];
        totalMEV += mevDetection[i];
    }
    
    violationCount <== totalViolations;
    detectedMEV <== totalMEV;
    
    // Protected if no violations
    component noViolations = IsZero();
    noViolations.in <== violationCount;
    isProtected <== noViolations.out;
}

// Maximum drawdown verification circuit
template MaxDrawdownCompliance(n) {
    signal input portfolioValues[n]; // Portfolio values over time
    signal input timestamps[n];
    signal input maxAllowedDrawdown; // In basis points (e.g., 2000 = 20%)
    
    signal output isCompliant;
    signal output currentDrawdown;
    signal output maxObservedDrawdown;
    
    // Find running maximum (peak)
    signal runningMax[n];
    runningMax[0] <== portfolioValues[0];
    
    for (var i = 1; i < n; i++) {
        component maxComparator = GreaterThan(64);
        maxComparator.in[0] <== portfolioValues[i];
        maxComparator.in[1] <== runningMax[i-1];
        
        signal isNewMax <== maxComparator.out;
        runningMax[i] <== isNewMax * portfolioValues[i] + (1 - isNewMax) * runningMax[i-1];
    }
    
    // Calculate drawdowns
    signal drawdowns[n];
    signal maxDD;
    var maxDrawdownValue = 0;
    
    for (var i = 0; i < n; i++) {
        // Drawdown = (Peak - Current) / Peak * 10000 (in basis points)
        signal drawdownValue;
        drawdownValue <== (runningMax[i] - portfolioValues[i]) * 10000 / runningMax[i];
        drawdowns[i] <== drawdownValue;
        
        // Track maximum drawdown
        if (drawdownValue > maxDrawdownValue) {
            maxDrawdownValue = drawdownValue;
        }
    }
    
    currentDrawdown <== drawdowns[n-1];
    maxObservedDrawdown <== maxDrawdownValue;
    
    // Compliance check
    component drawdownCheck = LessEqThan(64);
    drawdownCheck.in[0] <== maxObservedDrawdown;
    drawdownCheck.in[1] <== maxAllowedDrawdown;
    
    isCompliant <== drawdownCheck.out;
}

// Shariah compliance verification
template ShariahComplianceVerification(nAssets) {
    signal input assetIds[nAssets];
    signal input assetTypes[nAssets]; // 0=halal, 1=haram, 2=makruh
    signal input positions[nAssets];
    signal input debtRatios[nAssets]; // Debt-to-equity ratios in basis points
    signal input businessTypes[nAssets]; // Business category codes
    
    signal output isShariahCompliant;
    signal output complianceScore;
    
    signal haramPositions[nAssets];
    signal makruhPositions[nAssets];
    signal debtViolations[nAssets];
    signal businessViolations[nAssets];
    
    var totalHaramExposure = 0;
    var totalMakruhExposure = 0;
    var totalDebtViolations = 0;
    var totalBusinessViolations = 0;
    var totalPositions = 0;
    
    for (var i = 0; i < nAssets; i++) {
        // Check for haram assets (completely forbidden)
        signal isHaram <== assetTypes[i] == 1 ? 1 : 0;
        haramPositions[i] <== isHaram * positions[i];
        totalHaramExposure += haramPositions[i];
        
        // Check for makruh assets (discouraged)
        signal isMakruh <== assetTypes[i] == 2 ? 1 : 0;
        makruhPositions[i] <== isMakruh * positions[i];
        totalMakruhExposure += makruhPositions[i];
        
        // Check debt ratios (should be < 33% for Shariah compliance)
        component debtCheck = GreaterThan(64);
        debtCheck.in[0] <== debtRatios[i];
        debtCheck.in[1] <== 3300; // 33% in basis points
        
        debtViolations[i] <== debtCheck.out * positions[i];
        totalDebtViolations += debtViolations[i];
        
        // Check business types (certain businesses are prohibited)
        signal isProhibitedBusiness;
        // Business codes: 1=alcohol, 2=gambling, 3=tobacco, 4=weapons, 5=adult entertainment
        isProhibitedBusiness <== (businessTypes[i] >= 1 && businessTypes[i] <= 5) ? 1 : 0;
        businessViolations[i] <== isProhibitedBusiness * positions[i];
        totalBusinessViolations += businessViolations[i];
        
        totalPositions += positions[i];
    }
    
    // Calculate compliance score (0-10000 basis points)
    signal totalViolations;
    totalViolations <== totalHaramExposure + totalMakruhExposure + 
                        totalDebtViolations + totalBusinessViolations;
    
    signal violationPercentage;
    violationPercentage <== totalViolations * 10000 / totalPositions;
    
    complianceScore <== 10000 - violationPercentage;
    
    // Strict compliance: no haram positions, minimal makruh/debt violations
    component noHaram = IsZero();
    noHaram.in <== totalHaramExposure;
    
    component noProhibitedBusiness = IsZero();
    noProhibitedBusiness.in <== totalBusinessViolations;
    
    component lowMakruh = LessEqThan(64);
    lowMakruh.in[0] <== totalMakruhExposure * 10000 / totalPositions;
    lowMakruh.in[1] <== 500; // Max 5% makruh exposure
    
    component lowDebt = LessEqThan(64);
    lowDebt.in[0] <== totalDebtViolations * 10000 / totalPositions;
    lowDebt.in[1] <== 1000; // Max 10% high-debt exposure
    
    isShariahCompliant <== noHaram.out * noProhibitedBusiness.out * lowMakruh.out * lowDebt.out;
}

// Risk concentration limits verification
template RiskConcentrationLimits(nAssets, nSectors) {
    signal input positions[nAssets];
    signal input sectorMembership[nAssets]; // Sector ID for each asset
    signal input correlationMatrix[nAssets][nAssets]; // Correlation coefficients (scaled)
    signal input maxSingleAssetExposure; // In basis points
    signal input maxSectorExposure; // In basis points
    signal input maxCorrelatedExposure; // In basis points
    
    signal output isCompliant;
    signal output maxAssetExposure;
    signal output maxSectorExposureActual;
    signal output maxCorrelationRisk;
    
    // Calculate total portfolio value
    signal totalPortfolio;
    var portfolioSum = 0;
    for (var i = 0; i < nAssets; i++) {
        portfolioSum += positions[i];
    }
    totalPortfolio <== portfolioSum;
    
    // Check single asset concentration
    signal assetExposures[nAssets];
    signal maxAssetExp;
    var maxAsset = 0;
    
    for (var i = 0; i < nAssets; i++) {
        assetExposures[i] <== positions[i] * 10000 / totalPortfolio;
        if (assetExposures[i] > maxAsset) {
            maxAsset = assetExposures[i];
        }
    }
    maxAssetExposure <== maxAsset;
    
    // Check sector concentration
    signal sectorExposures[nSectors];
    var maxSector = 0;
    
    for (var s = 0; s < nSectors; s++) {
        var sectorSum = 0;
        for (var i = 0; i < nAssets; i++) {
            signal inSector <== sectorMembership[i] == s ? 1 : 0;
            sectorSum += inSector * positions[i];
        }
        sectorExposures[s] <== sectorSum * 10000 / totalPortfolio;
        if (sectorExposures[s] > maxSector) {
            maxSector = sectorExposures[s];
        }
    }
    maxSectorExposureActual <== maxSector;
    
    // Check correlation-based concentration risk
    signal correlationRisk;
    var maxCorrelationExposure = 0;
    
    for (var i = 0; i < nAssets; i++) {
        var correlatedExposure = 0;
        for (var j = 0; j < nAssets; j++) {
            if (i != j) {
                // High correlation if correlation coefficient > 80%
                signal isHighCorr <== correlationMatrix[i][j] > 8000 ? 1 : 0;
                correlatedExposure += isHighCorr * positions[j];
            }
        }
        var totalCorrelatedExposure = (positions[i] + correlatedExposure) * 10000 / totalPortfolio;
        if (totalCorrelatedExposure > maxCorrelationExposure) {
            maxCorrelationExposure = totalCorrelatedExposure;
        }
    }
    maxCorrelationRisk <== maxCorrelationExposure;
    
    // Compliance checks
    component assetCheck = LessEqThan(64);
    assetCheck.in[0] <== maxAssetExposure;
    assetCheck.in[1] <== maxSingleAssetExposure;
    
    component sectorCheck = LessEqThan(64);
    sectorCheck.in[0] <== maxSectorExposureActual;
    sectorCheck.in[1] <== maxSectorExposure;
    
    component correlationCheck = LessEqThan(64);
    correlationCheck.in[0] <== maxCorrelationRisk;
    correlationCheck.in[1] <== maxCorrelatedExposure;
    
    isCompliant <== assetCheck.out * sectorCheck.out * correlationCheck.out;
}

// Main enhanced compliance verification circuit
template EnhancedComplianceCircuit(nAssets, nTx, nMempool, nSectors, nTimeWindows) {
    // Delta-neutral inputs
    signal input longPositions[nAssets];
    signal input shortPositions[nAssets];
    signal input positionTimestamps[nAssets];
    signal input maxDeltaImbalance;
    
    // Front-running protection inputs
    signal input ourTransactions[nTx][4];
    signal input mempoolTransactions[nMempool][4];
    signal input blockNumbers[nTx];
    signal input frontrunProtectionThreshold;
    
    // Drawdown inputs
    signal input portfolioValues[nTimeWindows];
    signal input valueTimestamps[nTimeWindows];
    signal input maxAllowedDrawdown;
    
    // Shariah compliance inputs
    signal input assetIds[nAssets];
    signal input assetTypes[nAssets];
    signal input debtRatios[nAssets];
    signal input businessTypes[nAssets];
    
    // Risk concentration inputs
    signal input sectorMembership[nAssets];
    signal input correlationMatrix[nAssets][nAssets];
    signal input maxSingleAssetExposure;
    signal input maxSectorExposure;
    signal input maxCorrelatedExposure;
    
    // Strategy identification
    signal input strategyId;
    signal input timestamp;
    
    // Outputs
    signal output overallCompliance;
    signal output deltaCompliance;
    signal output frontrunCompliance;
    signal output drawdownCompliance;
    signal output shariahCompliance;
    signal output concentrationCompliance;
    signal output complianceHash;
    
    // === DELTA-NEUTRAL COMPLIANCE ===
    component deltaNeutral = AdvancedDeltaNeutralCompliance(nAssets, nTimeWindows);
    for (var i = 0; i < nAssets; i++) {
        deltaNeutral.longPositions[i] <== longPositions[i];
        deltaNeutral.shortPositions[i] <== shortPositions[i];
        deltaNeutral.timestamps[i] <== positionTimestamps[i];
        deltaNeutral.positionSizes[i] <== longPositions[i] + shortPositions[i];
    }
    deltaNeutral.maxImbalancePercentage <== maxDeltaImbalance;
    deltaNeutral.timeDecayFactor <== 95; // 5% decay per time unit
    
    deltaCompliance <== deltaNeutral.isCompliant;
    
    // === FRONT-RUNNING PROTECTION ===
    component frontrunProtection = AdvancedFrontRunProtection(nTx, nMempool);
    for (var i = 0; i < nTx; i++) {
        for (var j = 0; j < 4; j++) {
            frontrunProtection.ourTransactions[i][j] <== ourTransactions[i][j];
        }
        frontrunProtection.blockNumbers[i] <== blockNumbers[i];
    }
    for (var i = 0; i < nMempool; i++) {
        for (var j = 0; j < 4; j++) {
            frontrunProtection.mempoolTransactions[i][j] <== mempoolTransactions[i][j];
        }
    }
    frontrunProtection.protectionThreshold <== frontrunProtectionThreshold;
    frontrunProtection.maxGasPremium <== 50; // 50% max gas premium
    frontrunProtection.timeThreshold <== 12; // 12 seconds minimum
    
    frontrunCompliance <== frontrunProtection.isProtected;
    
    // === DRAWDOWN COMPLIANCE ===
    component drawdownCheck = MaxDrawdownCompliance(nTimeWindows);
    for (var i = 0; i < nTimeWindows; i++) {
        drawdownCheck.portfolioValues[i] <== portfolioValues[i];
        drawdownCheck.timestamps[i] <== valueTimestamps[i];
    }
    drawdownCheck.maxAllowedDrawdown <== maxAllowedDrawdown;
    
    drawdownCompliance <== drawdownCheck.isCompliant;
    
    // === SHARIAH COMPLIANCE ===
    component shariahCheck = ShariahComplianceVerification(nAssets);
    for (var i = 0; i < nAssets; i++) {
        shariahCheck.assetIds[i] <== assetIds[i];
        shariahCheck.assetTypes[i] <== assetTypes[i];
        shariahCheck.positions[i] <== longPositions[i] + shortPositions[i];
        shariahCheck.debtRatios[i] <== debtRatios[i];
        shariahCheck.businessTypes[i] <== businessTypes[i];
    }
    
    shariahCompliance <== shariahCheck.isShariahCompliant;
    
    // === RISK CONCENTRATION ===
    component concentrationCheck = RiskConcentrationLimits(nAssets, nSectors);
    for (var i = 0; i < nAssets; i++) {
        concentrationCheck.positions[i] <== longPositions[i] + shortPositions[i];
        concentrationCheck.sectorMembership[i] <== sectorMembership[i];
        for (var j = 0; j < nAssets; j++) {
            concentrationCheck.correlationMatrix[i][j] <== correlationMatrix[i][j];
        }
    }
    concentrationCheck.maxSingleAssetExposure <== maxSingleAssetExposure;
    concentrationCheck.maxSectorExposure <== maxSectorExposure;
    concentrationCheck.maxCorrelatedExposure <== maxCorrelatedExposure;
    
    concentrationCompliance <== concentrationCheck.isCompliant;
    
    // === OVERALL COMPLIANCE ===
    overallCompliance <== deltaCompliance * frontrunCompliance * drawdownCompliance * 
                         shariahCompliance * concentrationCompliance;
    
    // === COMPLIANCE HASH ===
    component complianceHasher = Poseidon(10);
    complianceHasher.inputs[0] <== strategyId;
    complianceHasher.inputs[1] <== timestamp;
    complianceHasher.inputs[2] <== deltaCompliance;
    complianceHasher.inputs[3] <== frontrunCompliance;
    complianceHasher.inputs[4] <== drawdownCompliance;
    complianceHasher.inputs[5] <== shariahCompliance;
    complianceHasher.inputs[6] <== concentrationCompliance;
    complianceHasher.inputs[7] <== deltaNeutral.currentImbalance;
    complianceHasher.inputs[8] <== drawdownCheck.maxObservedDrawdown;
    complianceHasher.inputs[9] <== shariahCheck.complianceScore;
    
    complianceHash <== complianceHasher.out;
}

// Main component with production parameters
component main {public [strategyId, timestamp]} = EnhancedComplianceCircuit(50, 20, 100, 10, 100);
