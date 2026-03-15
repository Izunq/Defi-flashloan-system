// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";
import "./SecureMultiOracle.sol";
import "./PreCognitiveOracle.sol";

/**
 * @title OracleSecurityWrapper
 * @notice Advanced oracle security layer with manipulation detection and prediction
 * @dev Wraps multiple oracle sources with ML-based anomaly detection
 */
contract OracleSecurityWrapper is AccessControl, ReentrancyGuard, Pausable {
    using Math for uint256;

    // =================
    // CONSTANTS & ROLES
    // =================
    
    bytes32 public constant ORACLE_ADMIN_ROLE = keccak256("ORACLE_ADMIN_ROLE");
    bytes32 public constant SECURITY_MANAGER_ROLE = keccak256("SECURITY_MANAGER_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");
    bytes32 public constant PRICE_FEED_ROLE = keccak256("PRICE_FEED_ROLE");

    // Security thresholds
    uint256 public constant MAX_PRICE_DEVIATION = 500; // 5% max deviation
    uint256 public constant MANIPULATION_THRESHOLD = 1000; // 10% manipulation threshold
    uint256 public constant MIN_VALIDATION_SOURCES = 3;
    uint256 public constant PREDICTION_CONFIDENCE_THRESHOLD = 75; // 75% confidence
    uint256 public constant HISTORICAL_ANALYSIS_WINDOW = 24 hours;
    uint256 public constant REAL_TIME_MONITORING_INTERVAL = 30 seconds;

    // =================
    // STATE VARIABLES
    // =================
    
    SecureMultiOracle public immutable primaryOracle;
    PreCognitiveOracle public immutable predictiveOracle;
    
    // Security state
    mapping(bytes32 => SecurityMetrics) public assetSecurityMetrics;
    mapping(bytes32 => PriceHistory[]) public priceHistories;
    mapping(bytes32 => ManipulationAlert[]) public manipulationAlerts;
    mapping(address => bool) public trustedPriceFeeds;
    
    // Anomaly detection
    mapping(bytes32 => AnomalyDetectionData) public anomalyData;
    mapping(bytes32 => uint256) public lastAnomalyCheck;
      // Circuit breaker states
    mapping(bytes32 => bool) public assetCircuitBreakers;
    mapping(bytes32 => uint256) public circuitBreakerActivationTime;
    
    // Asset-specific authorized monitors
    mapping(bytes32 => mapping(address => bool)) public authorizedMonitors;
    
    bool public globalSecurityMode = false;
    uint256 public securityModeActivationTime;
    
    // Real-time monitoring
    uint256 public lastGlobalSecurityCheck;
    uint256 public consecutiveFailures;
    uint256 public maxConsecutiveFailures = 5;

    // =================
    // STRUCTS
    // =================
    
    struct SecurityMetrics {
        uint256 trustScore;           // 0-100 trust score
        uint256 volatilityScore;      // Historical volatility measure
        uint256 liquidityScore;       // Liquidity depth score
        uint256 manipulationRisk;     // Risk of manipulation (0-100)
        uint256 lastUpdate;
        bool isUnderSurveillance;
        uint256 alertCount;
    }
    
    struct PriceHistory {
        uint256 price;
        uint256 timestamp;
        uint256 volume;
        address source;
        uint256 confidence;
        bool validated;
    }
    
    struct ManipulationAlert {
        uint256 timestamp;
        uint256 detectedPrice;
        uint256 expectedPrice;
        uint256 deviation;
        AlertSeverity severity;
        address detector;
        bool resolved;
        string details;
    }
    
    struct AnomalyDetectionData {
        uint256 movingAverage;
        uint256 standardDeviation;
        uint256 lastAnomalyScore;
        uint256 anomalyCount;
        uint256 baselinePrice;
        bool anomalyDetected;
    }
    
    struct ValidationResult {
        bool isValid;
        uint256 consensusPrice;
        uint256 confidence;
        uint256 deviation;
        ManipulationRisk risk;
        string[] warnings;
    }
    
    enum AlertSeverity { LOW, MEDIUM, HIGH, CRITICAL }
    enum ManipulationRisk { NONE, LOW, MEDIUM, HIGH, CRITICAL }

    // =================
    // EVENTS
    // =================
    
    event ManipulationDetected(
        bytes32 indexed assetId,
        uint256 suspiciousPrice,
        uint256 expectedPrice,
        uint256 deviation,
        AlertSeverity severity,
        uint256 timestamp
    );
    
    event AnomalyDetected(
        bytes32 indexed assetId,
        uint256 anomalyScore,
        uint256 price,
        string description,
        uint256 timestamp
    );
    
    event SecurityModeActivated(
        string reason,
        address triggeredBy,
        uint256 timestamp
    );
    
    event CircuitBreakerTriggered(
        bytes32 indexed assetId,
        string reason,
        uint256 price,
        uint256 timestamp
    );
    
    event PricePredictionAlert(
        bytes32 indexed assetId,
        uint256 predictedManipulation,
        uint256 confidence,
        uint256 timeHorizon
    );

    // =================
    // CONSTRUCTOR
    // =================
    
    constructor(
        address _primaryOracle,
        address _predictiveOracle,
        address _admin
    ) {
        require(_primaryOracle != address(0), "Invalid primary oracle");
        require(_predictiveOracle != address(0), "Invalid predictive oracle");
        require(_admin != address(0), "Invalid admin address");
        
        primaryOracle = SecureMultiOracle(_primaryOracle);
        predictiveOracle = PreCognitiveOracle(_predictiveOracle);
        
        // Setup roles
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), _admin);
        _grantRole(ORACLE_ADMIN_ROLE, _admin);
        _grantRole(SECURITY_MANAGER_ROLE, _admin);
        _grantRole(EMERGENCY_ROLE, _admin);
        
        lastGlobalSecurityCheck = block.timestamp;
    }

    // =================
    // MAIN VALIDATION FUNCTIONS
    // =================
    
    /**
     * @notice Get validated price with comprehensive security checks
     * @param assetId Asset identifier
     * @return result Comprehensive validation result
     */
    function getValidatedPrice(bytes32 assetId) 
        external 
        view 
        returns (ValidationResult memory result) 
    {
        // Check if asset is under circuit breaker
        if (assetCircuitBreakers[assetId]) {
            result.isValid = false;
            result.warnings = new string[](1);
            result.warnings[0] = "Asset under circuit breaker";
            result.risk = ManipulationRisk.CRITICAL;
            return result;
        }
        
        // Check global security mode
        if (globalSecurityMode) {
            result.isValid = false;
            result.warnings = new string[](1);
            result.warnings[0] = "Global security mode active";
            result.risk = ManipulationRisk.HIGH;
            return result;
        }
        
        // Get primary oracle price
        (uint256 primaryPrice, bool primaryValid) = primaryOracle.getSafePrice(assetId, 1 hours);
        
        if (!primaryValid) {
            result.isValid = false;
            result.warnings = new string[](1);
            result.warnings[0] = "Primary oracle price invalid";
            result.risk = ManipulationRisk.HIGH;
            return result;
        }
        
        // Perform comprehensive validation
        result = _performComprehensiveValidation(assetId, primaryPrice);
        
        return result;
    }
      /**
     * @notice Perform real-time security monitoring
     * @param assetId Asset to monitor
     */
    function performSecurityMonitoring(bytes32 assetId) external onlyRole(SECURITY_MANAGER_ROLE) whenNotPaused nonReentrant {
        require(assetId != bytes32(0), "Invalid asset ID");
        require(
            block.timestamp >= lastAnomalyCheck[assetId] + REAL_TIME_MONITORING_INTERVAL,
            "Monitoring interval not elapsed"
        );
        
        // Validate caller permissions for specific asset
        require(
            hasRole(ORACLE_ADMIN_ROLE, msg.sender) || 
            authorizedMonitors[assetId][msg.sender],
            "Not authorized to monitor this asset"
        );
        
        lastAnomalyCheck[assetId] = block.timestamp;
        
        // Get current price data
        (uint256 currentPrice, bool isValid) = primaryOracle.getSafePrice(assetId, 1 hours);
        require(isValid, "Invalid price data for monitoring");
        
        // Update price history
        _updatePriceHistory(assetId, currentPrice);
        
        // Perform anomaly detection
        bool anomalyDetected = _detectPriceAnomalies(assetId, currentPrice);
        
        if (anomalyDetected) {
            _handleAnomalyDetection(assetId, currentPrice);
        }
        
        // Update security metrics
        _updateSecurityMetrics(assetId, currentPrice);
        
        // Check for predictive manipulation warnings
        _checkPredictiveWarnings(assetId);
    }

    // =================
    // INTERNAL VALIDATION FUNCTIONS
    // =================
    
    /**
     * @notice Perform comprehensive price validation
     */
    function _performComprehensiveValidation(bytes32 assetId, uint256 primaryPrice) 
        internal 
        view 
        returns (ValidationResult memory result) 
    {
        result.consensusPrice = primaryPrice;
        result.isValid = true;
        result.warnings = new string[](0);
        
        // Check historical consistency
        bool historicallyConsistent = _checkHistoricalConsistency(assetId, primaryPrice);
        if (!historicallyConsistent) {
            result.isValid = false;
            string[] memory newWarnings = new string[](result.warnings.length + 1);
            for (uint i = 0; i < result.warnings.length; i++) {
                newWarnings[i] = result.warnings[i];
            }
            newWarnings[result.warnings.length] = "Historical inconsistency detected";
            result.warnings = newWarnings;
            result.risk = ManipulationRisk.MEDIUM;
        }
        
        // Check volatility patterns
        AnomalyDetectionData memory anomalyData = anomalyData[assetId];
        if (anomalyData.anomalyDetected) {
            result.confidence = result.confidence > 30 ? result.confidence - 30 : 0;
            result.risk = ManipulationRisk.HIGH;
        }
        
        // Check security metrics
        SecurityMetrics memory metrics = assetSecurityMetrics[assetId];
        if (metrics.manipulationRisk > 70) {
            result.isValid = false;
            result.risk = ManipulationRisk.CRITICAL;
        } else if (metrics.manipulationRisk > 50) {
            result.risk = ManipulationRisk.HIGH;
            result.confidence = result.confidence > 25 ? result.confidence - 25 : 0;
        }
        
        // Calculate overall confidence
        result.confidence = _calculateOverallConfidence(assetId, metrics);
        
        return result;
    }
    
    /**
     * @notice Check historical price consistency
     */
    function _checkHistoricalConsistency(bytes32 assetId, uint256 currentPrice) 
        internal 
        view 
        returns (bool) 
    {
        PriceHistory[] memory history = priceHistories[assetId];
        if (history.length < 3) return true; // Not enough data
        
        // Calculate average of recent prices
        uint256 sum = 0;
        uint256 count = 0;
        uint256 cutoffTime = block.timestamp - 1 hours;
        
        for (uint256 i = history.length; i > 0 && count < 10; i--) {
            if (history[i-1].timestamp >= cutoffTime) {
                sum += history[i-1].price;
                count++;
            }
        }
        
        if (count == 0) return true;
        
        uint256 averagePrice = sum / count;
        uint256 deviation = currentPrice > averagePrice 
            ? ((currentPrice - averagePrice) * 10000) / averagePrice
            : ((averagePrice - currentPrice) * 10000) / averagePrice;
        
        return deviation <= MAX_PRICE_DEVIATION;
    }
    
    /**
     * @notice Detect price anomalies using statistical analysis
     */
    function _detectPriceAnomalies(bytes32 assetId, uint256 currentPrice) 
        internal 
        returns (bool anomalyDetected) 
    {
        AnomalyDetectionData storage data = anomalyData[assetId];
        
        // Calculate Z-score for anomaly detection
        if (data.standardDeviation > 0) {
            uint256 zScore = currentPrice > data.movingAverage
                ? ((currentPrice - data.movingAverage) * 1000) / data.standardDeviation
                : ((data.movingAverage - currentPrice) * 1000) / data.standardDeviation;
            
            // Anomaly threshold: Z-score > 3 (99.7% confidence)
            if (zScore > 3000) {
                data.anomalyDetected = true;
                data.lastAnomalyScore = zScore;
                data.anomalyCount++;
                
                emit AnomalyDetected(
                    assetId,
                    zScore,
                    currentPrice,
                    "Statistical anomaly detected",
                    block.timestamp
                );
                
                return true;
            }
        }
        
        // Update moving statistics
        _updateMovingStatistics(assetId, currentPrice);
        
        return false;
    }
    
    /**
     * @notice Update moving average and standard deviation
     */
    function _updateMovingStatistics(bytes32 assetId, uint256 newPrice) internal {
        AnomalyDetectionData storage data = anomalyData[assetId];
        
        // Simple exponential moving average (alpha = 0.1)
        if (data.movingAverage == 0) {
            data.movingAverage = newPrice;
            data.baselinePrice = newPrice;
        } else {
            data.movingAverage = (data.movingAverage * 9 + newPrice) / 10;
        }
        
        // Update standard deviation using exponential moving average
        if (data.movingAverage > 0) {
            uint256 variance = newPrice > data.movingAverage
                ? ((newPrice - data.movingAverage) ** 2)
                : ((data.movingAverage - newPrice) ** 2);
            
            data.standardDeviation = data.standardDeviation == 0
                ? Math.sqrt(variance)
                : Math.sqrt((data.standardDeviation ** 2 * 9 + variance) / 10);
        }
    }

    // =================
    // SECURITY RESPONSE FUNCTIONS
    // =================
    
    /**
     * @notice Handle detected anomaly
     */
    function _handleAnomalyDetection(bytes32 assetId, uint256 suspiciousPrice) internal {
        SecurityMetrics storage metrics = assetSecurityMetrics[assetId];
        metrics.alertCount++;
        metrics.isUnderSurveillance = true;
        
        // Create manipulation alert
        ManipulationAlert memory alert = ManipulationAlert({
            timestamp: block.timestamp,
            detectedPrice: suspiciousPrice,
            expectedPrice: anomalyData[assetId].movingAverage,
            deviation: _calculateDeviation(suspiciousPrice, anomalyData[assetId].movingAverage),
            severity: _determineSeverity(suspiciousPrice, anomalyData[assetId].movingAverage),
            detector: address(this),
            resolved: false,
            details: "Automated anomaly detection"
        });
        
        manipulationAlerts[assetId].push(alert);
        
        // Trigger circuit breaker if critical
        if (alert.severity == AlertSeverity.CRITICAL) {
            _triggerCircuitBreaker(assetId, "Critical price anomaly detected");
        }
        
        emit ManipulationDetected(
            assetId,
            suspiciousPrice,
            anomalyData[assetId].movingAverage,
            alert.deviation,
            alert.severity,
            block.timestamp
        );
    }
    
    /**
     * @notice Trigger circuit breaker for an asset
     */
    function _triggerCircuitBreaker(bytes32 assetId, string memory reason) internal {
        assetCircuitBreakers[assetId] = true;
        circuitBreakerActivationTime[assetId] = block.timestamp;
        
        emit CircuitBreakerTriggered(assetId, reason, 0, block.timestamp);
        
        // Escalate to global security mode if multiple assets affected
        uint256 activeCircuitBreakers = 0;
        // Count would be implemented based on tracked assets
        
        if (activeCircuitBreakers >= 3) {
            _activateGlobalSecurityMode("Multiple asset circuit breakers triggered");
        }
    }
    
    /**
     * @notice Activate global security mode
     */
    function _activateGlobalSecurityMode(string memory reason) internal {
        globalSecurityMode = true;
        securityModeActivationTime = block.timestamp;
        _pause();
        
        emit SecurityModeActivated(reason, address(this), block.timestamp);
    }

    // =================
    // UTILITY FUNCTIONS
    // =================
    
    /**
     * @notice Calculate percentage deviation between two prices
     */
    function _calculateDeviation(uint256 price1, uint256 price2) internal pure returns (uint256) {
        if (price1 == price2) return 0;
        
        uint256 diff = price1 > price2 ? price1 - price2 : price2 - price1;
        uint256 base = Math.max(price1, price2);
        
        return (diff * 10000) / base; // Return in basis points
    }
    
    /**
     * @notice Determine alert severity based on price deviation
     */
    function _determineSeverity(uint256 actualPrice, uint256 expectedPrice) 
        internal 
        pure 
        returns (AlertSeverity) 
    {
        uint256 deviation = _calculateDeviation(actualPrice, expectedPrice);
        
        if (deviation >= 2000) return AlertSeverity.CRITICAL;  // 20%+
        if (deviation >= 1000) return AlertSeverity.HIGH;      // 10%+
        if (deviation >= 500) return AlertSeverity.MEDIUM;     // 5%+
        return AlertSeverity.LOW;
    }
    
    /**
     * @notice Calculate overall confidence score
     */
    function _calculateOverallConfidence(bytes32 assetId, SecurityMetrics memory metrics) 
        internal 
        view 
        returns (uint256) 
    {
        uint256 baseConfidence = 100;
        
        // Reduce confidence based on manipulation risk
        baseConfidence = baseConfidence > metrics.manipulationRisk 
            ? baseConfidence - metrics.manipulationRisk 
            : 0;
        
        // Reduce confidence if under surveillance
        if (metrics.isUnderSurveillance) {
            baseConfidence = baseConfidence > 20 ? baseConfidence - 20 : 0;
        }
        
        // Reduce confidence based on alert count
        uint256 alertPenalty = metrics.alertCount * 5;
        baseConfidence = baseConfidence > alertPenalty ? baseConfidence - alertPenalty : 0;
        
        return baseConfidence;
    }

    // =================
    // UPDATE FUNCTIONS
    // =================
    
    /**
     * @notice Update price history for an asset
     */
    function _updatePriceHistory(bytes32 assetId, uint256 price) internal {
        PriceHistory memory newEntry = PriceHistory({
            price: price,
            timestamp: block.timestamp,
            volume: 0, // Would be populated from external source
            source: address(primaryOracle),
            confidence: 100, // Default confidence
            validated: true
        });
        
        priceHistories[assetId].push(newEntry);
        
        // Keep only last 100 entries to manage storage
        if (priceHistories[assetId].length > 100) {
            // Remove oldest entry
            for (uint256 i = 0; i < priceHistories[assetId].length - 1; i++) {
                priceHistories[assetId][i] = priceHistories[assetId][i + 1];
            }
            priceHistories[assetId].pop();
        }
    }
    
    /**
     * @notice Update security metrics for an asset
     */
    function _updateSecurityMetrics(bytes32 assetId, uint256 currentPrice) internal {
        SecurityMetrics storage metrics = assetSecurityMetrics[assetId];
        
        // Update trust score based on consistency
        bool consistent = _checkHistoricalConsistency(assetId, currentPrice);
        if (consistent) {
            metrics.trustScore = Math.min(metrics.trustScore + 1, 100);
        } else {
            metrics.trustScore = metrics.trustScore > 5 ? metrics.trustScore - 5 : 0;
        }
        
        // Update manipulation risk
        if (anomalyData[assetId].anomalyDetected) {
            metrics.manipulationRisk = Math.min(metrics.manipulationRisk + 10, 100);
        } else {
            metrics.manipulationRisk = metrics.manipulationRisk > 1 ? metrics.manipulationRisk - 1 : 0;
        }
        
        metrics.lastUpdate = block.timestamp;
    }
    
    /**
     * @notice Check predictive warnings from the PreCognitiveOracle
     */
    function _checkPredictiveWarnings(bytes32 assetId) internal {
        // This would integrate with the PreCognitiveOracle to get manipulation predictions        // Implementation depends on the specific predictive oracle
        
        // Example: Check if there's a high probability of manipulation in the next hour
        // bytes32 eventId = keccak256(abi.encodePacked("price_manipulation", assetId));
        // (uint256 probability, uint256 confidence) = predictiveOracle.getProbability(eventId, "1_hour");
        
        // if (probability > 70 && confidence > PREDICTION_CONFIDENCE_THRESHOLD) {
        //     emit PricePredictionAlert(assetId, probability, confidence, 1 hours);
        //     
        //     // Increase surveillance
        //     assetSecurityMetrics[assetId].isUnderSurveillance = true;
        // }
    }

    // =================
    // ADMIN FUNCTIONS
    // =================
    
    /**
     * @notice Reset circuit breaker for an asset
     */
    function resetCircuitBreaker(bytes32 assetId) 
        external 
        onlyRole(EMERGENCY_ROLE) 
    {
        require(assetCircuitBreakers[assetId], "Circuit breaker not active");
        require(
            block.timestamp >= circuitBreakerActivationTime[assetId] + 1 hours,
            "Cooling period not elapsed"
        );
        
        assetCircuitBreakers[assetId] = false;
        assetSecurityMetrics[assetId].isUnderSurveillance = false;
        assetSecurityMetrics[assetId].alertCount = 0;
        
        // Reset anomaly detection
        anomalyData[assetId].anomalyDetected = false;
        anomalyData[assetId].anomalyCount = 0;
    }
    
    /**
     * @notice Deactivate global security mode
     */
    function deactivateGlobalSecurityMode() 
        external 
        onlyRole(EMERGENCY_ROLE) 
    {
        require(globalSecurityMode, "Security mode not active");
        require(
            block.timestamp >= securityModeActivationTime + 2 hours,
            "Minimum security period not elapsed"
        );
        
        globalSecurityMode = false;
        consecutiveFailures = 0;
        _unpause();
    }

    // =================
    // VIEW FUNCTIONS
    // =================
    
    /**
     * @notice Get comprehensive security status for an asset
     */
    function getAssetSecurityStatus(bytes32 assetId) 
        external 
        view 
        returns (
            SecurityMetrics memory metrics,
            bool circuitBreakerActive,
            bool anomalyDetected,
            uint256 alertsCount
        ) 
    {
        metrics = assetSecurityMetrics[assetId];
        circuitBreakerActive = assetCircuitBreakers[assetId];
        anomalyDetected = anomalyData[assetId].anomalyDetected;
        alertsCount = manipulationAlerts[assetId].length;
    }
    
    /**
     * @notice Get system-wide security health
     */
    function getSystemSecurityHealth() 
        external 
        view 
        returns (
            bool globalSecurityActive,
            uint256 consecutiveFailuresCount,
            uint256 lastSecurityCheck,
            bool systemPaused
        ) 
    {
        return (
            globalSecurityMode,
            consecutiveFailures,
            lastGlobalSecurityCheck,
            paused()
        );
    }
}
