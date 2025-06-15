// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title GasGriefingProtection
 * @notice Centralized contract for gas griefing protection mechanisms
 * @dev Provides common utilities and limits for preventing DoS attacks through gas exhaustion
 */
contract GasGriefingProtection is Ownable, ReentrancyGuard, Pausable {
    
    // Circuit breaker state
    struct CircuitBreaker {
        uint256 gasThreshold;        // Gas threshold for circuit breaker
        uint256 consecutiveFailures; // Number of consecutive failures
        uint256 failureThreshold;   // Threshold for triggering circuit breaker
        uint256 lastResetTime;      // Last time circuit breaker was reset
        bool isTripped;             // Whether circuit breaker is currently tripped
    }
    
    // Global limits
    uint256 public constant MAX_BATCH_SIZE = 100;
    uint256 public constant MAX_ARRAY_LENGTH = 1000;
    uint256 public constant MAX_LOOP_ITERATIONS = 500;
    uint256 public constant MIN_GAS_RESERVE = 50000;
    
    // Per-contract circuit breakers
    mapping(address => CircuitBreaker) public circuitBreakers;
    
    // Gas usage tracking
    mapping(address => uint256) public totalGasUsed;
    mapping(address => uint256) public lastGasUsageReset;
    
    // Rate limiting
    mapping(address => uint256) public lastOperationTime;
    mapping(address => uint256) public operationCount;
    uint256 public constant RATE_LIMIT_WINDOW = 1 minutes;
    uint256 public constant MAX_OPERATIONS_PER_WINDOW = 10;
    
    // Events
    event CircuitBreakerTripped(address indexed contract_, uint256 gasUsed);
    event CircuitBreakerReset(address indexed contract_);
    event GasLimitExceeded(address indexed contract_, uint256 gasUsed, uint256 limit);
    event RateLimitExceeded(address indexed user, uint256 operations, uint256 timeWindow);
    
    /**
     * @dev Check if operation is within gas limits
     * @param gasUsed Gas used by the operation
     * @param gasLimit Maximum allowed gas
     */
    modifier gasLimitCheck(uint256 gasUsed, uint256 gasLimit) {
        require(gasUsed <= gasLimit, "Gas limit exceeded");
        
        CircuitBreaker storage cb = circuitBreakers[msg.sender];
        if (gasUsed > cb.gasThreshold) {
            cb.consecutiveFailures++;
            if (cb.consecutiveFailures >= cb.failureThreshold) {
                cb.isTripped = true;
                emit CircuitBreakerTripped(msg.sender, gasUsed);
            }
            emit GasLimitExceeded(msg.sender, gasUsed, gasLimit);
        } else {
            cb.consecutiveFailures = 0; // Reset on successful operation
        }
        _;
    }
    
    /**
     * @dev Check if circuit breaker is tripped
     */
    modifier circuitBreakerCheck() {
        CircuitBreaker storage cb = circuitBreakers[msg.sender];
        require(!cb.isTripped, "Circuit breaker tripped");
        _;
    }
    
    /**
     * @dev Rate limiting check
     */
    modifier rateLimitCheck() {
        uint256 currentTime = block.timestamp;
        
        // Reset counter if window has passed
        if (currentTime > lastOperationTime[msg.sender] + RATE_LIMIT_WINDOW) {
            operationCount[msg.sender] = 0;
            lastOperationTime[msg.sender] = currentTime;
        }
        
        require(operationCount[msg.sender] < MAX_OPERATIONS_PER_WINDOW, "Rate limit exceeded");
        operationCount[msg.sender]++;
        
        if (operationCount[msg.sender] >= MAX_OPERATIONS_PER_WINDOW) {
            emit RateLimitExceeded(msg.sender, operationCount[msg.sender], RATE_LIMIT_WINDOW);
        }
        _;
    }
    
    /**
     * @dev Initialize circuit breaker for a contract
     * @param contract_ Contract address
     * @param gasThreshold Gas threshold for circuit breaker
     * @param failureThreshold Number of failures before tripping
     */
    function initializeCircuitBreaker(
        address contract_,
        uint256 gasThreshold,
        uint256 failureThreshold
    ) external onlyOwner {
        circuitBreakers[contract_] = CircuitBreaker({
            gasThreshold: gasThreshold,
            consecutiveFailures: 0,
            failureThreshold: failureThreshold,
            lastResetTime: block.timestamp,
            isTripped: false
        });
    }
    
    /**
     * @dev Reset circuit breaker for a contract
     * @param contract_ Contract address
     */
    function resetCircuitBreaker(address contract_) external onlyOwner {
        CircuitBreaker storage cb = circuitBreakers[contract_];
        cb.isTripped = false;
        cb.consecutiveFailures = 0;
        cb.lastResetTime = block.timestamp;
        emit CircuitBreakerReset(contract_);
    }
    
    /**
     * @dev Check array size limits
     * @param arrayLength Length of the array to check
     */
    function checkArraySize(uint256 arrayLength) external pure {
        require(arrayLength <= MAX_ARRAY_LENGTH, "Array too large");
        require(arrayLength > 0, "Array cannot be empty");
    }
    
    /**
     * @dev Check batch size limits
     * @param batchSize Size of the batch to check
     */
    function checkBatchSize(uint256 batchSize) external pure {
        require(batchSize <= MAX_BATCH_SIZE, "Batch size too large");
        require(batchSize > 0, "Batch cannot be empty");
    }
    
    /**
     * @dev Safe loop execution with gas monitoring
     * @param iterations Number of iterations to perform
     * @param gasPerIteration Estimated gas per iteration
     */
    function safeLoop(uint256 iterations, uint256 gasPerIteration) external view {
        require(iterations <= MAX_LOOP_ITERATIONS, "Too many loop iterations");
        
        uint256 estimatedGas = iterations * gasPerIteration;
        require(gasleft() > estimatedGas + MIN_GAS_RESERVE, "Insufficient gas for operation");
    }
    
    /**
     * @dev Get circuit breaker status
     * @param contract_ Contract address
     */
    function getCircuitBreakerStatus(address contract_) external view returns (
        uint256 gasThreshold,
        uint256 consecutiveFailures,
        uint256 failureThreshold,
        uint256 lastResetTime,
        bool isTripped
    ) {
        CircuitBreaker storage cb = circuitBreakers[contract_];
        return (
            cb.gasThreshold,
            cb.consecutiveFailures,
            cb.failureThreshold,
            cb.lastResetTime,
            cb.isTripped
        );
    }
    
    /**
     * @dev Emergency pause all operations
     */
    function emergencyPause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Emergency unpause all operations
     */
    function emergencyUnpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Update global limits (emergency use only)
     */
    function updateGlobalLimits(
        uint256 newRateLimit,
        uint256 newTimeWindow
    ) external onlyOwner {
        // These should be constants, but allowing emergency updates
        // Implementation would require additional storage variables
        // This is a placeholder for emergency scenarios
    }
}
