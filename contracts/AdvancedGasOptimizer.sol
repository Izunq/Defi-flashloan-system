// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "./interfaces/IGasOptimizer.sol";

/**
 * @title AdvancedGasOptimizer
 * @notice Advanced gas optimization and DoS protection system
 * @dev Provides comprehensive gas optimization, circuit breakers, and retry mechanisms
 */
contract AdvancedGasOptimizer is AccessControl, ReentrancyGuard, Pausable {
    
    bytes32 public constant GAS_ADMIN_ROLE = keccak256("GAS_ADMIN_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");
    
    // Enhanced gas limits
    struct GasLimits {
        uint256 maxGasPerOperation;     // Maximum gas per single operation
        uint256 maxGasPerBatch;         // Maximum gas per batch operation
        uint256 maxLoopIterations;      // Maximum loop iterations
        uint256 maxArrayLength;         // Maximum array length
        uint256 gasBuffer;              // Gas buffer for emergency operations
        uint256 lastUpdateTime;         // Last time limits were updated
        bool adaptive;                  // Whether limits adapt to network conditions
    }
    
    // Circuit breaker with enhanced features
    struct EnhancedCircuitBreaker {
        uint256 gasThreshold;           // Gas threshold for triggering
        uint256 timeWindowSeconds;      // Time window for failure tracking
        uint256 maxFailuresInWindow;    // Max failures allowed in time window
        uint256 currentFailures;        // Current failure count
        uint256 lastFailureTime;        // Last failure timestamp
        uint256 cooldownPeriod;         // Cooldown period after tripping
        uint256 tripTime;               // Time when circuit breaker tripped
        bool isTripped;                 // Whether circuit breaker is active
        bool autoReset;                 // Whether to auto-reset after cooldown
    }
    
    // Retry mechanism configuration
    struct RetryConfig {
        uint256 maxRetries;             // Maximum retry attempts
        uint256 baseDelaySeconds;       // Base delay between retries
        uint256 maxDelaySeconds;        // Maximum delay between retries
        uint256 backoffMultiplier;      // Exponential backoff multiplier (in basis points)
        bool exponentialBackoff;        // Whether to use exponential backoff
        bool jitterEnabled;             // Whether to add jitter to delays
    }
    
    // Operation tracking for optimization
    struct OperationMetrics {
        uint256 totalGasUsed;           // Total gas used by this operation type
        uint256 executionCount;         // Number of executions
        uint256 failureCount;           // Number of failures
        uint256 averageGasUsed;         // Average gas used per execution
        uint256 lastExecutionTime;      // Last execution timestamp
        uint256 optimalGasLimit;        // Calculated optimal gas limit
    }
    
    // External call optimization
    struct ExternalCallConfig {
        uint256 maxRetries;             // Max retries for external calls
        uint256 timeoutSeconds;         // Timeout for external calls
        uint256 gasLimitMultiplier;     // Gas limit multiplier (in basis points)
        bool batchingEnabled;           // Whether to batch external calls
        uint256 maxBatchSize;           // Maximum batch size
    }
    
    // Global gas limits per operation type
    mapping(bytes4 => GasLimits) public gasLimitsBySelector;
    
    // Circuit breakers per contract/operation
    mapping(address => mapping(bytes4 => EnhancedCircuitBreaker)) public circuitBreakers;
    
    // Retry configurations per operation
    mapping(bytes4 => RetryConfig) public retryConfigs;
    
    // Operation metrics for gas optimization
    mapping(bytes4 => OperationMetrics) public operationMetrics;
    
    // External call configurations
    mapping(address => ExternalCallConfig) public externalCallConfigs;
    
    // Rate limiting
    mapping(address => mapping(uint256 => uint256)) public operationsPerWindow;
    mapping(address => uint256) public lastWindowStart;
    
    // Default configurations
    GasLimits public defaultGasLimits;
    RetryConfig public defaultRetryConfig;
    ExternalCallConfig public defaultExternalCallConfig;
    
    // Global settings
    uint256 public constant RATE_LIMIT_WINDOW = 1 minutes;
    uint256 public constant MAX_OPERATIONS_PER_WINDOW = 50;
    uint256 public constant GAS_ESTIMATION_BUFFER = 2000; // 20% buffer in basis points
    uint256 public constant MIN_GAS_RESERVE = 100000;
    
    // Network condition tracking
    uint256 public networkCongestionLevel; // 0-10000 (0-100%)
    uint256 public lastNetworkUpdate;
    uint256 public networkUpdateInterval = 5 minutes;
    
    // Events
    event GasLimitsUpdated(bytes4 indexed selector, GasLimits limits);
    event CircuitBreakerTripped(address indexed contract_, bytes4 indexed selector, uint256 gasUsed);
    event CircuitBreakerReset(address indexed contract_, bytes4 indexed selector);
    event RetryConfigUpdated(bytes4 indexed selector, RetryConfig config);
    event OperationOptimized(bytes4 indexed selector, uint256 newOptimalGas);
    event ExternalCallConfigUpdated(address indexed target, ExternalCallConfig config);
    event NetworkCongestionUpdated(uint256 congestionLevel);
    event GasOptimizationPerformed(bytes4 indexed selector, uint256 gasSaved);
    
    constructor() {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(GAS_ADMIN_ROLE, msg.sender);
        _setupRole(EMERGENCY_ROLE, msg.sender);
        
        // Initialize default configurations
        _initializeDefaults();
    }
    
    /**
     * @dev Initialize default configurations
     */
    function _initializeDefaults() internal {
        defaultGasLimits = GasLimits({
            maxGasPerOperation: 5000000,     // 5M gas per operation
            maxGasPerBatch: 20000000,        // 20M gas per batch
            maxLoopIterations: 1000,         // Max 1000 iterations
            maxArrayLength: 500,             // Max 500 array elements
            gasBuffer: 200000,               // 200k gas buffer
            lastUpdateTime: block.timestamp,
            adaptive: true
        });
        
        defaultRetryConfig = RetryConfig({
            maxRetries: 3,
            baseDelaySeconds: 1,
            maxDelaySeconds: 60,
            backoffMultiplier: 2000,         // 2x multiplier (20%)
            exponentialBackoff: true,
            jitterEnabled: true
        });
        
        defaultExternalCallConfig = ExternalCallConfig({
            maxRetries: 3,
            timeoutSeconds: 30,
            gasLimitMultiplier: 12000,       // 1.2x multiplier (20% extra)
            batchingEnabled: true,
            maxBatchSize: 10
        });
    }
    
    /**
     * @dev Check gas limits for operation
     * @param selector Function selector
     * @param gasEstimate Estimated gas for operation
     * @param arrayLength Length of arrays being processed
     * @param loopIterations Number of loop iterations
     */
    modifier gasOptimized(
        bytes4 selector,
        uint256 gasEstimate,
        uint256 arrayLength,
        uint256 loopIterations
    ) {
        _checkGasLimits(selector, gasEstimate, arrayLength, loopIterations);
        uint256 gasStart = gasleft();
        _;
        _recordGasUsage(selector, gasStart - gasleft());
    }
    
    /**
     * @dev Check circuit breaker status
     */
    modifier circuitBreakerCheck(bytes4 selector) {
        require(
            !circuitBreakers[msg.sender][selector].isTripped,
            "Circuit breaker active"
        );
        _;
        _checkCircuitBreaker(selector);
    }
    
    /**
     * @dev Rate limiting check
     */
    modifier rateLimited() {
        _checkRateLimit();
        _;
    }
    
    /**
     * @dev Check gas limits before execution
     */
    function _checkGasLimits(
        bytes4 selector,
        uint256 gasEstimate,
        uint256 arrayLength,
        uint256 loopIterations
    ) internal view {
        GasLimits memory limits = gasLimitsBySelector[selector];
        
        // Use default limits if not set
        if (limits.maxGasPerOperation == 0) {
            limits = defaultGasLimits;
        }
        
        // Adaptive limits based on network congestion
        if (limits.adaptive) {
            limits = _adjustLimitsForCongestion(limits);
        }
        
        require(gasEstimate <= limits.maxGasPerOperation, "Gas estimate too high");
        require(arrayLength <= limits.maxArrayLength, "Array too large");
        require(loopIterations <= limits.maxLoopIterations, "Too many iterations");
        require(gasleft() >= gasEstimate + limits.gasBuffer, "Insufficient gas");
    }
    
    /**
     * @dev Adjust gas limits based on network congestion
     */
    function _adjustLimitsForCongestion(GasLimits memory limits) 
        internal 
        view 
        returns (GasLimits memory) 
    {
        // Reduce limits during high congestion
        if (networkCongestionLevel > 7500) { // 75%
            limits.maxGasPerOperation = (limits.maxGasPerOperation * 7) / 10; // 30% reduction
            limits.maxGasPerBatch = (limits.maxGasPerBatch * 7) / 10;
            limits.maxLoopIterations = (limits.maxLoopIterations * 8) / 10; // 20% reduction
        } else if (networkCongestionLevel > 5000) { // 50%
            limits.maxGasPerOperation = (limits.maxGasPerOperation * 85) / 100; // 15% reduction
            limits.maxGasPerBatch = (limits.maxGasPerBatch * 85) / 100;
            limits.maxLoopIterations = (limits.maxLoopIterations * 9) / 10; // 10% reduction
        }
        
        return limits;
    }
    
    /**
     * @dev Record gas usage for optimization
     */
    function _recordGasUsage(bytes4 selector, uint256 gasUsed) internal {
        OperationMetrics storage metrics = operationMetrics[selector];
        
        metrics.totalGasUsed += gasUsed;
        metrics.executionCount++;
        metrics.lastExecutionTime = block.timestamp;
        
        // Calculate new average
        metrics.averageGasUsed = metrics.totalGasUsed / metrics.executionCount;
        
        // Update optimal gas limit with buffer
        metrics.optimalGasLimit = (metrics.averageGasUsed * (10000 + GAS_ESTIMATION_BUFFER)) / 10000;
        
        // Emit optimization event if significant gas saving is achieved
        uint256 currentLimit = gasLimitsBySelector[selector].maxGasPerOperation;
        if (currentLimit > 0 && metrics.optimalGasLimit < currentLimit) {
            uint256 gasSaved = currentLimit - metrics.optimalGasLimit;
            if (gasSaved > currentLimit / 10) { // 10% improvement
                emit GasOptimizationPerformed(selector, gasSaved);
            }
        }
    }
    
    /**
     * @dev Check and update circuit breaker status
     */
    function _checkCircuitBreaker(bytes4 selector) internal {
        EnhancedCircuitBreaker storage cb = circuitBreakers[msg.sender][selector];
        
        // Auto-reset if cooldown period has passed
        if (cb.isTripped && cb.autoReset && 
            block.timestamp >= cb.tripTime + cb.cooldownPeriod) {
            cb.isTripped = false;
            cb.currentFailures = 0;
            emit CircuitBreakerReset(msg.sender, selector);
        }
    }
    
    /**
     * @dev Check rate limiting
     */
    function _checkRateLimit() internal {
        uint256 currentWindow = block.timestamp / RATE_LIMIT_WINDOW;
        uint256 lastWindow = lastWindowStart[msg.sender];
        
        if (currentWindow > lastWindow) {
            // New window, reset counter
            operationsPerWindow[msg.sender][currentWindow] = 1;
            lastWindowStart[msg.sender] = currentWindow;
        } else {
            // Same window, increment counter
            operationsPerWindow[msg.sender][currentWindow]++;
            require(
                operationsPerWindow[msg.sender][currentWindow] <= MAX_OPERATIONS_PER_WINDOW,
                "Rate limit exceeded"
            );
        }
    }
    
    /**
     * @dev Set gas limits for specific operation
     */
    function setGasLimits(
        bytes4 selector,
        GasLimits calldata limits
    ) external onlyRole(GAS_ADMIN_ROLE) {
        require(limits.maxGasPerOperation > 0, "Invalid max gas per operation");
        require(limits.maxGasPerBatch >= limits.maxGasPerOperation, "Invalid batch limit");
        require(limits.maxLoopIterations > 0, "Invalid max iterations");
        require(limits.maxArrayLength > 0, "Invalid max array length");
        
        gasLimitsBySelector[selector] = limits;
        gasLimitsBySelector[selector].lastUpdateTime = block.timestamp;
        
        emit GasLimitsUpdated(selector, limits);
    }
    
    /**
     * @dev Configure circuit breaker for operation
     */
    function configureCircuitBreaker(
        address contract_,
        bytes4 selector,
        EnhancedCircuitBreaker calldata config
    ) external onlyRole(GAS_ADMIN_ROLE) {
        require(contract_ != address(0), "Invalid contract address");
        require(config.gasThreshold > 0, "Invalid gas threshold");
        require(config.maxFailuresInWindow > 0, "Invalid max failures");
        require(config.timeWindowSeconds > 0, "Invalid time window");
        
        circuitBreakers[contract_][selector] = config;
    }
    
    /**
     * @dev Set retry configuration for operation
     */
    function setRetryConfig(
        bytes4 selector,
        RetryConfig calldata config
    ) external onlyRole(GAS_ADMIN_ROLE) {
        require(config.maxRetries > 0 && config.maxRetries <= 10, "Invalid max retries");
        require(config.baseDelaySeconds > 0, "Invalid base delay");
        require(config.maxDelaySeconds >= config.baseDelaySeconds, "Invalid max delay");
        
        retryConfigs[selector] = config;
        emit RetryConfigUpdated(selector, config);
    }
    
    /**
     * @dev Configure external call settings
     */
    function configureExternalCall(
        address target,
        ExternalCallConfig calldata config
    ) external onlyRole(GAS_ADMIN_ROLE) {
        require(target != address(0), "Invalid target address");
        require(config.maxRetries > 0, "Invalid max retries");
        require(config.timeoutSeconds > 0, "Invalid timeout");
        
        externalCallConfigs[target] = config;
        emit ExternalCallConfigUpdated(target, config);
    }
    
    /**
     * @dev Update network congestion level
     */
    function updateNetworkCongestion(uint256 congestionLevel) 
        external 
        onlyRole(GAS_ADMIN_ROLE) 
    {
        require(congestionLevel <= 10000, "Invalid congestion level");
        require(
            block.timestamp >= lastNetworkUpdate + networkUpdateInterval,
            "Update too frequent"
        );
        
        networkCongestionLevel = congestionLevel;
        lastNetworkUpdate = block.timestamp;
        
        emit NetworkCongestionUpdated(congestionLevel);
    }
    
    /**
     * @dev Reset circuit breaker manually
     */
    function resetCircuitBreaker(
        address contract_,
        bytes4 selector
    ) external onlyRole(EMERGENCY_ROLE) {
        EnhancedCircuitBreaker storage cb = circuitBreakers[contract_][selector];
        cb.isTripped = false;
        cb.currentFailures = 0;
        cb.tripTime = 0;
        
        emit CircuitBreakerReset(contract_, selector);
    }
    
    /**
     * @dev Get optimal gas limit for operation
     */
    function getOptimalGasLimit(bytes4 selector) 
        external 
        view 
        returns (uint256) 
    {
        OperationMetrics memory metrics = operationMetrics[selector];
        if (metrics.optimalGasLimit > 0) {
            return metrics.optimalGasLimit;
        }
        
        GasLimits memory limits = gasLimitsBySelector[selector];
        return limits.maxGasPerOperation > 0 ? 
            limits.maxGasPerOperation : 
            defaultGasLimits.maxGasPerOperation;
    }
    
    /**
     * @dev Get retry configuration for operation
     */
    function getRetryConfig(bytes4 selector) 
        external 
        view 
        returns (RetryConfig memory) 
    {
        RetryConfig memory config = retryConfigs[selector];
        if (config.maxRetries == 0) {
            return defaultRetryConfig;
        }
        return config;
    }
    
    /**
     * @dev Calculate retry delay with exponential backoff and jitter
     */
    function calculateRetryDelay(
        bytes4 selector,
        uint256 attemptNumber
    ) external view returns (uint256) {
        RetryConfig memory config = this.getRetryConfig(selector);
        
        uint256 delay = config.baseDelaySeconds;
        
        if (config.exponentialBackoff && attemptNumber > 1) {
            // Apply exponential backoff
            uint256 multiplier = (config.backoffMultiplier ** (attemptNumber - 1)) / (10000 ** (attemptNumber - 2));
            delay = (delay * multiplier) / 10000;
            
            // Cap at max delay
            if (delay > config.maxDelaySeconds) {
                delay = config.maxDelaySeconds;
            }
        }
        
        // Add jitter if enabled (±25% random variation)
        if (config.jitterEnabled) {
            uint256 jitter = (delay * (block.timestamp % 500)) / 2000; // 0-25% variation
            delay = delay + jitter;
        }
        
        return delay;
    }
    
    /**
     * @dev Check if operation should be retried based on error
     */
    function shouldRetry(
        bytes4 selector,
        uint256 attemptNumber,
        string calldata errorReason
    ) external view returns (bool) {
        RetryConfig memory config = this.getRetryConfig(selector);
        
        if (attemptNumber >= config.maxRetries) {
            return false;
        }
        
        // Don't retry certain errors
        bytes32 errorHash = keccak256(bytes(errorReason));
        if (errorHash == keccak256("INVALID_SIGNATURE") ||
            errorHash == keccak256("UNAUTHORIZED") ||
            errorHash == keccak256("INSUFFICIENT_BALANCE")) {
            return false;
        }
        
        return true;
    }
    
    /**
     * @dev Emergency pause functionality
     */
    function emergencyPause() external onlyRole(EMERGENCY_ROLE) {
        _pause();
    }
    
    /**
     * @dev Unpause functionality
     */
    function unpause() external onlyRole(EMERGENCY_ROLE) {
        _unpause();
    }
    
    /**
     * @dev Get operation metrics for analysis
     */
    function getOperationMetrics(bytes4 selector) 
        external 
        view 
        returns (OperationMetrics memory) 
    {
        return operationMetrics[selector];
    }
    
    /**
     * @dev Get circuit breaker status
     */
    function getCircuitBreakerStatus(address contract_, bytes4 selector) 
        external 
        view 
        returns (bool isTripped, uint256 currentFailures, uint256 tripTime) 
    {
        EnhancedCircuitBreaker memory cb = circuitBreakers[contract_][selector];
        return (cb.isTripped, cb.currentFailures, cb.tripTime);
    }
}
