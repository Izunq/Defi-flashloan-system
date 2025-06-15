// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./SecureMultiOracle.sol";
import "./OracleSecurityWrapper.sol";

/**
 * @title OracleManipulationMonitor
 * @notice Real-time monitoring system for oracle manipulation detection
 * @dev Provides continuous surveillance and automated response mechanisms
 */
contract OracleManipulationMonitor is AccessControl, ReentrancyGuard {
    
    // =================
    // CONSTANTS & ROLES
    // =================
    
    bytes32 public constant MONITOR_ADMIN_ROLE = keccak256("MONITOR_ADMIN_ROLE");
    bytes32 public constant ALERT_MANAGER_ROLE = keccak256("ALERT_MANAGER_ROLE");
    bytes32 public constant RESPONSE_TEAM_ROLE = keccak256("RESPONSE_TEAM_ROLE");
    
    // Monitoring intervals
    uint256 public constant CRITICAL_MONITORING_INTERVAL = 30 seconds;
    uint256 public constant STANDARD_MONITORING_INTERVAL = 5 minutes;
    uint256 public constant DEEP_ANALYSIS_INTERVAL = 1 hours;
    
    // Alert thresholds
    uint256 public constant PRICE_SPIKE_THRESHOLD = 1000; // 10% in basis points
    uint256 public constant VOLUME_ANOMALY_THRESHOLD = 300; // 3x normal volume
    uint256 public constant CONSENSUS_FAILURE_THRESHOLD = 2; // 2 oracle failures
    
    // =================
    // STATE VARIABLES
    // =================
    
    SecureMultiOracle public immutable primaryOracle;
    OracleSecurityWrapper public immutable securityWrapper;
    
    // Monitoring state
    mapping(bytes32 => MonitoringData) public assetMonitoring;
    mapping(bytes32 => AlertHistory[]) public alertHistories;
    mapping(address => ResponseTeamMember) public responseTeam;
    
    // Global monitoring state
    uint256 public lastGlobalCheck;
    uint256 public totalAlertsGenerated;
    uint256 public criticalAlertsActive;
    bool public emergencyProtocolActive;
    
    // Alert queues
    bytes32[] public pendingCriticalAlerts;
    bytes32[] public pendingHighAlerts;
    bytes32[] public pendingMediumAlerts;
    
    // Response metrics
    mapping(bytes32 => ResponseMetrics) public responseMetrics;
    uint256 public averageResponseTime;
    uint256 public successfulResponses;

    // =================
    // STRUCTS & ENUMS
    // =================
    
    struct MonitoringData {
        uint256 lastPrice;
        uint256 lastVolume;
        uint256 lastUpdate;
        uint256 priceMovingAverage;
        uint256 volumeMovingAverage;
        uint256 alertCount;
        MonitoringStatus status;
        bool isHighRisk;
        uint256 consecutiveAnomalies;
    }
    
    struct AlertHistory {
        bytes32 alertId;
        AlertType alertType;
        AlertSeverity severity;
        uint256 timestamp;
        uint256 detectedPrice;
        uint256 expectedPrice;
        string description;
        address detector;
        bool acknowledged;
        bool resolved;
        uint256 resolutionTime;
        address resolver;
    }
    
    struct ResponseTeamMember {
        string name;
        string role;
        bool isActive;
        uint256 alertsHandled;
        uint256 averageResponseTime;
        uint256 lastActivity;
        string[] specializations;
    }
    
    struct ResponseMetrics {
        uint256 detectionTime;
        uint256 acknowledgeTime;
        uint256 resolutionTime;
        bool automaticResponse;
        ResponseAction[] actionsTaken;
    }
    
    struct ResponseAction {
        string actionType;
        uint256 timestamp;
        address executor;
        bool successful;
        string details;
    }
    
    enum MonitoringStatus { 
        NORMAL, 
        ELEVATED, 
        HIGH_RISK, 
        CRITICAL, 
        EMERGENCY 
    }
    
    enum AlertType {
        PRICE_MANIPULATION,
        VOLUME_ANOMALY,
        ORACLE_FAILURE,
        CONSENSUS_BREAKDOWN,
        EXTERNAL_ATTACK,
        SYSTEM_MALFUNCTION
    }
    
    enum AlertSeverity { LOW, MEDIUM, HIGH, CRITICAL }

    // =================
    // EVENTS
    // =================
    
    event ManipulationAlert(
        bytes32 indexed alertId,
        bytes32 indexed assetId,
        AlertType alertType,
        AlertSeverity severity,
        uint256 timestamp,
        string description
    );
    
    event AlertAcknowledged(
        bytes32 indexed alertId,
        address indexed responder,
        uint256 responseTime
    );
    
    event AlertResolved(
        bytes32 indexed alertId,
        address indexed resolver,
        uint256 resolutionTime,
        string resolution
    );
    
    event EmergencyProtocolActivated(
        string reason,
        address activatedBy,
        uint256 timestamp
    );
    
    event AutomatedResponseExecuted(
        bytes32 indexed alertId,
        string responseType,
        bool successful
    );

    // =================
    // CONSTRUCTOR
    // =================
    
    constructor(
        address _primaryOracle,
        address _securityWrapper,
        address _admin
    ) {
        require(_primaryOracle != address(0), "Invalid primary oracle");
        require(_securityWrapper != address(0), "Invalid security wrapper");
        require(_admin != address(0), "Invalid admin");
        
        primaryOracle = SecureMultiOracle(_primaryOracle);
        securityWrapper = OracleSecurityWrapper(_securityWrapper);
        
        // Setup roles
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(MONITOR_ADMIN_ROLE, _admin);
        _grantRole(ALERT_MANAGER_ROLE, _admin);
        _grantRole(RESPONSE_TEAM_ROLE, _admin);
        
        lastGlobalCheck = block.timestamp;
    }

    // =================
    // MONITORING FUNCTIONS
    // =================
    
    /**
     * @notice Perform comprehensive monitoring check for an asset
     * @param assetId Asset to monitor
     */
    function performMonitoringCheck(bytes32 assetId) external nonReentrant {
        require(
            block.timestamp >= assetMonitoring[assetId].lastUpdate + CRITICAL_MONITORING_INTERVAL,
            "Monitoring interval not elapsed"
        );
        
        // Get current market data
        (uint256 currentPrice, bool priceValid) = primaryOracle.getSafePrice(assetId, 1 hours);
        require(priceValid, "Invalid price data for monitoring");
        
        // Get security status
        (,bool circuitBreakerActive, bool anomalyDetected,) = 
            securityWrapper.getAssetSecurityStatus(assetId);
        
        MonitoringData storage monitoring = assetMonitoring[assetId];
        
        // Detect price manipulation
        bool priceManipulation = _detectPriceManipulation(assetId, currentPrice);
        if (priceManipulation) {
            _generateAlert(
                assetId,
                AlertType.PRICE_MANIPULATION,
                AlertSeverity.HIGH,
                "Significant price deviation detected"
            );
        }
        
        // Check for oracle consensus issues
        (uint256 activeOracles,,,) = primaryOracle.getSystemHealth();
        if (activeOracles < 3) {
            _generateAlert(
                assetId,
                AlertType.CONSENSUS_BREAKDOWN,
                AlertSeverity.CRITICAL,
                "Insufficient oracle consensus"
            );
        }
        
        // Update monitoring data
        _updateMonitoringData(assetId, currentPrice, 0); // Volume would come from external source
        
        // Determine risk level
        _updateRiskLevel(assetId);
        
        // Execute automated responses if needed
        if (monitoring.status >= MonitoringStatus.CRITICAL) {
            _executeAutomatedResponse(assetId);
        }
    }
    
    /**
     * @notice Perform system-wide monitoring
     */
    function performSystemMonitoring() external onlyRole(MONITOR_ADMIN_ROLE) {
        require(
            block.timestamp >= lastGlobalCheck + STANDARD_MONITORING_INTERVAL,
            "System monitoring interval not elapsed"
        );
        
        lastGlobalCheck = block.timestamp;
        
        // Check oracle system health
        (uint256 activeOracles, uint256 totalWeight, bool circuitBreakerActive, bool systemPaused) = 
            primaryOracle.getSystemHealth();
        
        if (activeOracles < 3) {
            _activateEmergencyProtocol("Critical oracle consensus failure");
        }
        
        if (circuitBreakerActive || systemPaused) {
            _generateSystemAlert(
                AlertType.SYSTEM_MALFUNCTION,
                AlertSeverity.HIGH,
                "Oracle system protection activated"
            );
        }
        
        // Check security wrapper health
        (bool securityActive,, uint256 lastSecurityCheck, bool securityPaused) = 
            securityWrapper.getSystemSecurityHealth();
        
        if (securityActive || securityPaused) {
            _generateSystemAlert(
                AlertType.EXTERNAL_ATTACK,
                AlertSeverity.CRITICAL,
                "Security system emergency mode active"
            );
        }
        
        // Process pending alerts
        _processPendingAlerts();
        
        // Update system metrics
        _updateSystemMetrics();
    }

    // =================
    // DETECTION FUNCTIONS
    // =================
    
    /**
     * @notice Detect price manipulation patterns
     */
    function _detectPriceManipulation(bytes32 assetId, uint256 currentPrice) 
        internal 
        view 
        returns (bool) 
    {
        MonitoringData memory monitoring = assetMonitoring[assetId];
        
        if (monitoring.lastPrice == 0) return false;
        
        // Calculate price change percentage
        uint256 priceChange = currentPrice > monitoring.lastPrice
            ? ((currentPrice - monitoring.lastPrice) * 10000) / monitoring.lastPrice
            : ((monitoring.lastPrice - currentPrice) * 10000) / monitoring.lastPrice;
        
        // Check against threshold
        if (priceChange > PRICE_SPIKE_THRESHOLD) {
            return true;
        }
        
        // Check against moving average
        if (monitoring.priceMovingAverage > 0) {
            uint256 avgDeviation = currentPrice > monitoring.priceMovingAverage
                ? ((currentPrice - monitoring.priceMovingAverage) * 10000) / monitoring.priceMovingAverage
                : ((monitoring.priceMovingAverage - currentPrice) * 10000) / monitoring.priceMovingAverage;
            
            if (avgDeviation > PRICE_SPIKE_THRESHOLD * 2) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * @notice Generate monitoring alert
     */
    function _generateAlert(
        bytes32 assetId,
        AlertType alertType,
        AlertSeverity severity,
        string memory description
    ) internal {
        bytes32 alertId = keccak256(
            abi.encodePacked(
                assetId,
                alertType,
                block.timestamp,
                totalAlertsGenerated
            )
        );
        
        AlertHistory memory alert = AlertHistory({
            alertId: alertId,
            alertType: alertType,
            severity: severity,
            timestamp: block.timestamp,
            detectedPrice: assetMonitoring[assetId].lastPrice,
            expectedPrice: assetMonitoring[assetId].priceMovingAverage,
            description: description,
            detector: address(this),
            acknowledged: false,
            resolved: false,
            resolutionTime: 0,
            resolver: address(0)
        });
        
        alertHistories[assetId].push(alert);
        
        // Add to appropriate queue
        if (severity == AlertSeverity.CRITICAL) {
            pendingCriticalAlerts.push(alertId);
            criticalAlertsActive++;
        } else if (severity == AlertSeverity.HIGH) {
            pendingHighAlerts.push(alertId);
        } else if (severity == AlertSeverity.MEDIUM) {
            pendingMediumAlerts.push(alertId);
        }
        
        totalAlertsGenerated++;
        assetMonitoring[assetId].alertCount++;
        
        emit ManipulationAlert(
            alertId,
            assetId,
            alertType,
            severity,
            block.timestamp,
            description
        );
        
        // Auto-escalate critical alerts
        if (severity == AlertSeverity.CRITICAL) {
            _escalateCriticalAlert(alertId, assetId);
        }
    }
    
    /**
     * @notice Generate system-wide alert
     */
    function _generateSystemAlert(
        AlertType alertType,
        AlertSeverity severity,
        string memory description
    ) internal {
        bytes32 systemAssetId = keccak256("SYSTEM_WIDE");
        _generateAlert(systemAssetId, alertType, severity, description);
    }

    // =================
    // RESPONSE FUNCTIONS
    // =================
    
    /**
     * @notice Execute automated response to critical situations
     */
    function _executeAutomatedResponse(bytes32 assetId) internal {
        MonitoringData storage monitoring = assetMonitoring[assetId];
        
        // Create response entry
        bytes32 responseId = keccak256(abi.encodePacked(assetId, block.timestamp));
        
        ResponseAction[] storage actions = responseMetrics[responseId].actionsTaken;
        
        // Automatic circuit breaker activation
        try securityWrapper.resetCircuitBreaker(assetId) {
            actions.push(ResponseAction({
                actionType: "CIRCUIT_BREAKER_RESET",
                timestamp: block.timestamp,
                executor: address(this),
                successful: true,
                details: "Automated circuit breaker reset"
            }));
            
            emit AutomatedResponseExecuted(responseId, "CIRCUIT_BREAKER_RESET", true);
        } catch {
            actions.push(ResponseAction({
                actionType: "CIRCUIT_BREAKER_RESET",
                timestamp: block.timestamp,
                executor: address(this),
                successful: false,
                details: "Failed to reset circuit breaker"
            }));
        }
        
        // Increase monitoring frequency
        monitoring.status = MonitoringStatus.EMERGENCY;
        
        // Notify response team
        _notifyResponseTeam(assetId, "AUTOMATED_RESPONSE_TRIGGERED");
    }
    
    /**
     * @notice Escalate critical alert
     */
    function _escalateCriticalAlert(bytes32 alertId, bytes32 assetId) internal {
        // If multiple critical alerts, activate emergency protocol
        if (criticalAlertsActive >= 3) {
            _activateEmergencyProtocol("Multiple critical alerts detected");
        }
        
        // Immediate notification to all response team members
        _notifyResponseTeam(assetId, "CRITICAL_ALERT_ESCALATION");
    }
    
    /**
     * @notice Activate emergency protocol
     */
    function _activateEmergencyProtocol(string memory reason) internal {
        if (emergencyProtocolActive) return;
        
        emergencyProtocolActive = true;
        
        emit EmergencyProtocolActivated(reason, address(this), block.timestamp);
        
        // Emergency actions would be implemented here
        // e.g., pause all trading, activate all circuit breakers, etc.
    }
    
    /**
     * @notice Notify response team
     */
    function _notifyResponseTeam(bytes32 assetId, string memory alertType) internal {
        // This would integrate with external notification systems
        // Implementation depends on specific notification requirements
    }

    // =================
    // UPDATE FUNCTIONS
    // =================
    
    /**
     * @notice Update monitoring data for an asset
     */
    function _updateMonitoringData(bytes32 assetId, uint256 currentPrice, uint256 currentVolume) internal {
        MonitoringData storage monitoring = assetMonitoring[assetId];
        
        // Update moving averages (simple exponential moving average)
        if (monitoring.priceMovingAverage == 0) {
            monitoring.priceMovingAverage = currentPrice;
        } else {
            // Alpha = 0.1 for smoothing
            monitoring.priceMovingAverage = (monitoring.priceMovingAverage * 9 + currentPrice) / 10;
        }
        
        if (monitoring.volumeMovingAverage == 0) {
            monitoring.volumeMovingAverage = currentVolume;
        } else {
            monitoring.volumeMovingAverage = (monitoring.volumeMovingAverage * 9 + currentVolume) / 10;
        }
        
        monitoring.lastPrice = currentPrice;
        monitoring.lastVolume = currentVolume;
        monitoring.lastUpdate = block.timestamp;
    }
    
    /**
     * @notice Update risk level for an asset
     */
    function _updateRiskLevel(bytes32 assetId) internal {
        MonitoringData storage monitoring = assetMonitoring[assetId];
        
        uint256 riskScore = 0;
        
        // Factor in alert count
        riskScore += monitoring.alertCount * 10;
        
        // Factor in consecutive anomalies
        riskScore += monitoring.consecutiveAnomalies * 20;
        
        // Factor in time since last update
        if (block.timestamp - monitoring.lastUpdate > 1 hours) {
            riskScore += 30;
        }
        
        // Determine status based on risk score
        if (riskScore >= 100) {
            monitoring.status = MonitoringStatus.EMERGENCY;
        } else if (riskScore >= 70) {
            monitoring.status = MonitoringStatus.CRITICAL;
        } else if (riskScore >= 40) {
            monitoring.status = MonitoringStatus.HIGH_RISK;
        } else if (riskScore >= 20) {
            monitoring.status = MonitoringStatus.ELEVATED;
        } else {
            monitoring.status = MonitoringStatus.NORMAL;
        }
        
        monitoring.isHighRisk = riskScore >= 40;
    }
    
    /**
     * @notice Process pending alerts queue
     */
    function _processPendingAlerts() internal {
        // Process critical alerts first
        for (uint256 i = 0; i < pendingCriticalAlerts.length && i < 5; i++) {
            // Implementation would process alerts based on priority
        }
        
        // Clean up resolved alerts from queues
        _cleanupResolvedAlerts();
    }
    
    /**
     * @notice Update system-wide metrics
     */
    function _updateSystemMetrics() internal {
        // Calculate average response time
        if (successfulResponses > 0) {
            // Implementation would calculate from response history
        }
        
        // Update alert statistics
        // Implementation would maintain running statistics
    }
    
    /**
     * @notice Clean up resolved alerts from queues
     */
    function _cleanupResolvedAlerts() internal {
        // Remove resolved alerts from pending queues
        // Implementation would iterate through queues and remove resolved alerts
    }

    // =================
    // ADMIN FUNCTIONS
    // =================
    
    /**
     * @notice Acknowledge an alert
     */
    function acknowledgeAlert(bytes32 alertId, bytes32 assetId) 
        external 
        onlyRole(RESPONSE_TEAM_ROLE) 
    {
        AlertHistory[] storage alerts = alertHistories[assetId];
        
        for (uint256 i = 0; i < alerts.length; i++) {
            if (alerts[i].alertId == alertId && !alerts[i].acknowledged) {
                alerts[i].acknowledged = true;
                
                uint256 responseTime = block.timestamp - alerts[i].timestamp;
                
                emit AlertAcknowledged(alertId, msg.sender, responseTime);
                break;
            }
        }
    }
    
    /**
     * @notice Resolve an alert
     */
    function resolveAlert(bytes32 alertId, bytes32 assetId, string calldata resolution) 
        external 
        onlyRole(RESPONSE_TEAM_ROLE) 
    {
        AlertHistory[] storage alerts = alertHistories[assetId];
        
        for (uint256 i = 0; i < alerts.length; i++) {
            if (alerts[i].alertId == alertId && !alerts[i].resolved) {
                alerts[i].resolved = true;
                alerts[i].resolutionTime = block.timestamp;
                alerts[i].resolver = msg.sender;
                
                if (alerts[i].severity == AlertSeverity.CRITICAL) {
                    criticalAlertsActive--;
                }
                
                successfulResponses++;
                
                emit AlertResolved(alertId, msg.sender, block.timestamp, resolution);
                break;
            }
        }
    }
    
    /**
     * @notice Add response team member
     */
    function addResponseTeamMember(
        address member,
        string calldata name,
        string calldata role,
        string[] calldata specializations
    ) external onlyRole(MONITOR_ADMIN_ROLE) {
        responseTeam[member] = ResponseTeamMember({
            name: name,
            role: role,
            isActive: true,
            alertsHandled: 0,
            averageResponseTime: 0,
            lastActivity: block.timestamp,
            specializations: specializations
        });
        
        _grantRole(RESPONSE_TEAM_ROLE, member);
    }

    // =================
    // VIEW FUNCTIONS
    // =================
    
    /**
     * @notice Get monitoring status for an asset
     */
    function getMonitoringStatus(bytes32 assetId) 
        external 
        view 
        returns (MonitoringData memory) 
    {
        return assetMonitoring[assetId];
    }
    
    /**
     * @notice Get alert history for an asset
     */
    function getAlertHistory(bytes32 assetId) 
        external 
        view 
        returns (AlertHistory[] memory) 
    {
        return alertHistories[assetId];
    }
    
    /**
     * @notice Get system monitoring dashboard data
     */
    function getSystemDashboard() 
        external 
        view 
        returns (
            uint256 totalAlerts,
            uint256 criticalAlerts,
            uint256 avgResponseTime,
            bool emergencyActive,
            uint256 lastGlobalCheckTime
        ) 
    {
        return (
            totalAlertsGenerated,
            criticalAlertsActive,
            averageResponseTime,
            emergencyProtocolActive,
            lastGlobalCheck
        );
    }
}
