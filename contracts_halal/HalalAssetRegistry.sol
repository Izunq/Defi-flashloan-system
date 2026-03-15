// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @dev Interface for ERC20 tokens with an underlying asset
 */
interface IWrappedToken {
    function underlying() external view returns (address);
}

/**
 * @dev Interface for proxy contracts
 */
interface IProxyToken {
    function implementation() external view returns (address);
    function target() external view returns (address);
    function proxy() external view returns (address);
}

/**
 * @title HalalAssetRegistry
 * @notice Central registry for Shariah-compliant assets
 * @dev This contract serves as the single source of truth for all halal-compliant assets
 */
contract HalalAssetRegistry is AccessControl, Pausable, ReentrancyGuard, Ownable {
    // Role definitions
    bytes32 public constant SHARIAH_COMMITTEE_ROLE = keccak256("SHARIAH_COMMITTEE_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    // Asset compliance status
    mapping(address => bool) public halalCompliantAssets;
    
    // Explicitly blacklisted tokens (overrides isHalalCompliant)
    mapping(address => bool) public isExplicitlyBlacklisted;
    
    // Asset metadata
    mapping(address => string) public assetName;
    mapping(address => string) public complianceReason;
    mapping(address => uint256) public reviewTimestamp;
    
    // List of all compliant assets
    address[] public compliantAssets;
    
    // Industry categories (non-compliant)
    mapping(string => bool) public prohibitedIndustries;
    
    // Events
    event AssetApproved(address indexed asset, string name, string reason, address approver);
    event AssetRemoved(address indexed asset, string reason, address remover);
    event AssetBlacklisted(address indexed asset, string reason, address blacklister);
    event ProhibitedIndustryAdded(string industry, address adder);
    event ProhibitedIndustryRemoved(string industry, address remover);
      /**
     * @dev Constructor
     * @param _admin Address of the admin
     * @param _shariahCommittee Address of the initial Shariah committee member
     */
    constructor(address _admin, address _shariahCommittee) Ownable(_admin) {
        require(_admin != address(0), "Invalid admin address");
        require(_shariahCommittee != address(0), "Invalid committee address");
          _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(ADMIN_ROLE, _admin);
        _grantRole(SHARIAH_COMMITTEE_ROLE, _shariahCommittee);
        
        // Initialize prohibited industries
        _addProhibitedIndustry("Alcohol");
        _addProhibitedIndustry("Conventional Banking");
        _addProhibitedIndustry("Gambling");
        _addProhibitedIndustry("Pork");
        _addProhibitedIndustry("Tobacco");
        _addProhibitedIndustry("Adult Entertainment");
        _addProhibitedIndustry("Weapons");
        _addProhibitedIndustry("Interest-Based Finance");
        
        // Blacklist common interest-bearing tokens
        // Compound tokens
        _blacklistAsset(0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643, "cDAI - Interest-bearing");
        _blacklistAsset(0x39AA39c021dfbaE8faC545936693aC917d5E7563, "cUSDC - Interest-bearing");
        _blacklistAsset(0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5, "cETH - Interest-bearing");
        
        // Aave tokens
        _blacklistAsset(0x028171bCA77440897B824Ca71D1c56caC55b68A3, "aDAI - Interest-bearing");
        _blacklistAsset(0xBcca60bB61934080951369a648Fb03DF4F96263C, "aUSDC - Interest-bearing");
        
        // Maker DSR
        _blacklistAsset(0x06AF07097C9Eeb7fD685c692751D5C66dB49c215, "Chai - Interest-bearing DAI");
        
        // Other interest-bearing tokens can be added as needed
    }
      /**
     * @dev Add an asset to the halal-compliant registry
     * @param _asset Address of the token contract
     * @param _name Name of the asset
     * @param _reason Reason for compliance approval
     */
    function approveAsset(
        address _asset,
        string calldata _name,
        string calldata _reason
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE) whenNotPaused nonReentrant {
        require(_asset != address(0), "Invalid asset address");
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(bytes(_reason).length > 0, "Reason cannot be empty");
        require(!halalCompliantAssets[_asset], "Asset already approved");
        
        halalCompliantAssets[_asset] = true;
        assetName[_asset] = _name;
        complianceReason[_asset] = _reason;
        reviewTimestamp[_asset] = block.timestamp;
        compliantAssets.push(_asset);
        
        emit AssetApproved(_asset, _name, _reason, msg.sender);
    }
      /**
     * @dev Remove an asset from the halal-compliant registry
     * @param _asset Address of the token contract
     * @param _reason Reason for removal
     */
    function removeAsset(
        address _asset,
        string calldata _reason
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE) nonReentrant {
        require(halalCompliantAssets[_asset], "Asset not approved");
        require(bytes(_reason).length > 0, "Reason cannot be empty");
        
        halalCompliantAssets[_asset] = false;
        complianceReason[_asset] = _reason;
        reviewTimestamp[_asset] = block.timestamp;
        
        // Remove from compliantAssets array
        for (uint256 i = 0; i < compliantAssets.length; i++) {
            if (compliantAssets[i] == _asset) {
                compliantAssets[i] = compliantAssets[compliantAssets.length - 1];
                compliantAssets.pop();
                break;
            }
        }
        
        emit AssetRemoved(_asset, _reason, msg.sender);
    }
      /**
     * @dev Add a prohibited industry
     * @param _industry Name of the prohibited industry
     */
    function addProhibitedIndustry(string calldata _industry) external onlyRole(SHARIAH_COMMITTEE_ROLE) nonReentrant {
        _addProhibitedIndustry(_industry);
    }
    
    /**
     * @dev Internal function to add a prohibited industry
     * @param _industry Name of the prohibited industry
     */
    function _addProhibitedIndustry(string memory _industry) internal {
        require(bytes(_industry).length > 0, "Industry name cannot be empty");
        require(!prohibitedIndustries[_industry], "Industry already prohibited");
        
        prohibitedIndustries[_industry] = true;
        
        emit ProhibitedIndustryAdded(_industry, msg.sender);
    }
    
    /**
     * @dev Internal function to blacklist an asset
     * @param _asset Address of the token contract
     * @param _reason Reason for blacklisting
     */
    function _blacklistAsset(address _asset, string memory _reason) internal {
        if (halalCompliantAssets[_asset]) {
            halalCompliantAssets[_asset] = false;
            
            // Remove from compliantAssets array if present
            for (uint256 i = 0; i < compliantAssets.length; i++) {
                if (compliantAssets[i] == _asset) {
                    compliantAssets[i] = compliantAssets[compliantAssets.length - 1];
                    compliantAssets.pop();
                    break;
                }
            }
        }
        
        isExplicitlyBlacklisted[_asset] = true;
        complianceReason[_asset] = _reason;
        reviewTimestamp[_asset] = block.timestamp;
    }
    
    /**
     * @dev Remove a prohibited industry
     * @param _industry Name of the prohibited industry
     */    function removeProhibitedIndustry(string calldata _industry) external onlyRole(SHARIAH_COMMITTEE_ROLE) nonReentrant {
        require(prohibitedIndustries[_industry], "Industry not prohibited");
        
        prohibitedIndustries[_industry] = false;
        
        emit ProhibitedIndustryRemoved(_industry, msg.sender);
    }
      /**
     * @dev Explicitly blacklist a token (e.g., interest-bearing tokens)
     * @param _asset Address of the token contract
     * @param _reason Reason for blacklisting
     */
    function blacklistAsset(
        address _asset,
        string calldata _reason
    ) external onlyRole(SHARIAH_COMMITTEE_ROLE) nonReentrant {
        require(_asset != address(0), "Invalid asset address");
        require(bytes(_reason).length > 0, "Reason cannot be empty");
        
        // If it was previously approved, remove it
        if (halalCompliantAssets[_asset]) {
            removeAsset(_asset, _reason);
        }
        
        isExplicitlyBlacklisted[_asset] = true;
        complianceReason[_asset] = _reason;
        reviewTimestamp[_asset] = block.timestamp;        
        emit AssetBlacklisted(_asset, _reason, msg.sender);
    }
    
    /**
     * @dev Check if an asset is halal compliant
     * @param _asset Address of the token contract
     * @return Whether the asset is halal compliant
     */    function isHalalCompliant(address _asset) external view returns (bool) {
        return _isHalalCompliantRecursive(_asset, new address[](10), 0);
    }
    
    /**
     * @dev Recursive function to check if an asset is halal compliant
     * @param _asset Address of the token contract
     * @param _checkedAssets Array of already checked assets to prevent infinite loops
     * @param _depth Current recursion depth
     * @return Whether the asset is halal compliant
     */
    function _isHalalCompliantRecursive(
        address _asset, 
        address[] memory _checkedAssets, 
        uint256 _depth
    ) internal view returns (bool) {
        // Prevent infinite recursion and stack too deep
        if (_depth >= 5) {
            return false;
        }
        
        // Check if we've already seen this asset in the current chain
        for (uint256 i = 0; i < _depth; i++) {
            if (_checkedAssets[i] == _asset) {
                return false; // Circular reference detected
            }
        }
        
        // Add current asset to checked list
        _checkedAssets[_depth] = _asset;
        
        // Blacklist overrides approval
        if (isExplicitlyBlacklisted[_asset]) {
            return false;
        }
        
        // If explicitly approved, return true
        if (halalCompliantAssets[_asset]) {
            return true;
        }
        
        // Check if it's a wrapped token with an underlying asset
        try IWrappedToken(_asset).underlying() returns (address underlying) {
            if (underlying != address(0) && underlying != _asset) {
                return _isHalalCompliantRecursive(underlying, _checkedAssets, _depth + 1);
            }
        } catch {}
        
        // Check if it's a proxy contract
        try IProxyToken(_asset).implementation() returns (address implementation) {
            if (implementation != address(0) && implementation != _asset) {
                return _isHalalCompliantRecursive(implementation, _checkedAssets, _depth + 1);
            }
        } catch {}
        
        try IProxyToken(_asset).target() returns (address target) {
            if (target != address(0) && target != _asset) {
                return _isHalalCompliantRecursive(target, _checkedAssets, _depth + 1);
            }
        } catch {}
        
        try IProxyToken(_asset).proxy() returns (address proxy) {
            if (proxy != address(0) && proxy != _asset) {
                return _isHalalCompliantRecursive(proxy, _checkedAssets, _depth + 1);
            }
        } catch {}
        
        // Not explicitly approved and not a recognized proxy/wrapped token
        return false;
    }
    
    /**
     * @dev Get all compliant assets
     * @return Array of compliant asset addresses
     */    function getAllCompliantAssets() external view returns (address[] memory) {
        return compliantAssets;
    }
    
    /**
     * @dev Count of compliant assets
     * @return Number of compliant assets
     */    function getCompliantAssetCount() external view returns (uint256) {        return compliantAssets.length;
    }
    
    /**
     * @dev Pause the registry (emergency)
     */
    function pause() external onlyRole(ADMIN_ROLE) nonReentrant onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause the registry
     */
    function unpause() external onlyRole(ADMIN_ROLE) nonReentrant onlyOwner {
        _unpause();
    }
}