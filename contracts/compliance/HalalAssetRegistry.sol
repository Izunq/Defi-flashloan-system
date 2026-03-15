// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

/// @title HalalAssetRegistry — Sharia-compliant token allowlist
/// @notice Maintains an on-chain registry of approved (halal) and blacklisted
///         tokens.  A dedicated Shariah Committee role governs approvals,
///         revocations, and blacklisting.  Blacklisted tokens (e.g. interest-
///         bearing aTokens) can never be approved until the blacklist flag is
///         explicitly removed.
contract HalalAssetRegistry is AccessControl {
    // ─── Roles ───────────────────────────────────────────────────────────
    /// @notice Members of the Shariah Committee can approve / revoke / blacklist assets
    bytes32 public constant SHARIAH_COMMITTEE_ROLE =
        keccak256("SHARIAH_COMMITTEE_ROLE");

    // ─── Types ───────────────────────────────────────────────────────────
    /// @notice Metadata stored for every registered token
    struct AssetInfo {
        string name;
        string approvalReason;
        uint256 reviewTimestamp;
        bool approved;
        bool blacklisted;
    }

    // ─── State ───────────────────────────────────────────────────────────
    mapping(address => AssetInfo) private _assets;

    // ─── Events ──────────────────────────────────────────────────────────
    event AssetApproved(address indexed token, string name, string reason);
    event AssetRevoked(address indexed token);
    event AssetBlacklisted(address indexed token, string reason);
    event BlacklistRemoved(address indexed token);

    // ─── Errors ──────────────────────────────────────────────────────────
    error AssetIsBlacklisted(address token);
    error ZeroAddress();

    // ─── Constructor ─────────────────────────────────────────────────────
    /// @param _blacklistedTokens Array of known interest-bearing / non-compliant
    ///        token addresses to pre-blacklist at deployment (aTokens, etc.)
    constructor(address[] memory _blacklistedTokens) {
        // OZ 5.x: use _grantRole (not _setupRole)
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(SHARIAH_COMMITTEE_ROLE, msg.sender);

        for (uint256 i = 0; i < _blacklistedTokens.length; i++) {
            address token = _blacklistedTokens[i];
            if (token == address(0)) revert ZeroAddress();

            _assets[token].blacklisted = true;
            _assets[token].reviewTimestamp = block.timestamp;
            emit AssetBlacklisted(token, "Pre-blacklisted at deployment");
        }
    }

    // ─── Mutative — Shariah Committee ────────────────────────────────────

    /// @notice Approve a token as Sharia-compliant
    /// @param token  The ERC-20 token address
    /// @param name   Human-readable token name (for reference)
    /// @param reason Justification for Shariah approval
    function approveAsset(
        address token,
        string calldata name,
        string calldata reason
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE) {
        if (token == address(0)) revert ZeroAddress();
        if (_assets[token].blacklisted) revert AssetIsBlacklisted(token);

        AssetInfo storage info = _assets[token];
        info.name = name;
        info.approvalReason = reason;
        info.reviewTimestamp = block.timestamp;
        info.approved = true;

        emit AssetApproved(token, name, reason);
    }

    /// @notice Revoke Shariah approval for a token (does NOT blacklist it)
    /// @param token The ERC-20 token address
    function revokeAsset(
        address token
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE) {
        _assets[token].approved = false;
        _assets[token].reviewTimestamp = block.timestamp;
        emit AssetRevoked(token);
    }

    /// @notice Blacklist a token — automatically revokes approval
    /// @param token  The ERC-20 token address
    /// @param reason Justification for blacklisting
    function blacklistAsset(
        address token,
        string calldata reason
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE) {
        if (token == address(0)) revert ZeroAddress();

        AssetInfo storage info = _assets[token];
        info.blacklisted = true;
        info.approved = false;
        info.approvalReason = reason;
        info.reviewTimestamp = block.timestamp;

        emit AssetBlacklisted(token, reason);
    }

    /// @notice Remove a token from the blacklist (does NOT auto-approve)
    /// @param token The ERC-20 token address
    function removeBlacklist(
        address token
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE) {
        _assets[token].blacklisted = false;
        _assets[token].reviewTimestamp = block.timestamp;
        emit BlacklistRemoved(token);
    }

    // ─── View ────────────────────────────────────────────────────────────

    /// @notice Check whether a token is approved AND not blacklisted
    /// @return True if the token is halal-compliant for use in arbitrage
    function isHalalCompliant(address token) external view returns (bool) {
        return _assets[token].approved && !_assets[token].blacklisted;
    }

    /// @notice Check whether a token is on the blacklist
    function isBlacklisted(address token) external view returns (bool) {
        return _assets[token].blacklisted;
    }

    /// @notice Retrieve full metadata for a registered asset
    /// @return name            Human-readable name
    /// @return approvalReason  Reason for last approval / blacklist
    /// @return reviewTimestamp Timestamp of the most recent status change
    /// @return approved        Whether the asset is currently approved
    /// @return blacklisted     Whether the asset is currently blacklisted
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
        )
    {
        AssetInfo storage info = _assets[token];
        return (
            info.name,
            info.approvalReason,
            info.reviewTimestamp,
            info.approved,
            info.blacklisted
        );
    }
}
