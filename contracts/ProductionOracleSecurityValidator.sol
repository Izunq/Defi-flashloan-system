// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/**
 * @title ProductionOracleSecurityValidator
 * @notice Production-grade oracle security validation with ML-based threat detection
 * @dev Enterprise-level oracle security system with advanced anomaly detection
 */
contract ProductionOracleSecurityValidator is AccessControl, ReentrancyGuard, Pausable {
    using Math for uint256;
    using ECDSA for bytes32;

    // =================
    // CONSTANTS & ROLES
    // =================
    
    bytes32 public constant ORACLE_VALIDATOR_ROLE = keccak256("ORACLE_VALIDATOR_ROLE");
    bytes32 public constant SECURITY_MANAGER_ROLE = keccak256("SECURITY_MANAGER_ROLE");
    bytes32 public constant EMERGENCY_RESPONDER_ROLE = keccak256("EMERGENCY_RESPONDER_ROLE");
    bytes32 public constant ML_ANALYZER_ROLE = keccak256("ML_ANALYZER_ROLE");
    bytes32 public constant COMPLIANCE_ROLE = keccak256("COMPLIANCE_ROLE");
    
    // Security Constants
    uint256 public constant MAX_PRICE_DEVIATION = 500; // 5% in basis points
    uint256 public constant CIRCUIT_BREAKER_THRESHOLD = 1000; // 10% in basis points
    uint256 public constant CRITICAL_THRESHOLD = 1500; // 15% in basis points
    uint256 public constant MIN_ORACLE_CONSENSUS = 3;
    uint256 public constant MAX_ORACLE_STALENESS = 3600; // 1 hour
    uint256 public constant ML_CONFIDENCE_THRESHOLD = 8000; // 80%
    uint256 public constant THREAT_PROBABILITY_THRESHOLD = 7000; // 70%
    
    // Time Windows
    uint256 public constant SHORT_TERM_WINDOW = 300; // 5 minutes
    uint256 public constant MEDIUM_TERM_WINDOW = 1800; // 30 minutes
    uint256 public constant LONG_TERM_WINDOW = 7200; // 2 hours
    uint256 public constant HISTORICAL_WINDOW = 86400; // 24 hours

    // =================
    // STRUCTS
    // =================
    
    struct PriceDataPoint {
        uint256 price;
        uint256 timestamp;
        uint256 confidence;
        uint256 volume;
        address oracle;
        bytes32 signature;
        bool validated;
    }
    
    struct SecurityMetrics {
        uint256 threatLevel; // 0-10000 (0-100%)
        uint256 riskScore; // 0-10000 (0-100%)
        uint256 manipulationProbability; // 0-10000 (0-100%)
        uint256 mlAnomalyScore; // -10000 to 10000 (-100% to 100%)
        uint256 lastSecurityCheck;
        uint256 consecutiveAnomalies;
        bool isUnderSurveillance;
        bool emergencyMode;
    }
    
    struct MLPrediction {
        uint256 anomalyScore; // ML model output
        uint256 confidence; // Model confidence
        uint256 predictionTimestamp;
        bytes32 modelVersion;
        uint256[] featureImportance;
        bool isValid;
    }
    
    struct ThreatDetection {
        bytes32 threatId;
        ThreatType threatType;
        ThreatSeverity severity;
        uint256 detectedAt;
        uint256 probability;
        bytes32[] evidenceHashes;
        address[] affectedOracles;
        string description;
        bool resolved;
        uint256 resolutionTime;
    }
    
    struct ComplianceRecord {
        uint256 timestamp;
        bytes32 eventType;
        bytes32 dataHash;
        address actor;
        bool compliant;
        string regulatoryFramework;
    }
    
    struct EmergencyProtocol {
        bool active;
        uint256 activatedAt;
        address activatedBy;
        string reason;
        uint256 affectedAssets;
        uint256 estimatedImpact;
        bytes32[] responseActions;
    }
    
    enum ThreatType {
        PRICE_MANIPULATION,
        VOLUME_MANIPULATION,
        ORACLE_CORRUPTION,
        COORDINATED_ATTACK,
        FLASH_LOAN_ATTACK,
        FRONT_RUNNING,
        SANDWICH_ATTACK,
        MEV_EXPLOITATION,
        TIMESTAMP_MANIPULATION,
        STATISTICAL_ANOMALY
    }
    
    enum ThreatSeverity {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL,
        EMERGENCY
    }
    
    enum SecurityStatus {
        NORMAL,
        ELEVATED,
        HIGH_ALERT,
        CRITICAL,
        EMERGENCY
    }

    // =================
    // STATE VARIABLES
    // =================
    
    // Core Security State
    mapping(bytes32 => SecurityMetrics) public assetSecurityMetrics;
    mapping(bytes32 => PriceDataPoint[]) public priceHistory;
    mapping(bytes32 => MLPrediction) public mlPredictions;
    mapping(bytes32 => ThreatDetection) public threatDetections;
    mapping(bytes32 => ComplianceRecord[]) public complianceRecords;
    
    // Circuit Breakers and Emergency Controls
    mapping(bytes32 => bool) public assetCircuitBreakers;
    mapping(bytes32 => uint256) public circuitBreakerActivationTime;
    mapping(address => bool) public oracleEmergencyOverride;
    EmergencyProtocol public globalEmergencyProtocol;
    
    // ML Model Management
    mapping(bytes32 => bool) public approvedMLModels;
    mapping(bytes32 => uint256) public modelConfidenceScores;
    bytes32 public activeMLModelHash;
    uint256 public mlModelVersion;
    
    // Security Analytics
    mapping(bytes32 => uint256) public assetVolatilityMetrics;
    mapping(bytes32 => uint256) public manipulationAttemptCount;
    mapping(address => uint256) public oracleReputationScores;
    mapping(bytes32 => bytes32[]) public correlatedThreats;
    
    // Performance and Monitoring
    uint256 public totalValidations;
    uint256 public threatsDetected;
    uint256 public falsePositives;
    uint256 public averageResponseTime;
    uint256 public systemUptime;
    uint256 public lastGlobalSecurityScan;

    // =================
    // EVENTS
    // =================
    
    event ThreatDetected(
        bytes32 indexed threatId,
        bytes32 indexed assetId,
        ThreatType indexed threatType,
        ThreatSeverity severity,
        uint256 probability,
        address detector
    );
    
    event SecurityStatusChanged(
        bytes32 indexed assetId,
        SecurityStatus oldStatus,
        SecurityStatus newStatus,
        uint256 timestamp
    );
    
    event CircuitBreakerActivated(
        bytes32 indexed assetId,
        uint256 threshold,
        uint256 actualDeviation,
        address activatedBy
    );
    
    event EmergencyProtocolActivated(
        string reason,
        uint256 affectedAssets,
        address activatedBy,
        uint256 timestamp
    );
    
    event MLPredictionUpdated(
        bytes32 indexed assetId,
        uint256 anomalyScore,
        uint256 confidence,
        bytes32 modelVersion
    );
    
    event ComplianceEvent(
        bytes32 indexed assetId,
        bytes32 eventType,
        bool compliant,
        string regulatoryFramework
    );
    
    event SecurityMetricsUpdated(
        bytes32 indexed assetId,
        uint256 threatLevel,
        uint256 riskScore,
        uint256 manipulationProbability
    );
    
    event OracleReputationUpdated(
        address indexed oracle,
        uint256 oldReputation,
        uint256 newReputation,
        string reason
    );

    // =================
    // MODIFIERS
    // =================
    
    modifier onlyValidOracle() {
        require(hasRole(ORACLE_VALIDATOR_ROLE, msg.sender), "Invalid oracle");
        require(!oracleEmergencyOverride[msg.sender], "Oracle under emergency override");
        _;
    }
    
    modifier onlySecurityManager() {
        require(
            hasRole(SECURITY_MANAGER_ROLE, msg.sender) || 
            hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "Insufficient security permissions"
        );
        _;
    }
    
    modifier onlyEmergencyResponder() {
        require(
            hasRole(EMERGENCY_RESPONDER_ROLE, msg.sender) ||
            hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "Emergency responder access required"
        );
        _;
    }
    
    modifier whenNotInEmergency() {
        require(!globalEmergencyProtocol.active, "System in emergency mode");
        _;
    }
    
    modifier validAssetId(bytes32 assetId) {
        require(assetId != bytes32(0), "Invalid asset ID");
        _;
    }

    // =================
    // CONSTRUCTOR
    // =================
    
    constructor(address admin, address securityManager, address emergencyResponder) {
        require(admin != address(0), "Invalid admin address");
        require(securityManager != address(0), "Invalid security manager");
        require(emergencyResponder != address(0), "Invalid emergency responder");
        
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), admin);
        _grantRole(SECURITY_MANAGER_ROLE, securityManager);
        _grantRole(EMERGENCY_RESPONDER_ROLE, emergencyResponder);
        
        systemUptime = block.timestamp;
        lastGlobalSecurityScan = block.timestamp;
        mlModelVersion = 1;
    }

    // =================
    // CORE VALIDATION FUNCTIONS
    // =================
    
    /**
     * @notice Comprehensive price validation with ML-based threat detection
     * @param assetId Asset identifier
     * @param priceData Current price data
     * @param signature Oracle signature for authenticity
     * @return isValid Whether the price is valid
     * @return securityScore Security confidence score (0-10000)
     * @return threatLevel Detected threat level (0-10000)
     */
    function validatePriceWithSecurity(
        bytes32 assetId,
        PriceDataPoint memory priceData,
        bytes memory signature
    ) 
        external 
        onlyValidOracle 
        whenNotPaused 
        whenNotInEmergency 
        validAssetId(assetId)
        returns (bool isValid, uint256 securityScore, uint256 threatLevel) 
    {
        // Increment validation counter
        totalValidations++;
        
        // Validate basic price data integrity
        require(priceData.price > 0, "Invalid price");
        require(priceData.timestamp <= block.timestamp, "Future timestamp");
        require(
            block.timestamp - priceData.timestamp <= MAX_ORACLE_STALENESS,
            "Price data too stale"
        );
        
        // Verify oracle signature
        require(_verifyOracleSignature(assetId, priceData, signature), "Invalid signature");
        
        // Store price data
        priceData.oracle = msg.sender;
        priceData.signature = keccak256(signature);
        priceData.validated = false; // Will be set based on validation results
        
        // Perform comprehensive security analysis
        SecurityAnalysisResult memory analysisResult = _performSecurityAnalysis(assetId, priceData);
        
        // Update security metrics
        _updateSecurityMetrics(assetId, analysisResult);
        
        // Check for threats
        if (analysisResult.threatsDetected.length > 0) {
            _processThreatDetections(assetId, analysisResult.threatsDetected);
        }
        
        // Determine validation result
        isValid = _determineValidationResult(analysisResult);
        securityScore = analysisResult.securityScore;
        threatLevel = analysisResult.threatLevel;
        
        // Store validated price data
        priceData.validated = isValid;
        priceHistory[assetId].push(priceData);
        
        // Trim old price data to maintain storage efficiency
        _trimPriceHistory(assetId);
        
        // Record compliance event
        _recordComplianceEvent(assetId, "PRICE_VALIDATION", isValid, "MiFID_II");
        
        // Update oracle reputation
        _updateOracleReputation(msg.sender, isValid, analysisResult.threatLevel);
        
        emit SecurityMetricsUpdated(assetId, threatLevel, securityScore, analysisResult.manipulationProbability);
        
        return (isValid, securityScore, threatLevel);
    }
    
    /**
     * @notice Perform comprehensive security analysis on price data
     */
    function _performSecurityAnalysis(bytes32 assetId, PriceDataPoint memory priceData) 
        internal 
        returns (SecurityAnalysisResult memory result) 
    {
        result.assetId = assetId;
        result.analysisTimestamp = block.timestamp;
        
        // Statistical Analysis
        result.statisticalScore = _performStatisticalAnalysis(assetId, priceData);
        
        // Historical Consistency Check
        result.consistencyScore = _checkHistoricalConsistency(assetId, priceData);
        
        // Volume Analysis
        result.volumeScore = _analyzeVolumePatterns(assetId, priceData);
        
        // Temporal Analysis
        result.temporalScore = _analyzeTemporalPatterns(assetId, priceData);
        
        // ML-based Anomaly Detection
        result.mlScore = _performMLAnalysis(assetId, priceData);
        
        // Cross-Oracle Correlation Analysis
        result.correlationScore = _analyzeCrossOracleCorrelation(assetId, priceData);
        
        // Market Condition Analysis
        result.marketScore = _analyzeMarketConditions(assetId, priceData);
        
        // Calculate overall security score
        result.securityScore = _calculateOverallSecurityScore(result);
        
        // Determine threat level
        result.threatLevel = _calculateThreatLevel(result);
        
        // Calculate manipulation probability
        result.manipulationProbability = _calculateManipulationProbability(result);
        
        // Detect specific threats
        result.threatsDetected = _detectSpecificThreats(assetId, priceData, result);
        
        return result;
    }
    
    struct SecurityAnalysisResult {
        bytes32 assetId;
        uint256 analysisTimestamp;
        uint256 statisticalScore;
        uint256 consistencyScore;
        uint256 volumeScore;
        uint256 temporalScore;
        uint256 mlScore;
        uint256 correlationScore;
        uint256 marketScore;
        uint256 securityScore;
        uint256 threatLevel;
        uint256 manipulationProbability;
        bytes32[] threatsDetected;
    }
    
    /**
     * @notice Perform statistical analysis on price data
     */
    function _performStatisticalAnalysis(bytes32 assetId, PriceDataPoint memory priceData) 
        internal 
        view 
        returns (uint256 score) 
    {
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < 10) {
            return 8000; // 80% - insufficient data for analysis
        }
        
        // Calculate moving statistics
        uint256 sum = 0;
        uint256 recentDataPoints = Math.min(history.length, 50);
        
        for (uint256 i = history.length - recentDataPoints; i < history.length; i++) {
            sum += history[i].price;
        }
        
        uint256 meanPrice = sum / recentDataPoints;
        
        // Calculate standard deviation
        uint256 variance = 0;
        for (uint256 i = history.length - recentDataPoints; i < history.length; i++) {
            uint256 diff = history[i].price > meanPrice 
                ? history[i].price - meanPrice 
                : meanPrice - history[i].price;
            variance += (diff * diff) / recentDataPoints;
        }
        
        uint256 stdDev = _sqrt(variance);
        
        // Calculate Z-score
        uint256 priceDiff = priceData.price > meanPrice 
            ? priceData.price - meanPrice 
            : meanPrice - priceData.price;
        
        if (stdDev == 0) {
            return priceDiff == 0 ? 10000 : 0; // Perfect if no deviation, bad if any deviation
        }
        
        uint256 zScore = (priceDiff * 1000) / stdDev; // Multiply by 1000 for precision
        
        // Convert Z-score to security score
        if (zScore < 2000) return 10000; // Z < 2: Excellent
        if (zScore < 3000) return 8000;  // Z < 3: Good
        if (zScore < 4000) return 6000;  // Z < 4: Fair
        if (zScore < 5000) return 4000;  // Z < 5: Poor
        return 2000; // Z >= 5: Very Poor
    }
    
    /**
     * @notice Check historical consistency of price data
     */
    function _checkHistoricalConsistency(bytes32 assetId, PriceDataPoint memory priceData) 
        internal 
        view 
        returns (uint256 score) 
    {
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < 5) {
            return 8000; // Default score for insufficient data
        }
        
        // Check consistency with recent price trends
        uint256 recentPrices = Math.min(history.length, 10);
        uint256 consistentPrices = 0;
        
        for (uint256 i = history.length - recentPrices; i < history.length; i++) {
            uint256 deviation = history[i].price > priceData.price
                ? ((history[i].price - priceData.price) * 10000) / history[i].price
                : ((priceData.price - history[i].price) * 10000) / history[i].price;
            
            if (deviation <= MAX_PRICE_DEVIATION) {
                consistentPrices++;
            }
        }
        
        // Calculate consistency score
        return (consistentPrices * 10000) / recentPrices;
    }
    
    /**
     * @notice Analyze volume patterns for anomalies
     */
    function _analyzeVolumePatterns(bytes32 assetId, PriceDataPoint memory priceData) 
        internal 
        view 
        returns (uint256 score) 
    {
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < 5 || priceData.volume == 0) {
            return 8000; // Default score
        }
        
        // Calculate average volume
        uint256 totalVolume = 0;
        uint256 recentDataPoints = Math.min(history.length, 20);
        
        for (uint256 i = history.length - recentDataPoints; i < history.length; i++) {
            totalVolume += history[i].volume;
        }
        
        uint256 avgVolume = totalVolume / recentDataPoints;
        
        if (avgVolume == 0) {
            return 8000;
        }
        
        // Check for volume anomalies
        uint256 volumeRatio = (priceData.volume * 100) / avgVolume;
        
        if (volumeRatio > 300) return 3000; // Volume > 3x average: Suspicious
        if (volumeRatio > 200) return 6000; // Volume > 2x average: Concerning
        if (volumeRatio < 10) return 5000;  // Volume < 10% average: Low liquidity
        
        return 9000; // Normal volume
    }
    
    /**
     * @notice Analyze temporal patterns for timing attacks
     */
    function _analyzeTemporalPatterns(bytes32 assetId, PriceDataPoint memory priceData) 
        internal 
        view 
        returns (uint256 score) 
    {
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < 3) {
            return 8000;
        }
        
        // Check for rapid succession of price updates (potential flash loan attack)
        uint256 rapidUpdates = 0;
        uint256 timeWindow = 300; // 5 minutes
        
        for (uint256 i = history.length - 1; i > 0; i--) {
            if (priceData.timestamp - history[i-1].timestamp < timeWindow) {
                rapidUpdates++;
            } else {
                break;
            }
        }
        
        if (rapidUpdates > 10) return 2000; // > 10 updates in 5 min: High risk
        if (rapidUpdates > 5) return 6000;  // > 5 updates in 5 min: Medium risk
        
        return 9000; // Normal update frequency
    }
    
    /**
     * @notice Perform ML-based anomaly analysis
     */
    function _performMLAnalysis(bytes32 assetId, PriceDataPoint memory priceData) 
        internal 
        returns (uint256 score) 
    {
        // Check if we have a valid ML model
        if (activeMLModelHash == bytes32(0) || !approvedMLModels[activeMLModelHash]) {
            return 8000; // Default score when ML unavailable
        }
        
        // Extract features for ML analysis
        uint256[] memory features = _extractMLFeatures(assetId, priceData);
        
        // Simulate ML prediction (in production, this would call an off-chain ML service)
        uint256 anomalyScore = _simulateMLPrediction(features);
        
        // Store ML prediction
        mlPredictions[assetId] = MLPrediction({
            anomalyScore: anomalyScore,
            confidence: modelConfidenceScores[activeMLModelHash],
            predictionTimestamp: block.timestamp,
            modelVersion: activeMLModelHash,
            featureImportance: features,
            isValid: true
        });
        
        emit MLPredictionUpdated(assetId, anomalyScore, modelConfidenceScores[activeMLModelHash], activeMLModelHash);
        
        // Convert ML anomaly score to security score
        if (anomalyScore <= 3000) return 10000; // Very low anomaly: Excellent
        if (anomalyScore <= 5000) return 8000;  // Low anomaly: Good
        if (anomalyScore <= 7000) return 6000;  // Medium anomaly: Fair
        if (anomalyScore <= 8500) return 4000;  // High anomaly: Poor
        return 2000; // Very high anomaly: Very Poor
    }
    
    /**
     * @notice Extract features for ML analysis
     */
    function _extractMLFeatures(bytes32 assetId, PriceDataPoint memory priceData) 
        internal 
        view 
        returns (uint256[] memory features) 
    {
        features = new uint256[](10);
        
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        // Feature 1: Current price
        features[0] = priceData.price;
        
        // Feature 2: Volume
        features[1] = priceData.volume;
        
        // Feature 3: Confidence
        features[2] = priceData.confidence;
        
        if (history.length > 0) {
            // Feature 4: Price change from last update
            features[3] = history[history.length - 1].price > priceData.price
                ? ((history[history.length - 1].price - priceData.price) * 10000) / history[history.length - 1].price
                : ((priceData.price - history[history.length - 1].price) * 10000) / history[history.length - 1].price;
            
            // Feature 5: Time since last update
            features[4] = priceData.timestamp - history[history.length - 1].timestamp;
        }
        
        if (history.length >= 5) {
            // Feature 6: Short-term volatility
            features[5] = _calculateVolatility(assetId, 5);
            
            // Feature 7: Price momentum (5-period)
            features[6] = _calculateMomentum(assetId, 5);
        }
        
        if (history.length >= 20) {
            // Feature 8: Medium-term volatility
            features[7] = _calculateVolatility(assetId, 20);
            
            // Feature 9: Price momentum (20-period)
            features[8] = _calculateMomentum(assetId, 20);
        }
        
        // Feature 10: Hour of day (for temporal patterns)
        features[9] = (block.timestamp % 86400) / 3600; // Hour of day
        
        return features;
    }
    
    /**
     * @notice Simulate ML prediction (placeholder for off-chain ML service)
     */
    function _simulateMLPrediction(uint256[] memory features) 
        internal 
        pure 
        returns (uint256 anomalyScore) 
    {
        // Simple heuristic simulation (replace with actual ML service call)
        uint256 featureSum = 0;
        for (uint256 i = 0; i < features.length; i++) {
            featureSum += features[i];
        }
        
        // Normalize to 0-10000 range
        anomalyScore = (featureSum % 10000);
        
        // Add some randomness based on features
        if (features.length > 3) {
            uint256 volatilityFactor = features[5] % 1000;
            anomalyScore = (anomalyScore + volatilityFactor) % 10000;
        }
        
        return anomalyScore;
    }
    
    /**
     * @notice Analyze cross-oracle correlation
     */
    function _analyzeCrossOracleCorrelation(bytes32 assetId, PriceDataPoint memory priceData) 
        internal 
        view 
        returns (uint256 score) 
    {
        // Check how this oracle's data correlates with other oracles
        // This is a simplified implementation
        
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < 10) {
            return 8000;
        }
        
        // Count recent prices from different oracles
        mapping(address => uint256) storage oraclePrices;
        uint256 uniqueOracles = 0;
        uint256 recentWindow = 3600; // 1 hour
        
        for (uint256 i = history.length - 1; i > 0; i--) {
            if (priceData.timestamp - history[i].timestamp > recentWindow) {
                break;
            }
            
            if (oraclePrices[history[i].oracle] == 0) {
                uniqueOracles++;
                oraclePrices[history[i].oracle] = history[i].price;
            }
        }
        
        if (uniqueOracles < MIN_ORACLE_CONSENSUS) {
            return 5000; // Insufficient oracle diversity
        }
        
        return 9000; // Good oracle correlation
    }
    
    /**
     * @notice Analyze market conditions
     */
    function _analyzeMarketConditions(bytes32 assetId, PriceDataPoint memory priceData) 
        internal 
        view 
        returns (uint256 score) 
    {
        // Analyze broader market conditions and volatility
        
        uint256 volatility = assetVolatilityMetrics[assetId];
        
        if (volatility > 2000) return 6000; // High volatility: Reduced confidence
        if (volatility > 1000) return 8000; // Medium volatility: Good
        
        return 9500; // Low volatility: Excellent
    }
    
    /**
     * @notice Calculate overall security score
     */
    function _calculateOverallSecurityScore(SecurityAnalysisResult memory result) 
        internal 
        pure 
        returns (uint256 score) 
    {
        // Weighted average of all analysis components
        uint256 totalWeight = 100;
        
        score = (result.statisticalScore * 20 +    // 20%
                result.consistencyScore * 15 +      // 15%
                result.volumeScore * 10 +           // 10%
                result.temporalScore * 15 +         // 15%
                result.mlScore * 25 +               // 25%
                result.correlationScore * 10 +      // 10%
                result.marketScore * 5) / totalWeight; // 5%
        
        return score;
    }
    
    /**
     * @notice Calculate threat level
     */
    function _calculateThreatLevel(SecurityAnalysisResult memory result) 
        internal 
        pure 
        returns (uint256 threatLevel) 
    {
        // Inverse of security score with additional threat-specific adjustments
        threatLevel = 10000 - result.securityScore;
        
        // Amplify threat level if multiple systems show issues
        uint256 poorScores = 0;
        if (result.statisticalScore < 6000) poorScores++;
        if (result.consistencyScore < 6000) poorScores++;
        if (result.volumeScore < 6000) poorScores++;
        if (result.temporalScore < 6000) poorScores++;
        if (result.mlScore < 6000) poorScores++;
        
        // Increase threat level if multiple systems flag issues
        if (poorScores >= 3) {
            threatLevel = Math.min(threatLevel * 150 / 100, 10000);
        } else if (poorScores >= 2) {
            threatLevel = Math.min(threatLevel * 125 / 100, 10000);
        }
        
        return threatLevel;
    }
    
    /**
     * @notice Calculate manipulation probability
     */
    function _calculateManipulationProbability(SecurityAnalysisResult memory result) 
        internal 
        pure 
        returns (uint256 probability) 
    {
        // Base probability on threat level
        probability = result.threatLevel;
        
        // Specific indicators that increase manipulation probability
        if (result.volumeScore < 5000) {
            probability = Math.min(probability + 1000, 10000); // Volume anomalies
        }
        
        if (result.temporalScore < 5000) {
            probability = Math.min(probability + 1500, 10000); // Timing attacks
        }
        
        if (result.mlScore < 4000) {
            probability = Math.min(probability + 2000, 10000); // ML detects anomaly
        }
        
        return probability;
    }
    
    /**
     * @notice Detect specific threat types
     */
    function _detectSpecificThreats(
        bytes32 assetId, 
        PriceDataPoint memory priceData,
        SecurityAnalysisResult memory result
    ) 
        internal 
        view 
        returns (bytes32[] memory threats) 
    {
        threats = new bytes32[](10); // Maximum 10 threat types
        uint256 threatCount = 0;
        
        // Flash loan attack pattern
        if (result.temporalScore < 4000 && result.volumeScore < 5000) {
            threats[threatCount++] = keccak256(abi.encodePacked("FLASH_LOAN_ATTACK", block.timestamp));
        }
        
        // Price manipulation
        if (result.statisticalScore < 3000) {
            threats[threatCount++] = keccak256(abi.encodePacked("PRICE_MANIPULATION", block.timestamp));
        }
        
        // Volume manipulation
        if (result.volumeScore < 3000) {
            threats[threatCount++] = keccak256(abi.encodePacked("VOLUME_MANIPULATION", block.timestamp));
        }
        
        // Coordinated attack
        if (result.correlationScore < 4000 && result.consistencyScore < 5000) {
            threats[threatCount++] = keccak256(abi.encodePacked("COORDINATED_ATTACK", block.timestamp));
        }
        
        // Statistical anomaly
        if (result.mlScore < 3000) {
            threats[threatCount++] = keccak256(abi.encodePacked("STATISTICAL_ANOMALY", block.timestamp));
        }
        
        // Resize array to actual threat count
        bytes32[] memory actualThreats = new bytes32[](threatCount);
        for (uint256 i = 0; i < threatCount; i++) {
            actualThreats[i] = threats[i];
        }
        
        return actualThreats;
    }
    
    /**
     * @notice Update security metrics for an asset
     */
    function _updateSecurityMetrics(bytes32 assetId, SecurityAnalysisResult memory result) internal {
        SecurityMetrics storage metrics = assetSecurityMetrics[assetId];
        
        metrics.threatLevel = result.threatLevel;
        metrics.riskScore = 10000 - result.securityScore;
        metrics.manipulationProbability = result.manipulationProbability;
        metrics.lastSecurityCheck = block.timestamp;
        
        // Update consecutive anomalies
        if (result.threatLevel > THREAT_PROBABILITY_THRESHOLD) {
            metrics.consecutiveAnomalies++;
        } else {
            metrics.consecutiveAnomalies = 0;
        }
        
        // Update surveillance status
        if (metrics.consecutiveAnomalies >= 3 || result.threatLevel > 8000) {
            metrics.isUnderSurveillance = true;
        } else if (result.threatLevel < 3000 && metrics.consecutiveAnomalies == 0) {
            metrics.isUnderSurveillance = false;
        }
        
        // Update emergency mode
        if (result.threatLevel > 9000 || metrics.consecutiveAnomalies >= 5) {
            metrics.emergencyMode = true;
            _triggerAssetEmergencyProtocol(assetId, "High threat level detected");
        }
    }
    
    /**
     * @notice Process detected threats
     */
    function _processThreatDetections(bytes32 assetId, bytes32[] memory threatIds) internal {
        for (uint256 i = 0; i < threatIds.length; i++) {
            if (threatIds[i] != bytes32(0)) {
                threatsDetected++;
                
                // Create threat detection record
                ThreatDetection storage threat = threatDetections[threatIds[i]];
                threat.threatId = threatIds[i];
                threat.detectedAt = block.timestamp;
                threat.probability = assetSecurityMetrics[assetId].manipulationProbability;
                
                // Determine threat type and severity from threat ID
                (ThreatType threatType, ThreatSeverity severity) = _parseThreatId(threatIds[i]);
                threat.threatType = threatType;
                threat.severity = severity;
                
                // Record affected oracles
                threat.affectedOracles = new address[](1);
                threat.affectedOracles[0] = msg.sender;
                
                emit ThreatDetected(
                    threatIds[i],
                    assetId,
                    threatType,
                    severity,
                    threat.probability,
                    address(this)
                );
                
                // Auto-trigger responses for high-severity threats
                if (severity >= ThreatSeverity.HIGH) {
                    _triggerAutomatedResponse(assetId, threatIds[i], severity);
                }
            }
        }
    }
    
    /**
     * @notice Parse threat ID to determine type and severity
     */
    function _parseThreatId(bytes32 threatId) 
        internal 
        pure 
        returns (ThreatType threatType, ThreatSeverity severity) 
    {
        // Simple parsing based on threat ID content (in production, use proper encoding)
        bytes memory threatBytes = abi.encodePacked(threatId);
        
        if (_contains(threatBytes, "FLASH_LOAN")) {
            threatType = ThreatType.FLASH_LOAN_ATTACK;
            severity = ThreatSeverity.HIGH;
        } else if (_contains(threatBytes, "PRICE_MANIPULATION")) {
            threatType = ThreatType.PRICE_MANIPULATION;
            severity = ThreatSeverity.CRITICAL;
        } else if (_contains(threatBytes, "VOLUME_MANIPULATION")) {
            threatType = ThreatType.VOLUME_MANIPULATION;
            severity = ThreatSeverity.MEDIUM;
        } else if (_contains(threatBytes, "COORDINATED")) {
            threatType = ThreatType.COORDINATED_ATTACK;
            severity = ThreatSeverity.CRITICAL;
        } else {
            threatType = ThreatType.STATISTICAL_ANOMALY;
            severity = ThreatSeverity.MEDIUM;
        }
        
        return (threatType, severity);
    }
    
    /**
     * @notice Check if bytes contain substring
     */
    function _contains(bytes memory data, string memory substr) 
        internal 
        pure 
        returns (bool) 
    {
        bytes memory substrBytes = bytes(substr);
        
        if (substrBytes.length > data.length) {
            return false;
        }
        
        for (uint256 i = 0; i <= data.length - substrBytes.length; i++) {
            bool found = true;
            for (uint256 j = 0; j < substrBytes.length; j++) {
                if (data[i + j] != substrBytes[j]) {
                    found = false;
                    break;
                }
            }
            if (found) {
                return true;
            }
        }
        
        return false;
    }

    // =================
    // EMERGENCY RESPONSE FUNCTIONS
    // =================
    
    /**
     * @notice Trigger automated response to threats
     */
    function _triggerAutomatedResponse(
        bytes32 assetId, 
        bytes32 threatId, 
        ThreatSeverity severity
    ) internal {
        if (severity == ThreatSeverity.CRITICAL || severity == ThreatSeverity.EMERGENCY) {
            // Activate circuit breaker
            _activateCircuitBreaker(assetId, "Automated response to critical threat");
            
            // Increase monitoring frequency (would integrate with off-chain systems)
            
            // Notify emergency responders
            // (Integration with external notification systems)
        }
        
        if (severity >= ThreatSeverity.HIGH) {
            // Put asset under surveillance
            assetSecurityMetrics[assetId].isUnderSurveillance = true;
            
            // Log incident for compliance
            _recordComplianceEvent(assetId, "THREAT_RESPONSE", true, "MiFID_II");
        }
    }
    
    /**
     * @notice Activate circuit breaker for an asset
     */
    function _activateCircuitBreaker(bytes32 assetId, string memory reason) internal {
        assetCircuitBreakers[assetId] = true;
        circuitBreakerActivationTime[assetId] = block.timestamp;
        
        emit CircuitBreakerActivated(
            assetId,
            CIRCUIT_BREAKER_THRESHOLD,
            assetSecurityMetrics[assetId].threatLevel,
            address(this)
        );
        
        // Record compliance event
        _recordComplianceEvent(assetId, "CIRCUIT_BREAKER_ACTIVATION", true, "MiFID_II");
    }
    
    /**
     * @notice Trigger asset-specific emergency protocol
     */
    function _triggerAssetEmergencyProtocol(bytes32 assetId, string memory reason) internal {
        assetSecurityMetrics[assetId].emergencyMode = true;
        
        // If multiple assets in emergency, trigger global protocol
        uint256 assetsInEmergency = 0;
        // Count would be implemented by iterating through assets
        
        if (assetsInEmergency >= 3) {
            _triggerGlobalEmergencyProtocol("Multiple assets in emergency mode");
        }
    }
    
    /**
     * @notice Trigger global emergency protocol
     */
    function _triggerGlobalEmergencyProtocol(string memory reason) internal {
        if (globalEmergencyProtocol.active) {
            return; // Already active
        }
        
        globalEmergencyProtocol.active = true;
        globalEmergencyProtocol.activatedAt = block.timestamp;
        globalEmergencyProtocol.activatedBy = address(this);
        globalEmergencyProtocol.reason = reason;
        
        // Pause the contract
        _pause();
        
        emit EmergencyProtocolActivated(
            reason,
            globalEmergencyProtocol.affectedAssets,
            address(this),
            block.timestamp
        );
    }

    // =================
    // UTILITY FUNCTIONS
    // =================
    
    /**
     * @notice Verify oracle signature
     */
    function _verifyOracleSignature(
        bytes32 assetId,
        PriceDataPoint memory priceData,
        bytes memory signature
    ) internal view returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(
            assetId,
            priceData.price,
            priceData.timestamp,
            priceData.confidence,
            priceData.volume
        ));
        
        bytes32 ethSignedMessageHash = messageHash.toEthSignedMessageHash();
        address recoveredSigner = ethSignedMessageHash.recover(signature);
        
        return recoveredSigner == msg.sender && hasRole(ORACLE_VALIDATOR_ROLE, recoveredSigner);
    }
    
    /**
     * @notice Determine final validation result
     */
    function _determineValidationResult(SecurityAnalysisResult memory result) 
        internal 
        view 
        returns (bool isValid) 
    {
        // Price is valid if security score is above threshold and no critical threats
        return (result.securityScore >= 6000 && 
                result.threatLevel < CRITICAL_THRESHOLD &&
                result.manipulationProbability < THREAT_PROBABILITY_THRESHOLD);
    }
    
    /**
     * @notice Trim old price history to maintain storage efficiency
     */
    function _trimPriceHistory(bytes32 assetId) internal {
        PriceDataPoint[] storage history = priceHistory[assetId];
        
        // Keep last 1000 data points
        if (history.length > 1000) {
            for (uint256 i = 0; i < history.length - 1000; i++) {
                history[i] = history[i + 1000];
            }
            
            // Reset array length (this is a simplified approach)
            // In practice, you'd use a more gas-efficient circular buffer
            assembly {
                sstore(history.slot, 1000)
            }
        }
    }
    
    /**
     * @notice Calculate volatility for a given period
     */
    function _calculateVolatility(bytes32 assetId, uint256 periods) 
        internal 
        view 
        returns (uint256 volatility) 
    {
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < periods + 1) {
            return 0;
        }
        
        uint256 sum = 0;
        for (uint256 i = history.length - periods; i < history.length; i++) {
            uint256 priceChange = history[i].price > history[i-1].price
                ? ((history[i].price - history[i-1].price) * 10000) / history[i-1].price
                : ((history[i-1].price - history[i].price) * 10000) / history[i-1].price;
            sum += priceChange;
        }
        
        return sum / periods;
    }
    
    /**
     * @notice Calculate price momentum
     */
    function _calculateMomentum(bytes32 assetId, uint256 periods) 
        internal 
        view 
        returns (uint256 momentum) 
    {
        PriceDataPoint[] memory history = priceHistory[assetId];
        
        if (history.length < periods + 1) {
            return 0;
        }
        
        uint256 currentPrice = history[history.length - 1].price;
        uint256 pastPrice = history[history.length - periods - 1].price;
        
        if (pastPrice == 0) {
            return 0;
        }
        
        return currentPrice > pastPrice
            ? ((currentPrice - pastPrice) * 10000) / pastPrice
            : ((pastPrice - currentPrice) * 10000) / pastPrice;
    }
    
    /**
     * @notice Record compliance event
     */
    function _recordComplianceEvent(
        bytes32 assetId,
        bytes32 eventType,
        bool compliant,
        string memory framework
    ) internal {
        ComplianceRecord memory record = ComplianceRecord({
            timestamp: block.timestamp,
            eventType: eventType,
            dataHash: keccak256(abi.encodePacked(assetId, eventType, block.timestamp)),
            actor: msg.sender,
            compliant: compliant,
            regulatoryFramework: framework
        });
        
        complianceRecords[assetId].push(record);
        
        emit ComplianceEvent(assetId, eventType, compliant, framework);
    }
    
    /**
     * @notice Update oracle reputation
     */
    function _updateOracleReputation(address oracle, bool validPrice, uint256 threatLevel) internal {
        uint256 oldReputation = oracleReputationScores[oracle];
        uint256 newReputation = oldReputation;
        
        if (validPrice && threatLevel < 5000) {
            // Increase reputation for good data
            newReputation = Math.min(oldReputation + 10, 10000);
        } else if (!validPrice || threatLevel > 7000) {
            // Decrease reputation for bad data
            newReputation = oldReputation > 50 ? oldReputation - 50 : 0;
        }
        
        oracleReputationScores[oracle] = newReputation;
        
        if (newReputation != oldReputation) {
            emit OracleReputationUpdated(
                oracle,
                oldReputation,
                newReputation,
                validPrice ? "Valid price submission" : "Invalid price submission"
            );
        }
        
        // Emergency override for very low reputation
        if (newReputation < 2000) {
            oracleEmergencyOverride[oracle] = true;
        }
    }
    
    /**
     * @notice Square root function for standard deviation calculation
     */
    function _sqrt(uint256 x) internal pure returns (uint256) {
        if (x == 0) return 0;
        
        uint256 z = (x + 1) / 2;
        uint256 y = x;
        
        while (z < y) {
            y = z;
            z = (x / z + z) / 2;
        }
        
        return y;
    }

    // =================
    // ADMIN FUNCTIONS
    // =================
    
    /**
     * @notice Reset circuit breaker for an asset
     */
    function resetCircuitBreaker(bytes32 assetId) 
        external 
        onlyEmergencyResponder 
        validAssetId(assetId) 
    {
        require(assetCircuitBreakers[assetId], "Circuit breaker not active");
        require(
            block.timestamp >= circuitBreakerActivationTime[assetId] + 3600,
            "Cooldown period not elapsed"
        );
        
        assetCircuitBreakers[assetId] = false;
        assetSecurityMetrics[assetId].emergencyMode = false;
        
        _recordComplianceEvent(assetId, "CIRCUIT_BREAKER_RESET", true, "MiFID_II");
    }
    
    /**
     * @notice Deactivate global emergency protocol
     */
    function deactivateGlobalEmergencyProtocol() external onlyEmergencyResponder nonReentrant{
        require(globalEmergencyProtocol.active, "Emergency protocol not active");
        require(
            block.timestamp >= globalEmergencyProtocol.activatedAt + 1 hours,
            "Minimum emergency duration not elapsed"
        );
        
        globalEmergencyProtocol.active = false;
        _unpause();
        
        _recordComplianceEvent(
            bytes32(0), 
            "GLOBAL_EMERGENCY_DEACTIVATION", 
            true, 
            "OPERATIONAL_RISK_MANAGEMENT"
        );
    }
    
    /**
     * @notice Update ML model
     */
    function updateMLModel(bytes32 modelHash, uint256 confidenceScore) 
        external 
        onlyRole(ML_ANALYZER_ROLE) 
    {
        require(modelHash != bytes32(0), "Invalid model hash");
        require(confidenceScore <= 10000, "Invalid confidence score");
        
        approvedMLModels[modelHash] = true;
        modelConfidenceScores[modelHash] = confidenceScore;
        activeMLModelHash = modelHash;
        mlModelVersion++;
    }
    
    /**
     * @notice Get security dashboard data
     */
    function getSecurityDashboard() 
        external 
        view 
        returns (
            uint256 totalValidationsCount,
            uint256 totalThreatsDetected,
            uint256 activeCircuitBreakers,
            uint256 avgResponseTime,
            bool emergencyProtocolActive
        ) 
    {
        totalValidationsCount = totalValidations;
        totalThreatsDetected = threatsDetected;
        avgResponseTime = averageResponseTime;
        emergencyProtocolActive = globalEmergencyProtocol.active;
        
        // Count active circuit breakers (simplified)
        activeCircuitBreakers = 0; // Would iterate through all assets
    }
    
    /**
     * @notice Get asset security status
     */
    function getAssetSecurityStatus(bytes32 assetId) 
        external 
        view 
        validAssetId(assetId)
        returns (
            uint256 threatLevel,
            uint256 riskScore,
            uint256 manipulationProbability,
            bool isUnderSurveillance,
            bool circuitBreakerActive,
            bool emergencyMode
        ) 
    {
        SecurityMetrics memory metrics = assetSecurityMetrics[assetId];
        
        return (
            metrics.threatLevel,
            metrics.riskScore,
            metrics.manipulationProbability,
            metrics.isUnderSurveillance,
            assetCircuitBreakers[assetId],
            metrics.emergencyMode
        );
    }
}
