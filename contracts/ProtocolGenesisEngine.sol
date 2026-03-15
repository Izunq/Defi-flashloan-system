// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/proxy/Clones.sol";
import "./SelfAmendingProtocol.sol";

/**
 * @title ProtocolGenesisEngine
 * @notice Factory for creating new DeFi protocols based on AI-identified market inefficiencies
 * @dev Part of the V47 Protocol Genesis Engine architecture
 */
contract ProtocolGenesisEngine is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;
    using Clones for address;

    // Role definitions
    bytes32 public constant GENESIS_ADMIN_ROLE = keccak256("GENESIS_ADMIN_ROLE");
    bytes32 public constant PROTOCOL_CREATOR_ROLE = keccak256("PROTOCOL_CREATOR_ROLE");
    bytes32 public constant TREASURY_MANAGER_ROLE = keccak256("TREASURY_MANAGER_ROLE");

    // Protocol types
    enum ProtocolType {
        DEX,
        LendingProtocol,
        Derivatives,
        Yield,
        Insurance,
        Stablecoin,
        AssetManagement,
        Other
    }

    // Protocol template struct
    struct ProtocolTemplate {
        address implementation;
        string name;
        string description;
        ProtocolType protocolType;
        bool isActive;
    }

    // Protocol instance struct
    struct ProtocolInstance {
        address contractAddress;
        string name;
        string description;
        ProtocolType protocolType;
        uint256 createdAt;
        address creator;
        uint256 treasuryAllocation;
        bool isActive;
    }

    // Protocol template mapping
    mapping(uint256 => ProtocolTemplate) public protocolTemplates;
    uint256 public templateCount;

    // Protocol instance mapping
    mapping(uint256 => ProtocolInstance) public protocolInstances;
    uint256 public instanceCount;

    // Treasury configuration
    address public treasuryAddress;
    uint256 public maxTreasuryAllocationPerProtocol;
    uint256 public totalTreasuryAllocated;

    // Self-amending protocol reference
    SelfAmendingProtocol public selfAmendingProtocol;

    // Events
    event TemplateRegistered(
        uint256 indexed templateId,
        address indexed implementation,
        string name,
        ProtocolType protocolType
    );

    event TemplateUpdated(
        uint256 indexed templateId,
        address indexed implementation,
        string name,
        ProtocolType protocolType,
        bool isActive
    );

    event ProtocolCreated(
        uint256 indexed instanceId,
        address indexed contractAddress,
        string name,
        ProtocolType protocolType,
        address indexed creator,
        uint256 treasuryAllocation
    );

    event ProtocolUpdated(
        uint256 indexed instanceId,
        address indexed contractAddress,
        bool isActive
    );

    event TreasuryAllocationChanged(
        uint256 oldAllocation,
        uint256 newAllocation
    );

    event TreasuryAddressChanged(
        address oldTreasury,
        address newTreasury
    );

    /**
     * @dev Constructor
     * @param _treasuryAddress Address of the treasury
     * @param _selfAmendingProtocolAddress Address of the SelfAmendingProtocol contract
     */
    constructor(address _treasuryAddress, address _selfAmendingProtocolAddress) {
        require(_treasuryAddress != address(0), "Invalid treasury address");
        require(_selfAmendingProtocolAddress != address(0), "Invalid SelfAmendingProtocol address");
        
        treasuryAddress = _treasuryAddress;
        selfAmendingProtocol = SelfAmendingProtocol(_selfAmendingProtocolAddress);
        
        // Set default max treasury allocation (5% of treasury)
        maxTreasuryAllocationPerProtocol = 5;
        
        // Setup roles
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), msg.sender);
        _grantRole(GENESIS_ADMIN_ROLE, msg.sender);
        _grantRole(PROTOCOL_CREATOR_ROLE, msg.sender);
        _grantRole(TREASURY_MANAGER_ROLE, msg.sender);
    }
    
    /**
     * @dev Register a new protocol template
     * @param _implementation Address of the implementation contract
     * @param _name Name of the protocol template
     * @param _description Description of the protocol template
     * @param _protocolType Type of the protocol
     */
    function registerTemplate(
        address _implementation,
        string memory _name,
        string memory _description,
        ProtocolType _protocolType
    ) external onlyRole(GENESIS_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_implementation != address(0), "Invalid implementation address");
        require(bytes(_name).length > 0, "Name cannot be empty");
        
        uint256 templateId = templateCount++;
        
        protocolTemplates[templateId] = ProtocolTemplate({
            implementation: _implementation,
            name: _name,
            description: _description,
            protocolType: _protocolType,
            isActive: true
        });
        
        emit TemplateRegistered(
            templateId,
            _implementation,
            _name,
            _protocolType
        );
    }
    
    /**
     * @dev Update a protocol template
     * @param _templateId ID of the template to update
     * @param _implementation New implementation address
     * @param _name New name
     * @param _description New description
     * @param _protocolType New protocol type
     * @param _isActive Whether the template is active
     */
    function updateTemplate(
        uint256 _templateId,
        address _implementation,
        string memory _name,
        string memory _description,
        ProtocolType _protocolType,
        bool _isActive
    ) external onlyRole(GENESIS_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_templateId < templateCount, "Template does not exist");
        require(_implementation != address(0), "Invalid implementation address");
        require(bytes(_name).length > 0, "Name cannot be empty");
        
        ProtocolTemplate storage template = protocolTemplates[_templateId];
        
        template.implementation = _implementation;
        template.name = _name;
        template.description = _description;
        template.protocolType = _protocolType;
        template.isActive = _isActive;
        
        emit TemplateUpdated(
            _templateId,
            _implementation,
            _name,
            _protocolType,
            _isActive
        );
    }
    
    /**
     * @dev Create a new protocol instance from a template
     * @param _templateId ID of the template to use
     * @param _name Name of the protocol instance
     * @param _description Description of the protocol instance
     * @param _treasuryAllocationPercentage Percentage of treasury to allocate (in basis points)
     * @param _initData Initialization data for the protocol
     * @return instanceId ID of the created protocol instance
     */
    function createProtocol(
        uint256 _templateId,
        string memory _name,
        string memory _description,
        uint256 _treasuryAllocationPercentage,
        bytes memory _initData
    ) external onlyRole(PROTOCOL_CREATOR_ROLE) nonReentrant returns (uint256 instanceId) {
        require(_templateId < templateCount, "Template does not exist");
        require(protocolTemplates[_templateId].isActive, "Template is not active");
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(_treasuryAllocationPercentage <= maxTreasuryAllocationPerProtocol, "Allocation exceeds maximum");
        
        ProtocolTemplate storage template = protocolTemplates[_templateId];
        
        // Clone the implementation
        address clonedProtocol = Clones.clone(template.implementation);
        
        // Initialize the protocol
        (bool success, ) = clonedProtocol.call(_initData);
        require(success, "Protocol initialization failed");
        
        // Calculate treasury allocation
        uint256 treasuryBalance = IERC20(treasuryAddress).balanceOf(address(this));
        uint256 allocation = (treasuryBalance * _treasuryAllocationPercentage) / 10000;
        
        // Update total allocation
        totalTreasuryAllocated += allocation;
        
        // Create protocol instance
        instanceId = instanceCount++;
        
        protocolInstances[instanceId] = ProtocolInstance({
            contractAddress: clonedProtocol,
            name: _name,
            description: _description,
            protocolType: template.protocolType,
            createdAt: block.timestamp,
            creator: msg.sender,
            treasuryAllocation: allocation,
            isActive: true
        });
        
        // Transfer funds to the protocol
        if (allocation > 0) {
            IERC20(treasuryAddress).safeTransfer(clonedProtocol, allocation);
        }
        
        // Register the protocol with the SelfAmendingProtocol
        selfAmendingProtocol.registerContract(clonedProtocol, _name);
        
        emit ProtocolCreated(
            instanceId,
            clonedProtocol,
            _name,
            template.protocolType,
            msg.sender,
            allocation
        );
        
        return instanceId;
    }
    
    /**
     * @dev Update a protocol instance
     * @param _instanceId ID of the instance to update
     * @param _isActive Whether the instance is active
     */
    function updateProtocolStatus(uint256 _instanceId, bool _isActive) external onlyRole(GENESIS_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_instanceId < instanceCount, "Instance does not exist");
        
        ProtocolInstance storage instance = protocolInstances[_instanceId];
        instance.isActive = _isActive;
        
        emit ProtocolUpdated(
            _instanceId,
            instance.contractAddress,
            _isActive
        );
    }
    
    /**
     * @dev Update the maximum treasury allocation per protocol
     * @param _newMaxAllocation New maximum allocation (in basis points)
     */
    function updateMaxTreasuryAllocation(uint256 _newMaxAllocation) external onlyRole(TREASURY_MANAGER_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_newMaxAllocation <= 10000, "Allocation cannot exceed 100%");
        
        uint256 oldAllocation = maxTreasuryAllocationPerProtocol;
        maxTreasuryAllocationPerProtocol = _newMaxAllocation;
        
        emit TreasuryAllocationChanged(oldAllocation, _newMaxAllocation);
    }
    
    /**
     * @dev Update the treasury address
     * @param _newTreasuryAddress New treasury address
     */
    function updateTreasuryAddress(address _newTreasuryAddress) external onlyRole(TREASURY_MANAGER_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_newTreasuryAddress != address(0), "Invalid treasury address");
        
        address oldTreasury = treasuryAddress;
        treasuryAddress = _newTreasuryAddress;
        
        emit TreasuryAddressChanged(oldTreasury, _newTreasuryAddress);
    }
    
    /**
     * @dev Get the number of protocol templates
     * @return The number of templates
     */
    function getTemplateCount() external view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        return templateCount;
    }
    
    /**
     * @dev Get the number of protocol instances
     * @return The number of instances
     */
    function getInstanceCount() external view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        return instanceCount;
    }
    
    /**
     * @dev Get all active protocol instances
     * @return instanceIds Array of active instance IDs
     */
    function getActiveProtocols() external view returns (uint256[] memory instanceIds)  {
        // TODO: Add nonReentrant modifier
        uint256 activeCount = 0;
        
        // Count active instances
        for (uint256 i = 0; i < instanceCount; i++) {
            if (protocolInstances[i].isActive) {
                activeCount++;
            }
        }
        
        // Create array of active instance IDs
        instanceIds = new uint256[](activeCount);
        uint256 index = 0;
        
        for (uint256 i = 0; i < instanceCount; i++) {
            if (protocolInstances[i].isActive) {
                instanceIds[index++] = i;
            }
        }
        
        return instanceIds;
    }
    
    /**
     * @dev Get protocols by type
     * @param _protocolType Type of protocols to get
     * @return instanceIds Array of instance IDs of the specified type
     */
    function getProtocolsByType(ProtocolType _protocolType) external view returns (uint256[] memory instanceIds)  {
        // TODO: Add nonReentrant modifier
        uint256 typeCount = 0;
        
        // Count instances of the specified type
        for (uint256 i = 0; i < instanceCount; i++) {
            if (protocolInstances[i].protocolType == _protocolType) {
                typeCount++;
            }
        }
        
        // Create array of instance IDs of the specified type
        instanceIds = new uint256[](typeCount);
        uint256 index = 0;
        
        for (uint256 i = 0; i < instanceCount; i++) {
            if (protocolInstances[i].protocolType == _protocolType) {
                instanceIds[index++] = i;
            }
        }
        
        return instanceIds;
    }
    
    /**
     * @dev Get detailed information about a protocol instance
     * @param _instanceId ID of the instance
     * @return instance The protocol instance
     */
    function getProtocolDetails(uint256 _instanceId) external view returns (ProtocolInstance memory)  {
        // TODO: Add nonReentrant modifier
        require(_instanceId < instanceCount, "Instance does not exist");
        return protocolInstances[_instanceId];
    }
}
