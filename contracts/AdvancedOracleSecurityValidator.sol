// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";
import "./SecureMultiOracle.sol";

/**
 * @title AdvancedOracleSecurityValidator
 * @notice Enhanced oracle security validation with ML-based anomaly detection
 * @dev Provides advanced statistical analysis and predictive security measures
 */
contract AdvancedOracleSecurityValidator is AccessControl, ReentrancyGuard, Pausable {
    using Math for uint256;

    // =================
    // CONSTANTS & ROLES
    // =================
    
    bytes32 public constant VALIDATOR_ADMIN_ROLE = keccak256("VALIDATOR_ADMIN_ROLE");
    bytes32 public constant SECURITY_ANALYST_ROLE = keccak256("SECURITY_ANALYST_ROLE");
    bytes32 public constant EMERGENCY_RESPONSE_ROLE = keccak256("EMERGENCY_RESPONSE_ROLE");
    bytes32 public constant ORACLE_REPORTER_ROLE = keccak256("ORACLE_REPORTER_ROLE");
    
    // Advanced security constants
    uint256 public constant STATISTICAL_SIGNIFICANCE_THRESHOLD = 9973; // 99.73% (3 sigma)
    uint256 public constant MANIPULATION_CONFIDENCE_THRESHOLD = 8000; // 80%
    uint256 public constant PRICE_VELOCITY_THRESHOLD = 1000; // 10% per minute
    uint256 public constant CORRELATION_THRESHOLD = 8500; // 85% correlation
    uint256 public constant VOLUME_ANOMALY_MULTIPLIER = 300; // 3x normal volume
    
    // Time windows for analysis
    uint256 public constant SHORT_TERM_WINDOW = 5 minutes;
    uint256 public constant MEDIUM_TERM_WINDOW = 1 hours;
    uint256 public constant LONG_TERM_WINDOW = 24 hours;
    uint256 public constant VOLATILITY_WINDOW = 7 days;

    // =================
    // STRUCTURES
    // =================
    
    struct PriceDataPoint {
        uint256 price;
        uint256 timestamp;
        uint256 volume;
        uint256 gasUsed;
        address submitter;
        uint256 blockNumber;
    }
    
    struct StatisticalMetrics {
        uint256 mean;
        uint256 standardDeviation;
        uint256 variance;
        uint256 skewness;
        uint256 kurtosis;
        uint256 lastUpdate;
    }
    
    struct AnomalyScore {
        uint256 zScore;
        uint256 isolationScore;
        uint256 mahalanobisDistance;
        uint256 velocityScore;
        uint256 volumeScore;
        uint256 combinedScore;
        bool isAnomalous;
    }
    
    struct ValidationResult {
        bool isValid;
        uint256 confidenceScore;
        uint256 riskLevel;
        AnomalyScore anomalyAnalysis;
        string[] warnings;
        uint256 recommendedAction;
    }
    
    struct SecurityThreat {
        bytes32 threatId;
        uint256 threatType;
        uint256 severity;
        uint256 confidence;
        bytes32 assetId;
        uint256 detectedAt;
        uint256 priceAtDetection;
        string description;
        bool mitigated;
        uint256 mitigationAction;
    }
    
    enum ThreatType {
        PRICE_MANIPULATION,
        FLASH_LOAN_ATTACK,
        ORACLE_CORRUPTION,
        VOLUME_MANIPULATION,
        TIMESTAMP_MANIPULATION,
        COORDINATED_ATTACK,
        STATISTICAL_ANOMALY
    }
    
    enum SecurityAction {
        NONE,
        INCREASE_MONITORING,
        REQUIRE_CONSENSUS,
        ACTIVATE_CIRCUIT_BREAKER,
        PAUSE_OPERATIONS,
        EMERGENCY_SHUTDOWN
    }

    // =================
    // STATE VARIABLES
    // =================
    
    SecureMultiOracle public immutable primaryOracle;
    
    // Price history and statistics
    mapping(bytes32 => PriceDataPoint[]) public priceHistory;
    mapping(bytes32 => StatisticalMetrics) public assetStatistics;
    mapping(bytes32 => uint256) public priceVelocities;
    mapping(bytes32 => uint256) public volumeBaselines;
    
    // Security state
    mapping(bytes32 => SecurityThreat[]) public detectedThreats;
    mapping(bytes32 => uint256) public threatScores;
    mapping(bytes32 => uint256) public lastSecurityCheck;
    mapping(bytes32 => bool) public emergencyMode;
    
    // Advanced monitoring
    mapping(bytes32 => uint256) public correlationMatrix;
    mapping(address => uint256) public oracleReputationScores;
    mapping(bytes32 => uint256) public marketRegimeState;
    
    // Configuration
    uint256 public maxHistoryLength = 1000;
    uint256 public anomalyThreshold = 9500; // 95%
    uint256 public emergencyThreshold = 9800; // 98%
    
    // Events
    event ThreatDetected(
        bytes32 indexed threatId,
        bytes32 indexed assetId,
        uint256 threatType,
        uint256 severity,
        uint256 timestamp
    );
    
    event AnomalyDetected(
        bytes32 indexed assetId,
        uint256 anomalyScore,
        uint256 price,
        uint256 timestamp
    );
    
    event SecurityActionTaken(
        bytes32 indexed assetId,
        uint256 action,
        string reason,
        uint256 timestamp
    );
    
    event EmergencyModeActivated(
        bytes32 indexed assetId,
        string reason,
        uint256 timestamp
    );

    // =================
    // CONSTRUCTOR
    // =================
    
    constructor(
        address _primaryOracle,
        address _admin
    ) {
        require(_primaryOracle != address(0), "Invalid oracle address");
        require(_admin != address(0), "Invalid admin address");
        
        primaryOracle = SecureMultiOracle(_primaryOracle);
        
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(VALIDATOR_ADMIN_ROLE, _admin);
        _grantRole(SECURITY_ANALYST_ROLE, _admin);
        _grantRole(EMERGENCY_RESPONSE_ROLE, _admin);
    }

    // =================
    // MAIN VALIDATION FUNCTIONS
    // =================
    
    /**
     * @notice Perform comprehensive security validation on price data
     * @param assetId Asset to validate
     * @param price Price to validate
     * @param volume Trading volume
     * @return result Detailed validation result
     */
    function validatePriceSecurity(
        bytes32 assetId,
        uint256 price,
        uint256 volume
    ) external nonReentrant whenNotPaused returns (ValidationResult memory result) {
        require(price > 0, "Invalid price");
        
        // Check emergency mode
        if (emergencyMode[assetId]) {
            result.isValid = false;
            result.warnings = new string[](1);
            result.warnings[0] = "Asset in emergency mode";
            result.recommendedAction = uint256(SecurityAction.PAUSE_OPERATIONS);
            return result;
        }
        
        // Record price data
        _recordPriceData(assetId, price, volume);
        
        // Perform statistical analysis
        result.anomalyAnalysis = _performAnomalyDetection(assetId, price, volume);
        
        // Calculate confidence and risk
        result.confidenceScore = _calculateConfidenceScore(assetId, result.anomalyAnalysis);
        result.riskLevel = _assessRiskLevel(assetId, result.anomalyAnalysis);
        
        // Determine validity
        result.isValid = result.confidenceScore >= anomalyThreshold && 
                        !result.anomalyAnalysis.isAnomalous;
        
        // Generate warnings and recommendations
        (result.warnings, result.recommendedAction) = _generateRecommendations(
            assetId, 
            result.anomalyAnalysis,
            result.riskLevel
        );
        
        // Check for security threats
        _checkSecurityThreats(assetId, price, volume, result.anomalyAnalysis);
        
        return result;
    }
    
    /**
     * @notice Perform real-time threat analysis
     * @param assetId Asset to analyze
     */
    function performThreatAnalysis(bytes32 assetId) 
        external 
        onlyRole(SECURITY_ANALYST_ROLE) 
        nonReentrant 
    {
        require(
            block.timestamp >= lastSecurityCheck[assetId] + SHORT_TERM_WINDOW,
            "Analysis interval not elapsed"
        );
        
        lastSecurityCheck[assetId] = block.timestamp;
        
        // Comprehensive threat detection
        _detectFlashLoanManipulation(assetId);
        _detectCoordinatedAttacks(assetId);
        _detectVolumeManipulation(assetId);
        _detectTimestampManipulation(assetId);
        _updateThreatScore(assetId);
        
        // Auto-response to high threats
        if (threatScores[assetId] > emergencyThreshold) {
            _activateEmergencyMode(assetId, "High threat score detected");
        }
    }

    // =================
    // ANOMALY DETECTION
    // =================
    
    /**
     * @notice Perform comprehensive anomaly detection
     */
    function _performAnomalyDetection(
        bytes32 assetId,
        uint256 price,
        uint256 volume
    ) internal view returns (AnomalyScore memory score) {
        
        // Z-Score analysis
        score.zScore = _calculateZScore(assetId, price);
        
        // Isolation forest score (simplified)
        score.isolationScore = _calculateIsolationScore(assetId, price);
        
        // Mahalanobis distance for multivariate analysis
        score.mahalanobisDistance = _calculateMahalanobisDistance(assetId, price, volume);
        
        // Price velocity analysis
        score.velocityScore = _calculateVelocityScore(assetId, price);
        
        // Volume anomaly analysis
        score.volumeScore = _calculateVolumeScore(assetId, volume);
        
        // Combined anomaly score
        score.combinedScore = _calculateCombinedScore(score);
        
        // Determine if anomalous
        score.isAnomalous = score.combinedScore > anomalyThreshold;
        
        return score;
    }
    
    function _calculateZScore(bytes32 assetId, uint256 price) 
        internal 
        view 
        returns (uint256) 
    {
        StatisticalMetrics memory stats = assetStatistics[assetId];
        
        if (stats.standardDeviation == 0) return 0;
        
        uint256 deviation = price > stats.mean 
            ? price - stats.mean 
            : stats.mean - price;
            
        return (deviation * 10000) / stats.standardDeviation;
    }
    
    function _calculateIsolationScore(bytes32 assetId, uint256 price) 
        internal 
        view 
        returns (uint256) 
    {
        // Simplified isolation forest calculation
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < 10) return 0;
        
        uint256 isolationCount = 0;
        uint256 totalComparisons = 0;
        
        // Sample recent history for isolation calculation
        uint256 sampleSize = Math.min(50, history.length);
        uint256 startIndex = history.length - sampleSize;
        
        for (uint256 i = startIndex; i < history.length; i++) {
            uint256 historicalPrice = history[i].price;
            uint256 difference = price > historicalPrice 
                ? price - historicalPrice 
                : historicalPrice - price;
                
            uint256 percentDiff = (difference * 10000) / historicalPrice;
            
            if (percentDiff > 1000) { // 10% difference threshold
                isolationCount++;
            }
            totalComparisons++;
        }
        
        return totalComparisons > 0 
            ? (isolationCount * 10000) / totalComparisons 
            : 0;
    }
    
    function _calculateMahalanobisDistance(
        bytes32 assetId, 
        uint256 price, 
        uint256 volume
    ) internal view returns (uint256) {
        // Simplified multivariate distance calculation
        StatisticalMetrics memory stats = assetStatistics[assetId];
        uint256 volumeBaseline = volumeBaselines[assetId];
        
        if (stats.standardDeviation == 0 || volumeBaseline == 0) return 0;
        
        // Calculate normalized deviations
        uint256 priceDeviation = price > stats.mean 
            ? ((price - stats.mean) * 10000) / stats.standardDeviation
            : ((stats.mean - price) * 10000) / stats.standardDeviation;
            
        uint256 volumeDeviation = volume > volumeBaseline 
            ? ((volume - volumeBaseline) * 10000) / volumeBaseline
            : ((volumeBaseline - volume) * 10000) / volumeBaseline;
        
        // Simplified distance (assuming independence)
        return Math.sqrt(priceDeviation ** 2 + volumeDeviation ** 2);
    }
    
    function _calculateVelocityScore(bytes32 assetId, uint256 price) 
        internal 
        view 
        returns (uint256) 
    {
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < 2) return 0;
        
        uint256 lastPrice = history[history.length - 1].price;
        uint256 lastTimestamp = history[history.length - 1].timestamp;
        
        if (block.timestamp <= lastTimestamp) return 0;
        
        uint256 timeDelta = block.timestamp - lastTimestamp;
        uint256 priceDelta = price > lastPrice 
            ? price - lastPrice 
            : lastPrice - price;
            
        // Calculate velocity (price change per minute)
        uint256 velocity = (priceDelta * 60 * 10000) / (lastPrice * timeDelta);
        
        return velocity;
    }
    
    function _calculateVolumeScore(bytes32 assetId, uint256 volume) 
        internal 
        view 
        returns (uint256) 
    {
        uint256 baseline = volumeBaselines[assetId];
        
        if (baseline == 0) return 0;
        
        return volume > baseline 
            ? ((volume - baseline) * 10000) / baseline
            : ((baseline - volume) * 10000) / baseline;
    }
    
    function _calculateCombinedScore(AnomalyScore memory scores) 
        internal 
        pure 
        returns (uint256) 
    {
        // Weighted combination of different scores
        uint256 combined = (
            scores.zScore * 25 +
            scores.isolationScore * 20 +
            scores.mahalanobisDistance * 20 +
            scores.velocityScore * 20 +
            scores.volumeScore * 15
        ) / 100;
        
        return combined;
    }

    // =================
    // THREAT DETECTION
    // =================
    
    function _detectFlashLoanManipulation(bytes32 assetId) internal {
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < 3) return;
        
        // Check for rapid price changes within single block
        uint256 currentBlock = block.number;
        uint256 sameBlockCount = 0;
        uint256 maxPriceChange = 0;
        
        for (uint256 i = history.length; i > 0 && i > history.length - 10; i--) {
            if (history[i-1].blockNumber == currentBlock) {
                sameBlockCount++;
                
                if (i > 1) {
                    uint256 priceChange = history[i-1].price > history[i-2].price
                        ? ((history[i-1].price - history[i-2].price) * 10000) / history[i-2].price
                        : ((history[i-2].price - history[i-1].price) * 10000) / history[i-2].price;
                    
                    if (priceChange > maxPriceChange) {
                        maxPriceChange = priceChange;
                    }
                }
            }
        }
        
        // Flash loan manipulation pattern: multiple updates in same block with large changes
        if (sameBlockCount >= 2 && maxPriceChange > 1000) { // 10%
            _recordThreat(
                assetId,
                ThreatType.FLASH_LOAN_ATTACK,
                8000, // 80% confidence
                "Flash loan manipulation pattern detected"
            );
        }
    }
    
    function _detectCoordinatedAttacks(bytes32 assetId) internal {
        // Simplified coordinated attack detection
        // Would analyze correlation with other assets and timing patterns
        
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < 5) return;
        
        uint256 simultaneousUpdates = 0;
        uint256 recentTimestamp = block.timestamp - SHORT_TERM_WINDOW;
        
        for (uint256 i = history.length; i > 0; i--) {
            if (history[i-1].timestamp >= recentTimestamp) {
                simultaneousUpdates++;
            } else {
                break;
            }
        }
        
        // High frequency updates might indicate coordinated manipulation
        if (simultaneousUpdates > 10) {
            _recordThreat(
                assetId,
                ThreatType.COORDINATED_ATTACK,
                7000, // 70% confidence
                "Suspicious high-frequency updates detected"
            );
        }
    }
    
    function _detectVolumeManipulation(bytes32 assetId) internal {
        PriceDataPoint[] memory history = priceHistory[assetId];
        uint256 baseline = volumeBaselines[assetId];
        
        if (history.length == 0 || baseline == 0) return;
        
        uint256 recentVolume = history[history.length - 1].volume;
        
        // Volume manipulation: extremely high volume compared to baseline
        if (recentVolume > baseline * VOLUME_ANOMALY_MULTIPLIER / 100) {
            _recordThreat(
                assetId,
                ThreatType.VOLUME_MANIPULATION,
                7500, // 75% confidence
                "Abnormal volume spike detected"
            );
        }
    }
    
    function _detectTimestampManipulation(bytes32 assetId) internal {
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < 2) return;
        
        uint256 lastTimestamp = history[history.length - 1].timestamp;
        uint256 currentTime = block.timestamp;
        
        // Timestamp manipulation: future timestamps or too rapid updates
        if (lastTimestamp > currentTime + 300) { // 5 minutes in future
            _recordThreat(
                assetId,
                ThreatType.TIMESTAMP_MANIPULATION,
                9000, // 90% confidence
                "Future timestamp detected"
            );
        }
    }
    
    function _recordThreat(
        bytes32 assetId,
        ThreatType threatType,
        uint256 confidence,
        string memory description
    ) internal {
        bytes32 threatId = keccak256(abi.encodePacked(
            assetId,
            uint256(threatType),
            block.timestamp,
            block.number
        ));
        
        SecurityThreat memory threat = SecurityThreat({
            threatId: threatId,
            threatType: uint256(threatType),
            severity: _calculateThreatSeverity(confidence),
            confidence: confidence,
            assetId: assetId,
            detectedAt: block.timestamp,
            priceAtDetection: _getCurrentPrice(assetId),
            description: description,
            mitigated: false,
            mitigationAction: uint256(SecurityAction.NONE)
        });
        
        detectedThreats[assetId].push(threat);
        
        emit ThreatDetected(
            threatId,
            assetId,
            uint256(threatType),
            threat.severity,
            block.timestamp
        );
    }
    
    function _calculateThreatSeverity(uint256 confidence) internal pure returns (uint256) {
        if (confidence >= 9500) return 4; // CRITICAL
        if (confidence >= 8500) return 3; // HIGH
        if (confidence >= 7000) return 2; // MEDIUM
        return 1; // LOW
    }

    // =================
    // HELPER FUNCTIONS
    // =================
    
    function _recordPriceData(bytes32 assetId, uint256 price, uint256 volume) internal {
        PriceDataPoint memory dataPoint = PriceDataPoint({
            price: price,
            timestamp: block.timestamp,
            volume: volume,
            gasUsed: gasleft(),
            submitter: msg.sender,
            blockNumber: block.number
        });
        
        priceHistory[assetId].push(dataPoint);
        
        // Maintain maximum history length
        if (priceHistory[assetId].length > maxHistoryLength) {
            // Remove oldest entries (simplified - would use circular buffer in production)
            for (uint256 i = 0; i < priceHistory[assetId].length - maxHistoryLength; i++) {
                priceHistory[assetId][i] = priceHistory[assetId][i + 1];
            }
            priceHistory[assetId].pop();
        }
        
        // Update statistics
        _updateStatistics(assetId);
    }
    
    function _updateStatistics(bytes32 assetId) internal {
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length == 0) return;
        
        // Calculate basic statistics
        uint256 sum = 0;
        for (uint256 i = 0; i < history.length; i++) {
            sum += history[i].price;
        }
        
        uint256 mean = sum / history.length;
        
        // Calculate variance
        uint256 varianceSum = 0;
        for (uint256 i = 0; i < history.length; i++) {
            uint256 diff = history[i].price > mean 
                ? history[i].price - mean 
                : mean - history[i].price;
            varianceSum += diff ** 2;
        }
        
        uint256 variance = varianceSum / history.length;
        uint256 standardDeviation = Math.sqrt(variance);
        
        assetStatistics[assetId] = StatisticalMetrics({
            mean: mean,
            standardDeviation: standardDeviation,
            variance: variance,
            skewness: 0, // Simplified
            kurtosis: 0, // Simplified
            lastUpdate: block.timestamp
        });
    }
    
    function _calculateConfidenceScore(
        bytes32 assetId,
        AnomalyScore memory anomalyScore
    ) internal view returns (uint256) {
        // Base confidence starts at 100%
        uint256 confidence = 10000;
        
        // Reduce confidence based on anomaly scores
        confidence = confidence > anomalyScore.combinedScore 
            ? confidence - anomalyScore.combinedScore 
            : 0;
        
        // Factor in threat score
        uint256 threatScore = threatScores[assetId];
        confidence = confidence > threatScore / 2 
            ? confidence - threatScore / 2 
            : 0;
        
        return confidence;
    }
    
    function _assessRiskLevel(
        bytes32 assetId,
        AnomalyScore memory anomalyScore
    ) internal view returns (uint256) {
        uint256 riskLevel = 0;
        
        // Base risk from anomaly score
        if (anomalyScore.combinedScore > 9500) riskLevel = 4; // CRITICAL
        else if (anomalyScore.combinedScore > 8500) riskLevel = 3; // HIGH
        else if (anomalyScore.combinedScore > 7000) riskLevel = 2; // MEDIUM
        else if (anomalyScore.combinedScore > 5000) riskLevel = 1; // LOW
        
        // Escalate based on threat score
        uint256 threatScore = threatScores[assetId];
        if (threatScore > 9000) riskLevel = Math.max(riskLevel, 4);
        else if (threatScore > 8000) riskLevel = Math.max(riskLevel, 3);
        else if (threatScore > 6000) riskLevel = Math.max(riskLevel, 2);
        
        return riskLevel;
    }
    
    function _generateRecommendations(
        bytes32 assetId,
        AnomalyScore memory anomalyScore,
        uint256 riskLevel
    ) internal view returns (string[] memory warnings, uint256 recommendedAction) {
        warnings = new string[](0);
        recommendedAction = uint256(SecurityAction.NONE);
        
        if (riskLevel >= 4) {
            warnings = _addWarning(warnings, "CRITICAL: Immediate action required");
            recommendedAction = uint256(SecurityAction.EMERGENCY_SHUTDOWN);
        } else if (riskLevel >= 3) {
            warnings = _addWarning(warnings, "HIGH: Enhanced monitoring required");
            recommendedAction = uint256(SecurityAction.ACTIVATE_CIRCUIT_BREAKER);
        } else if (riskLevel >= 2) {
            warnings = _addWarning(warnings, "MEDIUM: Additional consensus required");
            recommendedAction = uint256(SecurityAction.REQUIRE_CONSENSUS);
        } else if (riskLevel >= 1) {
            warnings = _addWarning(warnings, "LOW: Increased monitoring recommended");
            recommendedAction = uint256(SecurityAction.INCREASE_MONITORING);
        }
        
        if (anomalyScore.velocityScore > PRICE_VELOCITY_THRESHOLD) {
            warnings = _addWarning(warnings, "High price velocity detected");
        }
        
        if (anomalyScore.volumeScore > 5000) {
            warnings = _addWarning(warnings, "Abnormal volume detected");
        }
        
        return (warnings, recommendedAction);
    }
    
    function _addWarning(string[] memory warnings, string memory newWarning) 
        internal 
        pure 
        returns (string[] memory) 
    {
        string[] memory newWarnings = new string[](warnings.length + 1);
        for (uint256 i = 0; i < warnings.length; i++) {
            newWarnings[i] = warnings[i];
        }
        newWarnings[warnings.length] = newWarning;
        return newWarnings;
    }
    
    function _getCurrentPrice(bytes32 assetId) internal view returns (uint256) {
        PriceDataPoint[] memory history = priceHistory[assetId];
        return history.length > 0 ? history[history.length - 1].price : 0;
    }
    
    function _updateThreatScore(bytes32 assetId) internal {
        SecurityThreat[] memory threats = detectedThreats[assetId];
        
        uint256 totalScore = 0;
        uint256 recentThreats = 0;
        uint256 cutoffTime = block.timestamp - MEDIUM_TERM_WINDOW;
        
        for (uint256 i = 0; i < threats.length; i++) {
            if (threats[i].detectedAt >= cutoffTime && !threats[i].mitigated) {
                totalScore += threats[i].confidence;
                recentThreats++;
            }
        }
        
        // Average threat score with decay
        threatScores[assetId] = recentThreats > 0 
            ? totalScore / recentThreats 
            : threatScores[assetId] * 95 / 100; // 5% decay
    }
    
    function _activateEmergencyMode(bytes32 assetId, string memory reason) internal {
        emergencyMode[assetId] = true;
        
        emit EmergencyModeActivated(assetId, reason, block.timestamp);
        emit SecurityActionTaken(
            assetId,
            uint256(SecurityAction.EMERGENCY_SHUTDOWN),
            reason,
            block.timestamp
        );
    }
    
    function _checkSecurityThreats(
        bytes32 assetId,
        uint256 price,
        uint256 volume,
        AnomalyScore memory anomalyScore
    ) internal {
        // Check for statistical anomalies
        if (anomalyScore.isAnomalous) {
            _recordThreat(
                assetId,
                ThreatType.STATISTICAL_ANOMALY,
                anomalyScore.combinedScore / 100,
                "Statistical anomaly detected in price data"
            );
        }
        
        // Update threat monitoring
        _updateThreatScore(assetId);
    }

    // =================
    // ADMIN FUNCTIONS
    // =================
    
    function setAnomalyThreshold(uint256 _threshold) 
        external 
        onlyRole(VALIDATOR_ADMIN_ROLE) 
    {
        require(_threshold <= 10000, "Invalid threshold");
        anomalyThreshold = _threshold;
    }
    
    function setEmergencyThreshold(uint256 _threshold) 
        external 
        onlyRole(VALIDATOR_ADMIN_ROLE) 
    {
        require(_threshold <= 10000, "Invalid threshold");
        emergencyThreshold = _threshold;
    }
    
    function resetEmergencyMode(bytes32 assetId) 
        external 
        onlyRole(EMERGENCY_RESPONSE_ROLE) 
    {
        require(emergencyMode[assetId], "Emergency mode not active");
        emergencyMode[assetId] = false;
        
        emit SecurityActionTaken(
            assetId,
            uint256(SecurityAction.NONE),
            "Emergency mode reset by admin",
            block.timestamp
        );
    }
    
    function mitigateThreat(bytes32 assetId, bytes32 threatId) 
        external 
        onlyRole(SECURITY_ANALYST_ROLE) 
    {
        SecurityThreat[] storage threats = detectedThreats[assetId];
        
        for (uint256 i = 0; i < threats.length; i++) {
            if (threats[i].threatId == threatId) {
                threats[i].mitigated = true;
                threats[i].mitigationAction = uint256(SecurityAction.INCREASE_MONITORING);
                break;
            }
        }
    }

    // =================
    // VIEW FUNCTIONS
    // =================
    
    function getAssetStatistics(bytes32 assetId) 
        external 
        view 
        returns (StatisticalMetrics memory) 
    {
        return assetStatistics[assetId];
    }
    
    function getThreatScore(bytes32 assetId) external view returns (uint256) {
        return threatScores[assetId];
    }
    
    function getRecentThreats(bytes32 assetId, uint256 timeWindow) 
        external 
        view 
        returns (SecurityThreat[] memory) 
    {
        SecurityThreat[] memory allThreats = detectedThreats[assetId];
        uint256 cutoffTime = block.timestamp - timeWindow;
        
        // Count recent threats
        uint256 recentCount = 0;
        for (uint256 i = 0; i < allThreats.length; i++) {
            if (allThreats[i].detectedAt >= cutoffTime) {
                recentCount++;
            }
        }
        
        // Build recent threats array
        SecurityThreat[] memory recentThreats = new SecurityThreat[](recentCount);
        uint256 index = 0;
        for (uint256 i = 0; i < allThreats.length; i++) {
            if (allThreats[i].detectedAt >= cutoffTime) {
                recentThreats[index] = allThreats[i];
                index++;
            }
        }
        
        return recentThreats;
    }
    
    function isEmergencyMode(bytes32 assetId) external view returns (bool) {
        return emergencyMode[assetId];
    }
}
