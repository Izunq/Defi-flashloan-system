// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title IAaveV3Pool - Minimal Aave V3 Pool interface for flash loans
/// @notice Only includes the functions needed for flash loan arbitrage on Arbitrum
interface IAaveV3Pool {
    /// @notice Execute a simple flash loan (single asset)
    /// @param receiverAddress The address of the contract receiving the flash loan
    /// @param asset The address of the asset being flash-borrowed
    /// @param amount The amount of the asset being flash-borrowed
    /// @param params Arbitrary bytes-encoded params to pass to the receiver
    /// @param referralCode Referral code for tracking (use 0 if none)
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;

    /// @notice Returns the total flash loan premium as a percentage (in bps)
    /// @return The total flash loan premium
    function FLASHLOAN_PREMIUM_TOTAL() external view returns (uint128);
}
