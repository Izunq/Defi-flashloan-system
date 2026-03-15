// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title IMudarabahInvestmentPool
 * @notice Interface for the Mudarabah Investment Pool
 * @dev Shariah-compliant investment pool based on profit-sharing principles
 */

interface IMudarabahInvestmentPool {
    /**
     * @dev Invest capital into the Mudarabah pool
     * @param token The token to invest
     * @param amount The amount to invest
     */
    function invest(address token, uint256 amount) external;
    
    /**
     * @dev Withdraw capital from the Mudarabah pool
     * @param token The token to withdraw
     * @param amount The amount to withdraw
     */
    function withdraw(address token, uint256 amount) external;
    
    /**
     * @dev Withdraw profit share
     * @param token The token to withdraw profit in
     */
    function withdrawProfitShare(address token) external;
    
    /**
     * @dev Execute Shariah-compliant strategy
     * @param strategyId The ID of the strategy
     * @param assets The assets to use
     * @param amounts The amounts of each asset
     * @param executionData The execution data for each asset
     * @param aiPredictionId The ID of the AI prediction
     */
    function executeStrategy(
        bytes32 strategyId,
        address[] calldata assets,
        uint256[] calldata amounts,
        bytes[] calldata executionData,
        bytes32 aiPredictionId
    ) external;
    
    /**
     * @dev Distribute profit according to Mudarabah principles
     * @param token The token in which profit is realized
     * @param amount The amount of profit to distribute
     */
    function distributeProfit(address token, uint256 amount) external;
    
    /**
     * @dev Distribute loss according to Mudarabah principles
     * @param token The token in which loss is realized
     * @param amount The amount of loss to distribute
     */
    function distributeLoss(address token, uint256 amount) external;
}
