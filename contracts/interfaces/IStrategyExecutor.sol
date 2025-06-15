// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IStrategyExecutor
 * @notice Interface for strategy executor contracts
 * @dev Implement this interface to execute arbitrage strategies
 */
interface IStrategyExecutor {
    /**
     * @dev Execution details struct
     */
    struct ExecutionDetails {
        address strategy;
        address initiator;
        uint256 startTime;
        uint256 endTime;
        bool successful;
        uint256 profit;
        bytes32 executionHash;
        uint8 status; // ExecutionStatus enum
    }
    
    /**
     * @dev Initiate arbitrage execution
     * @param strategy Strategy address to execute
     * @param asset Asset to borrow
     * @param amount Amount to borrow
     * @param params Additional parameters for the strategy
     * @return executionId Unique identifier for this execution
     */
    function initiateArbitrage(
        address strategy,
        address asset,
        uint256 amount,
        bytes calldata params
    ) external returns (bytes32 executionId);
    
    /**
     * @dev Get execution details
     * @param executionId Execution ID
     * @return Execution details
     */
    function getExecutionDetails(bytes32 executionId) 
        external 
        view 
        returns (ExecutionDetails memory);
    
    /**
     * @dev Set strategy approval
     * @param strategy Strategy address
     * @param approved Approval status
     */
    function setStrategyApproval(address strategy, bool approved) external;
    
    /**
     * @dev Set minimum return amount for a token (slippage protection)
     * @param token Token address
     * @param minAmount Minimum return amount
     */
    function setMinReturnAmount(address token, uint256 minAmount) external;
    
    /**
     * @dev Set circuit breaker threshold
     * @param threshold New threshold
     */
    function setCircuitBreakerThreshold(uint256 threshold) external;
    
    /**
     * @dev Reset circuit breaker
     */
    function resetCircuitBreaker() external;
    
    /**
     * @dev Set maximum gas price for MEV protection
     * @param newMaxGasPrice New maximum gas price
     */
    function setMaxGasPrice(uint256 newMaxGasPrice) external;
    
    /**
     * @dev Emergency pause function
     */
    function emergencyPause() external;
    
    /**
     * @dev Emergency unpause function
     */
    function emergencyUnpause() external;
    
    /**
     * @dev Emergency fund recovery
     * @param token Token to recover
     */
    function emergencyFundRecovery(address token) external;
}