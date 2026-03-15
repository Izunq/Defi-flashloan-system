// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title IGasOptimizer
 * @notice Interface for gas optimization and DoS protection
 */

interface IGasOptimizer {
    
    struct GasLimits {
        uint256 maxGasPerOperation;
        uint256 maxGasPerBatch;
        uint256 maxLoopIterations;
        uint256 maxArrayLength;
        uint256 gasBuffer;
        uint256 lastUpdateTime;
        bool adaptive;
    }
    
    struct RetryConfig {
        uint256 maxRetries;
        uint256 baseDelaySeconds;
        uint256 maxDelaySeconds;
        uint256 backoffMultiplier;
        bool exponentialBackoff;
        bool jitterEnabled;
    }
    
    struct OperationMetrics {
        uint256 totalGasUsed;
        uint256 executionCount;
        uint256 failureCount;
        uint256 averageGasUsed;
        uint256 lastExecutionTime;
        uint256 optimalGasLimit;
    }
    
    /**
     * @dev Get optimal gas limit for operation
     */
    function getOptimalGasLimit(bytes4 selector) external view returns (uint256);
    
    /**
     * @dev Get retry configuration for operation
     */
    function getRetryConfig(bytes4 selector) external view returns (RetryConfig memory);
    
    /**
     * @dev Calculate retry delay with exponential backoff
     */
    function calculateRetryDelay(bytes4 selector, uint256 attemptNumber) external view returns (uint256);
    
    /**
     * @dev Check if operation should be retried
     */
    function shouldRetry(bytes4 selector, uint256 attemptNumber, string calldata errorReason) external view returns (bool);
    
    /**
     * @dev Get operation metrics
     */
    function getOperationMetrics(bytes4 selector) external view returns (OperationMetrics memory);
    
    /**
     * @dev Get circuit breaker status
     */
    function getCircuitBreakerStatus(address contract_, bytes4 selector) external view returns (bool isTripped, uint256 currentFailures, uint256 tripTime);
}
