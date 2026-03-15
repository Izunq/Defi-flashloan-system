// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title IMudarabahFlashSwap
 * @notice Interface for the Mudarabah Flash Swap receiver
 * @dev Shariah-compliant alternative to flash loans
 */

interface IMudarabahFlashSwap {
    /**
     * @dev Execute Mudarabah operation
     * @param asset The asset being used in the Mudarabah
     * @param amount The amount of the asset
     * @param expectedProfit The expected profit from the operation
     * @param initiator The address that initiated the Mudarabah
     * @param params Additional parameters for the operation
     * @return success Whether the operation was successful
     * @return actualProfit The actual profit generated (0 if no profit)
     */
    function executeMudarabahOperation(
        address asset,
        uint256 amount,
        uint256 expectedProfit,
        address initiator,
        bytes calldata params
    ) external returns (bool success, uint256 actualProfit);
}
