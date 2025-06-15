// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/proxy/Clones.sol";
import "./interfaces/IGenericStrategy.sol";

/**
 * @title StrategyFactoryV33
 * @notice Factory contract for creating and managing arbitrage strategies
 * @dev Uses minimal proxy pattern for gas-efficient strategy deployment
 */
contract StrategyFactoryV33 is AccessControl, ReentrancyGuard, Pausable {
    using Clones for address;
    
    // Roles
    bytes32 public constant STRATEGY_CREATOR_ROLE = keccak256("STRATEGY_CREATOR_ROLE");
    bytes32 public constant STRATEGY_MANAGER_ROLE = keccak256("STRATEGY_MANAGER_ROLE");
    bytes32 public constant EMERGENCY_ADMIN_ROLE = keccak256("EMERGENCY_ADMIN_ROLE");
    
    // Strategy templates
    mapping(string => address) public strategyTemplates;
    string[] public strategyTypes;
    
    // Deployed strategies
    struct StrategyInfo {
        address strategyAddress;
        string strategyType;
        address creator;
        uint256 createdAt;
        bool active;
        bytes32 configHash;
    }
    
    mapping(bytes32 => StrategyInfo) public strategies;
    bytes32[] public strategyIds;
    
    // Strategy approval tracking
    mapping(bytes32 => bool) public approvedStrategies;
    
    // Events
    event StrategyTemplateAdded(string indexed strategyType, address indexed templateAddress);
    event StrategyTemplateRemoved(string indexed strategyType);
    event StrategyCreated(
        bytes32 indexed strategyId,
        string strategyType,
        address indexed strategyAddress,
        address indexed creator
    );
    event StrategyActivated(bytes32 indexed strategyId, address indexed activator);
    event StrategyDeactivated(bytes32 indexed strategyId, address indexed deactivator);
    event StrategyApproved(bytes32 indexed strategyId, address indexed approver);
    event StrategyRejected(bytes32 indexed strategyId, address indexed rejecter);
    
    /**
     * @dev Constructor
     */
    constructor() {
        // Setup roles
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(STRATEGY_CREATOR_ROLE, msg.sender);
        _setupRole(STRATEGY_MANAGER_ROLE, msg.sender);
        _setupRole(EMERGENCY_ADMIN_ROLE, msg.sender);
    }
    
    /**
     * @dev Add a strategy template
     * @param strategyType Type identifier for the strategy
     * @param templateAddress Address of the template contract
     */
    function addStrategyTemplate(string calldata strategyType, address templateAddress) 
        external 
        onlyRole(STRATEGY_MANAGER_ROLE) 
    {
        require(bytes(strategyType).length > 0, "Strategy type cannot be empty");
        require(templateAddress != address(0), "Invalid template address");
        require(strategyTemplates[strategyType] == address(0), "Template already exists");
        
        // Verify the template implements IGenericStrategy
        require(
            IGenericStrategy(templateAddress).supportsInterface(
                type(IGenericStrategy).interfaceId
            ),
            "Template does not implement IGenericStrategy"
        );
        
        strategyTemplates[strategyType] = templateAddress;
        strategyTypes.push(strategyType);
        
        emit StrategyTemplateAdded(strategyType, templateAddress);
    }
    
    /**
     * @dev Remove a strategy template
     * @param strategyType Type identifier for the strategy
     */
    function removeStrategyTemplate(string calldata strategyType) 
        external 
        onlyRole(STRATEGY_MANAGER_ROLE) 
    {
        require(strategyTemplates[strategyType] != address(0), "Template does not exist");
        
        delete strategyTemplates[strategyType];
        
        // Remove from strategyTypes array
        for (uint256 i = 0; i < strategyTypes.length; i++) {
            if (keccak256(bytes(strategyTypes[i])) == keccak256(bytes(strategyType))) {
                // Replace with the last element and pop
                strategyTypes[i] = strategyTypes[strategyTypes.length - 1];
                strategyTypes.pop();
                break;
            }
        }
        
        emit StrategyTemplateRemoved(strategyType);
    }
    
    /**
     * @dev Create a new strategy
     * @param strategyType Type identifier for the strategy
     * @param initData Initialization data for the strategy
     * @return strategyId Unique identifier for the created strategy
     * @return strategyAddress Address of the created strategy
     */
    function createStrategy(
        string calldata strategyType,
        bytes calldata initData
    ) 
        external 
        nonReentrant 
        whenNotPaused 
        onlyRole(STRATEGY_CREATOR_ROLE) 
        returns (bytes32 strategyId, address strategyAddress) 
    {
        address templateAddress = strategyTemplates[strategyType];
        require(templateAddress != address(0), "Strategy template not found");
        
        // Generate strategy ID
        strategyId = keccak256(
            abi.encodePacked(
                strategyType,
                msg.sender,
                block.timestamp,
                initData
            )
        );
        
        // Check if strategy ID already exists
        require(strategies[strategyId].strategyAddress == address(0), "Strategy ID already exists");
        
        // Clone the template
        strategyAddress = templateAddress.clone();
        
        // Initialize the strategy
        IGenericStrategy(strategyAddress).initialize(initData);
        
        // Store strategy info
        strategies[strategyId] = StrategyInfo({
            strategyAddress: strategyAddress,
            strategyType: strategyType,
            creator: msg.sender,
            createdAt: block.timestamp,
            active: false,
            configHash: keccak256(initData)
        });
        
        strategyIds.push(strategyId);
        
        emit StrategyCreated(strategyId, strategyType, strategyAddress, msg.sender);
        
        return (strategyId, strategyAddress);
    }
    
    /**
     * @dev Activate a strategy
     * @param strategyId ID of the strategy to activate
     */
    function activateStrategy(bytes32 strategyId) 
        external 
        onlyRole(STRATEGY_MANAGER_ROLE) 
    {
        StrategyInfo storage strategy = strategies[strategyId];
        require(strategy.strategyAddress != address(0), "Strategy not found");
        require(!strategy.active, "Strategy already active");
        
        strategy.active = true;
        
        emit StrategyActivated(strategyId, msg.sender);
    }
    
    /**
     * @dev Deactivate a strategy
     * @param strategyId ID of the strategy to deactivate
     */
    function deactivateStrategy(bytes32 strategyId) 
        external 
        onlyRole(STRATEGY_MANAGER_ROLE) 
    {
        StrategyInfo storage strategy = strategies[strategyId];
        require(strategy.strategyAddress != address(0), "Strategy not found");
        require(strategy.active, "Strategy already inactive");
        
        strategy.active = false;
        
        emit StrategyDeactivated(strategyId, msg.sender);
    }
    
    /**
     * @dev Approve a strategy for execution
     * @param strategyId ID of the strategy to approve
     */
    function approveStrategy(bytes32 strategyId) 
        external 
        onlyRole(STRATEGY_MANAGER_ROLE) 
    {
        require(strategies[strategyId].strategyAddress != address(0), "Strategy not found");
        require(!approvedStrategies[strategyId], "Strategy already approved");
        
        approvedStrategies[strategyId] = true;
        
        emit StrategyApproved(strategyId, msg.sender);
    }
    
    /**
     * @dev Reject a strategy
     * @param strategyId ID of the strategy to reject
     */
    function rejectStrategy(bytes32 strategyId) 
        external 
        onlyRole(STRATEGY_MANAGER_ROLE) 
    {
        require(strategies[strategyId].strategyAddress != address(0), "Strategy not found");
        require(approvedStrategies[strategyId], "Strategy not approved");
        
        approvedStrategies[strategyId] = false;
        
        emit StrategyRejected(strategyId, msg.sender);
    }
    
    /**
     * @dev Emergency pause function
     */
    function emergencyPause() 
        external 
        onlyRole(EMERGENCY_ADMIN_ROLE) 
    {
        _pause();
    }
    
    /**
     * @dev Emergency unpause function
     */
    function emergencyUnpause() 
        external 
        onlyRole(EMERGENCY_ADMIN_ROLE) 
    {
        _unpause();
    }
    
    /**
     * @dev Get strategy info
     * @param strategyId ID of the strategy
     * @return Strategy info
     */
    function getStrategyInfo(bytes32 strategyId) 
        external 
        view 
        returns (StrategyInfo memory) 
    {
        return strategies[strategyId];
    }
    
    /**
     * @dev Get all strategy types
     * @return Array of strategy types
     */
    function getAllStrategyTypes() 
        external 
        view 
        returns (string[] memory) 
    {
        return strategyTypes;
    }
    
    /**
     * @dev Get all strategy IDs
     * @return Array of strategy IDs
     */
    function getAllStrategyIds() 
        external 
        view 
        returns (bytes32[] memory) 
    {
        return strategyIds;
    }
    
    /**
     * @dev Get active strategies
     * @return Array of active strategy IDs
     */
    function getActiveStrategies() 
        external 
        view 
        returns (bytes32[] memory) 
    {
        uint256 activeCount = 0;
        
        // Count active strategies
        for (uint256 i = 0; i < strategyIds.length; i++) {
            if (strategies[strategyIds[i]].active) {
                activeCount++;
            }
        }
        
        // Create array of active strategy IDs
        bytes32[] memory activeStrategyIds = new bytes32[](activeCount);
        uint256 index = 0;
        
        for (uint256 i = 0; i < strategyIds.length; i++) {
            if (strategies[strategyIds[i]].active) {
                activeStrategyIds[index] = strategyIds[i];
                index++;
            }
        }
        
        return activeStrategyIds;
    }
    
    /**
     * @dev Get approved strategies
     * @return Array of approved strategy IDs
     */
    function getApprovedStrategies() 
        external 
        view 
        returns (bytes32[] memory) 
    {
        uint256 approvedCount = 0;
        
        // Count approved strategies
        for (uint256 i = 0; i < strategyIds.length; i++) {
            if (approvedStrategies[strategyIds[i]]) {
                approvedCount++;
            }
        }
        
        // Create array of approved strategy IDs
        bytes32[] memory approvedStrategyIds = new bytes32[](approvedCount);
        uint256 index = 0;
        
        for (uint256 i = 0; i < strategyIds.length; i++) {
            if (approvedStrategies[strategyIds[i]]) {
                approvedStrategyIds[index] = strategyIds[i];
                index++;
            }
        }
        
        return approvedStrategyIds;
    }
    
    /**
     * @dev Check if a strategy is valid for execution
     * @param strategyId ID of the strategy to check
     * @return True if the strategy is valid for execution
     */
    function isValidStrategy(bytes32 strategyId) 
        external 
        view 
        returns (bool) 
    {
        return strategies[strategyId].active && approvedStrategies[strategyId];
    }
}