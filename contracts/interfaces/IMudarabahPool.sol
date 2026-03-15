// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title IMudarabahPool - Interface for the Mudarabah investment pool
/// @notice Mudarabah is an Islamic finance partnership where one party provides
///         capital (Rabb al-Mal) and the other provides labor/expertise (Mudarib).
///         Profits are shared according to a pre-agreed ratio; losses are borne
///         by the capital provider only.
interface IMudarabahPool {
    /// @notice Deposit tokens into the pool as a capital provider
    /// @param token The address of the token to deposit
    /// @param amount The amount of tokens to deposit
    function deposit(address token, uint256 amount) external;

    /// @notice Withdraw tokens from the pool by redeeming shares
    /// @param token The address of the token to withdraw
    /// @param shares The number of shares to redeem
    function withdraw(address token, uint256 shares) external;

    /// @notice Claim accumulated profit for a given token
    /// @param token The address of the token to claim profit for
    function claimProfit(address token) external;

    /// @notice Execute a Mudarabah operation (called by the Mudarib)
    /// @param token The address of the token used in the operation
    /// @param amount The amount of tokens to deploy
    /// @param data Arbitrary encoded data describing the operation strategy
    function executeMudarabah(
        address token,
        uint256 amount,
        bytes calldata data
    ) external;

    /// @notice Get the total pool balance for a given token
    /// @param token The address of the token to query
    /// @return The total balance of the token held by the pool
    function getPoolBalance(address token) external view returns (uint256);

    /// @notice Get the share balance for a specific capital provider
    /// @param token The address of the token to query
    /// @param provider The address of the capital provider
    /// @return The number of shares held by the provider for the given token
    function getShareBalance(
        address token,
        address provider
    ) external view returns (uint256);

    /// @notice Get the profit-sharing ratio between provider and Mudarib
    /// @return providerShare The capital provider's share (in basis points)
    /// @return mudaribShare The Mudarib's share (in basis points)
    function getProfitRatio()
        external
        view
        returns (uint256 providerShare, uint256 mudaribShare);
}
