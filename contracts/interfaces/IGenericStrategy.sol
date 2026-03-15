// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

import "@openzeppelin/contracts/utils/introspection/IERC165.sol";

/**
 * @title IGenericStrategy
 * @notice Interface for arbitrage strategy contracts
 * @dev All strategy contracts must implement this

interface */

interface IGenericStrategy is IERC165 {
    /**
     * @dev Initialize the strategy with configuration data
     * @param initData Initialization data
     */
    function initialize(bytes calldata initData) external;
    
    /**
     * @dev Execute arbitrage operation
     * @param asset Asset being used for arbitrage
     * @param amount Amount of asset being used
     * @param premium Premium to be paid for flash loan
     * @param params Additional parameters for execution
     * @return profit Amount of profit generated
     */
    function executeArbitrage(
        address asset,
        uint256 amount,
        uint256 premium,
        bytes calldata params
    ) external returns (uint256 profit);
    
    /**
     * @dev Get strategy configuration
     * @return Configuration data
     */
    function getStrategyConfig() external view returns (bytes memory);
    
    /**
     * @dev Get strategy type
     * @return Strategy type identifier
     */
    function getStrategyType() external view returns (string memory);
    
    /**
     * @dev Get strategy version
     * @return Version string
     */
    function getVersion() external view returns (string memory);
    
    /**
     * @dev Check if strategy is active
     * @return True if the strategy is active
     */
    function isActive() external view returns (bool);
    
    /**
     * @dev Get strategy performance metrics
     * @return totalExecutions Total number of executions
     * @return successfulExecutions Number of successful executions
     * @return totalProfit Total profit generated
     * @return lastExecutionTime Timestamp of last execution
     */
    function getPerformanceMetrics() external view returns (
        uint256 totalExecutions,
        uint256 successfulExecutions,
        uint256 totalProfit,
        uint256 lastExecutionTime
    );
}
