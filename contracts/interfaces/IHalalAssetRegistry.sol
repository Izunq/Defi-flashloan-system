// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title IHalalAssetRegistry - Interface for the halal asset compliance registry
/// @notice Maintains a registry of tokens that have been reviewed and approved
///         as Sharia-compliant, along with blacklisted tokens that must be avoided.
interface IHalalAssetRegistry {
    /// @notice Check whether a token is approved as halal-compliant
    /// @param token The address of the token to check
    /// @return True if the token is approved as halal-compliant
    function isHalalCompliant(address token) external view returns (bool);

    /// @notice Check whether a token is blacklisted (non-compliant)
    /// @param token The address of the token to check
    /// @return True if the token is blacklisted
    function isBlacklisted(address token) external view returns (bool);

    /// @notice Get full asset information for a given token
    /// @param token The address of the token to query
    /// @return name The name or label assigned to the asset in the registry
    /// @return approvalReason The reason or basis for the compliance decision
    /// @return reviewTimestamp The timestamp of the last compliance review
    /// @return approved Whether the asset is currently approved as halal
    /// @return blacklisted Whether the asset is currently blacklisted
    function getAssetInfo(
        address token
    )
        external
        view
        returns (
            string memory name,
            string memory approvalReason,
            uint256 reviewTimestamp,
            bool approved,
            bool blacklisted
        );
}
