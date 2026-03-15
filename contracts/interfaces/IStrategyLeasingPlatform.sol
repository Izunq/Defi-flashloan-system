// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title IStrategyLeasingPlatform
 * @notice Interface for the Strategy Leasing Platform
 * @dev Shariah-compliant platform for leasing trading strategies based on Ijara principles
 */

interface IStrategyLeasingPlatform {
    /**
     * @dev Register a new strategy for leasing
     * @param _name Strategy name
     * @param _description Strategy description
     * @param _leasePrice Price per lease period
     * @param _leasePeriod Lease period in seconds
     * @param _paymentToken Token used for payment
     * @return strategyId The ID of the registered strategy
     */
    function registerStrategy(
        string calldata _name,
        string calldata _description,
        uint256 _leasePrice,
        uint256 _leasePeriod,
        address _paymentToken
    ) external returns (bytes32);
    
    /**
     * @dev Lease a strategy
     * @param _strategyId ID of the strategy to lease
     */
    function leaseStrategy(bytes32 _strategyId) external;
    
    /**
     * @dev Check if a user has an active lease for a strategy
     * @param _strategyId ID of the strategy
     * @param _lessee Address of the lessee
     * @return Whether the lessee has an active lease
     */
    function hasActiveLease(bytes32 _strategyId, address _lessee) external view returns (bool);
    
    /**
     * @dev Get active strategies
     * @return Array of active strategy IDs
     */
    function getActiveStrategies() external view returns (bytes32[] memory);
}
