// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IFlashLoanReceiver {
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}

/// @title MockAavePool — Simulates Aave V3 flash loan behaviour for testing
contract MockAavePool {
    /// @dev Accept ETH so tests can fund this address for gas when impersonating.
    receive() external payable {}

    function flashLoanSimple(
        address receiver,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 /* referralCode */
    ) external {
        // Transfer the borrowed amount to the receiver
        IERC20(asset).transfer(receiver, amount);

        // Calculate the premium (0.05%)
        uint256 premium = (amount * 5) / 10000;

        // Call the receiver's executeOperation callback
        IFlashLoanReceiver(receiver).executeOperation(
            asset,
            amount,
            premium,
            receiver,  // initiator = receiver (the contract that called flashLoanSimple)
            params
        );

        // Pull back the loan + premium
        IERC20(asset).transferFrom(receiver, address(this), amount + premium);
    }

    function FLASHLOAN_PREMIUM_TOTAL() external pure returns (uint128) {
        return 5;
    }
}
