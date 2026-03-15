// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title IHalalAssetRegistry
 * @notice Interface for the Halal Asset Registry
 * @dev Used to verify if assets are Shariah-compliant */

interface IHalalAssetRegistry {
    /**
     * @dev Check if an asset is Shariah-compliant
     * @param asset The address of the asset to check
     * @return isCompliant Whether the asset is Shariah-compliant
     */
    function isHalalCompliant(address asset) external view returns (bool);
    
    /**
     * @dev Get information about a Halal asset
     * @param asset The address of the asset
     * @return name The name of the asset
     * @return approvalReason The reason for approval
     * @return approvalTimestamp When the asset was approved
     * @return approvedBy Who approved the asset
     */
    function getHalalAssetInfo(address asset) external view returns (
        string memory name,
        string memory approvalReason,
        uint256 approvalTimestamp,
        address approvedBy
    );
}
