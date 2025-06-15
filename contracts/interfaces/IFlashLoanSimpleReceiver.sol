// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IFlashLoanSimpleReceiver
 * @notice Interface for flash loan receivers
 * @dev Implement this interface to receive flash loans
 */
interface IFlashLoanSimpleReceiver {
    /**
     * @dev Executes an operation after receiving the flash-borrowed asset
     * @param asset The address of the flash-borrowed asset
     * @param amount The amount of the flash-borrowed asset
     * @param premium The fee of the flash-borrowed asset
     * @param initiator The address of the flashloan initiator
     * @param params Encoded parameters for the operation
     * @return True if the operation is successful
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}