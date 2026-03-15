// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/**
 * @title InterChainCognitiveMesh
 * @notice Coordinates cross-chain operations and maintains a unified global state
 * @dev Part of the V48 Inter-Chain Cognitive Mesh architecture
 */
contract InterChainCognitiveMesh is AccessControl, ReentrancyGuard {
    using ECDSA for bytes32;

    // Role definitions
    bytes32 public constant MESH_ADMIN_ROLE = keccak256("MESH_ADMIN_ROLE");
    bytes32 public constant BRIDGE_OPERATOR_ROLE = keccak256("BRIDGE_OPERATOR_ROLE");
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");

    // Chain information
    struct ChainInfo {
        uint256 chainId;
        string name;
        address meshEndpoint;
        bool isActive;
        uint256 lastSyncTimestamp;
        uint256 blockConfirmations;
        uint256 gasPrice;
        mapping(bytes32 => bool) executedOperations;
    }

    // Operation status
    enum OperationStatus {
        Pending,
        InProgress,
        Completed,
        Failed
    }

    // Cross-chain operation
    struct CrossChainOperation {
        bytes32 operationId;
        uint256 sourceChainId;
        uint256 targetChainId;
        address initiator;
        bytes payload;
        uint256 gasLimit;
        uint256 value;
        uint256 deadline;
        OperationStatus status;
        uint256 createdAt;
        uint256 executedAt;
        bytes result;    }

    // Global state entry
    struct GlobalStateEntry {
        bytes32 key;
        bytes value;
        uint256 lastUpdated;
        uint256 updateChainId;
        uint256 version;
    }

    // Mappings
    mapping(uint256 => ChainInfo) public chains;
    mapping(bytes32 => CrossChainOperation) public operations;
    mapping(bytes32 => GlobalStateEntry) public globalState;
    
    // Arrays for iteration
    uint256[] public chainIds;
    bytes32[] public stateKeys;
    bytes32[] public pendingOperations;
    
    // Counters
    uint256 public chainCount;
    uint256 public operationCount;
      // Configuration
    uint256 public operationTimeout = 1 hours;
    uint256 public maxGasPrice = 500 gwei;
    uint256 public minConfirmations = 12;
    
    // Gas griefing protection
    uint256 public constant MAX_OPERATIONS_PER_CLEANUP = 50; // Maximum operations to process per cleanup call
    uint256 public constant MAX_PENDING_OPERATIONS = 1000; // Maximum number of pending operations
    uint256 public cleanupGasLimit = 2000000; // Gas limit for cleanup operations
    
    // Events
    event ChainRegistered(
        uint256 indexed chainId,
        string name,
        address meshEndpoint
    );
    
    event ChainUpdated(
        uint256 indexed chainId,
        address meshEndpoint,
        bool isActive
    );
    
    event OperationCreated(
        bytes32 indexed operationId,
        uint256 indexed sourceChainId,
        uint256 indexed targetChainId,
        address initiator,
        uint256 createdAt
    );
    
    event OperationStatusChanged(
        bytes32 indexed operationId,
        OperationStatus status,
        uint256 timestamp
    );
    
    event OperationExecuted(
        bytes32 indexed operationId,
        uint256 indexed targetChainId,
        bool success,
        bytes result
    );
    
    event GlobalStateUpdated(
        bytes32 indexed key,
        uint256 indexed updateChainId,
        uint256 version,
        uint256 timestamp
    );
    
    event ConfigurationUpdated(
        string parameter,
        uint256 oldValue,
        uint256 newValue
    );
    
    /**
     * @dev Constructor
     */
    constructor() {
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), msg.sender);
        _grantRole(MESH_ADMIN_ROLE, msg.sender);
        
        // Register the current chain
        _registerChain(
            block.chainid,
            "Origin Chain",
            address(this),
            20,
            block.basefee
        );
    }
    
    /**
     * @dev Register a new chain
     * @param _chainId Chain ID
     * @param _name Chain name
     * @param _meshEndpoint Address of the mesh endpoint on the chain
     * @param _blockConfirmations Number of block confirmations required
     * @param _gasPrice Current gas price on the chain
     */
    function registerChain(
        uint256 _chainId,
        string memory _name,
        address _meshEndpoint,
        uint256 _blockConfirmations,
        uint256 _gasPrice
    ) external onlyRole(MESH_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        _registerChain(_chainId, _name, _meshEndpoint, _blockConfirmations, _gasPrice);
    }
    
    /**
     * @dev Internal function to register a chain
     */
    function _registerChain(
        uint256 _chainId,
        string memory _name,
        address _meshEndpoint,
        uint256 _blockConfirmations,
        uint256 _gasPrice
    ) internal {
        require(_chainId > 0, "Invalid chain ID");
        require(_meshEndpoint != address(0), "Invalid mesh endpoint");
        require(chains[_chainId].chainId == 0, "Chain already registered");
        
        chains[_chainId].chainId = _chainId;
        chains[_chainId].name = _name;
        chains[_chainId].meshEndpoint = _meshEndpoint;
        chains[_chainId].isActive = true;
        chains[_chainId].lastSyncTimestamp = block.timestamp;
        chains[_chainId].blockConfirmations = _blockConfirmations;
        chains[_chainId].gasPrice = _gasPrice;
        
        chainIds.push(_chainId);
        chainCount++;
        
        emit ChainRegistered(_chainId, _name, _meshEndpoint);
    }
    
    /**
     * @dev Update chain information
     * @param _chainId Chain ID
     * @param _meshEndpoint New mesh endpoint address
     * @param _isActive Whether the chain is active
     * @param _blockConfirmations New block confirmations
     * @param _gasPrice New gas price
     */
    function updateChain(
        uint256 _chainId,
        address _meshEndpoint,
        bool _isActive,
        uint256 _blockConfirmations,
        uint256 _gasPrice
    ) external onlyRole(MESH_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(chains[_chainId].chainId != 0, "Chain not registered");
        require(_meshEndpoint != address(0), "Invalid mesh endpoint");
        
        chains[_chainId].meshEndpoint = _meshEndpoint;
        chains[_chainId].isActive = _isActive;
        chains[_chainId].blockConfirmations = _blockConfirmations;
        chains[_chainId].gasPrice = _gasPrice;
        
        emit ChainUpdated(_chainId, _meshEndpoint, _isActive);
    }
    
    /**
     * @dev Create a cross-chain operation
     * @param _targetChainId Target chain ID
     * @param _payload Operation payload
     * @param _gasLimit Gas limit for execution
     * @param _deadline Deadline for execution
     * @return operationId ID of the created operation
     */
    function createOperation(
        uint256 _targetChainId,
        bytes memory _payload,
        uint256 _gasLimit,
        uint256 _deadline
    ) external payable nonReentrant returns (bytes32 operationId)  {
        // TODO: Add nonReentrant modifier
        require(chains[_targetChainId].chainId != 0, "Target chain not registered");
        require(chains[_targetChainId].isActive, "Target chain not active");
        require(_deadline > block.timestamp, "Deadline must be in the future");
        require(_gasLimit > 0, "Gas limit must be greater than zero");
        
        operationId = keccak256(abi.encodePacked(
            block.chainid,
            _targetChainId,
            msg.sender,
            operationCount,
            block.timestamp
        ));
        
        operations[operationId] = CrossChainOperation({
            operationId: operationId,
            sourceChainId: block.chainid,
            targetChainId: _targetChainId,
            initiator: msg.sender,
            payload: _payload,
            gasLimit: _gasLimit,
            value: msg.value,
            deadline: _deadline,
            status: OperationStatus.Pending,
            createdAt: block.timestamp,
            executedAt: 0,
            result: new bytes(0)
        });
        
        pendingOperations.push(operationId);
        operationCount++;
        
        emit OperationCreated(
            operationId,
            block.chainid,
            _targetChainId,
            msg.sender,
            block.timestamp
        );
        
        return operationId;
    }
    
    /**
     * @dev Execute a cross-chain operation
     * @param _operationId Operation ID
     * @param _sourceChainId Source chain ID
     * @param _initiator Operation initiator
     * @param _payload Operation payload
     * @param _value Operation value
     * @param _signature Signature from the bridge operator
     */
    function executeOperation(
        bytes32 _operationId,
        uint256 _sourceChainId,
        address _initiator,
        bytes memory _payload,
        uint256 _value,
        bytes memory _signature
    ) external onlyRole(EXECUTOR_ROLE) nonReentrant {
        require(chains[_sourceChainId].chainId != 0, "Source chain not registered");
        require(!chains[_sourceChainId].executedOperations[_operationId], "Operation already executed");
        
        // Verify the signature
        bytes32 messageHash = keccak256(abi.encodePacked(
            _operationId,
            _sourceChainId,
            block.chainid,
            _initiator,
            _payload,
            _value
        ));
        
        bytes32 ethSignedMessageHash = messageHash.toEthSignedMessageHash();
        address signer = ethSignedMessageHash.recover(_signature);
        
        require(hasRole(BRIDGE_OPERATOR_ROLE, signer), "Invalid signature");
        
        // Mark operation as in progress
        operations[_operationId].status = OperationStatus.InProgress;
        emit OperationStatusChanged(_operationId, OperationStatus.InProgress, block.timestamp);
        
        // Execute the operation
        (bool success, bytes memory result) = address(this).call{value: _value}(_payload);
        
        // Update operation status
        operations[_operationId].status = success ? OperationStatus.Completed : OperationStatus.Failed;
        operations[_operationId].executedAt = block.timestamp;
        operations[_operationId].result = result;
        
        // Mark as executed on this chain
        chains[_sourceChainId].executedOperations[_operationId] = true;
        
        // Remove from pending operations
        _removePendingOperation(_operationId);
        
        emit OperationStatusChanged(
            _operationId,
            operations[_operationId].status,
            block.timestamp
        );
        
        emit OperationExecuted(
            _operationId,
            block.chainid,
            success,
            result
        );
    }
    
    /**
     * @dev Update global state
     * @param _key State key
     * @param _value State value
     * @param _signature Signature from the oracle
     */
    function updateGlobalState(
        bytes32 _key,
        bytes memory _value,
        bytes memory _signature
    ) external onlyRole(BRIDGE_OPERATOR_ROLE)  {
        // TODO: Add nonReentrant modifier
        // Verify the signature
        bytes32 messageHash = keccak256(abi.encodePacked(
            _key,
            _value,
            block.chainid,
            block.timestamp
        ));
        
        bytes32 ethSignedMessageHash = messageHash.toEthSignedMessageHash();
        address signer = ethSignedMessageHash.recover(_signature);
        
        require(hasRole(ORACLE_ROLE, signer), "Invalid signature");
        
        // Update or create state entry
        GlobalStateEntry storage entry = globalState[_key];
        
        if (entry.key == bytes32(0)) {
            // New entry
            entry.key = _key;
            stateKeys.push(_key);
        }
        
        entry.value = _value;
        entry.lastUpdated = block.timestamp;
        entry.updateChainId = block.chainid;
        entry.version++;
        
        emit GlobalStateUpdated(
            _key,
            block.chainid,
            entry.version,
            block.timestamp
        );
    }
    
    /**
     * @dev Get global state
     * @param _key State key
     * @return value State value
     * @return lastUpdated Last update timestamp
     * @return updateChainId Chain ID of the last update
     * @return version State version
     */
    function getGlobalState(bytes32 _key) external view returns (
        bytes memory value,
        uint256 lastUpdated,
        uint256 updateChainId,
        uint256 version
    ) {
        GlobalStateEntry storage entry = globalState[_key];
        
        return (
            entry.value,
            entry.lastUpdated,
            entry.updateChainId,
            entry.version
        );
    }
    
    /**
     * @dev Get all global state keys
     * @return Array of state keys
     */
    function getAllStateKeys() external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        return stateKeys;
    }
    
    /**
     * @dev Get all registered chain IDs
     * @return Array of chain IDs
     */
    function getAllChainIds() external view returns (uint256[] memory)  {
        // TODO: Add nonReentrant modifier
        return chainIds;
    }
    
    /**
     * @dev Get all pending operations
     * @return Array of pending operation IDs
     */
    function getPendingOperations() external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        return pendingOperations;
    }
    
    /**
     * @dev Remove a pending operation
     * @param _operationId Operation ID
     */    function _removePendingOperation(bytes32 _operationId) internal {
        uint256 length = pendingOperations.length;
        for (uint256 i = 0; i < length; i++) {
            if (pendingOperations[i] == _operationId) {
                // Replace with the last element and pop
                pendingOperations[i] = pendingOperations[length - 1];
                pendingOperations.pop();
                break;
            }
        }
    }
    
    /**
     * @dev Clean up expired operations
     * @param _maxOperations Maximum number of operations to clean up
     */    function cleanupExpiredOperations(uint256 _maxOperations) external nonReentrant{
        require(_maxOperations <= MAX_OPERATIONS_PER_CLEANUP, "Exceeds maximum operations per cleanup");
        
        uint256 count = 0;
        uint256 i = 0;
        uint256 gasStart = gasleft();
        
        while (i < pendingOperations.length && count < _maxOperations && gasleft() > cleanupGasLimit / 10) {
            bytes32 operationId = pendingOperations[i];
            CrossChainOperation storage operation = operations[operationId];
            
            if (block.timestamp > operation.deadline) {
                // Operation expired
                operation.status = OperationStatus.Failed;
                emit OperationStatusChanged(operationId, OperationStatus.Failed, block.timestamp);
                
                // Replace with the last element and pop
                pendingOperations[i] = pendingOperations[pendingOperations.length - 1];
                pendingOperations.pop();
                
                count++;
            } else {
                i++;
            }
            
            // Circuit breaker: Stop if gas usage is too high
            uint256 gasUsed = gasStart - gasleft();
            if (gasUsed > cleanupGasLimit) {
                break;
            }
        }
    }
    
    /**
     * @dev Update configuration
     * @param _operationTimeout New operation timeout
     * @param _maxGasPrice New maximum gas price
     * @param _minConfirmations New minimum confirmations
     */
    function updateConfiguration(
        uint256 _operationTimeout,
        uint256 _maxGasPrice,
        uint256 _minConfirmations
    ) external onlyRole(MESH_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        if (_operationTimeout != operationTimeout) {
            uint256 oldTimeout = operationTimeout;
            operationTimeout = _operationTimeout;
            emit ConfigurationUpdated("operationTimeout", oldTimeout, _operationTimeout);
        }
        
        if (_maxGasPrice != maxGasPrice) {
            uint256 oldMaxGasPrice = maxGasPrice;
            maxGasPrice = _maxGasPrice;
            emit ConfigurationUpdated("maxGasPrice", oldMaxGasPrice, _maxGasPrice);
        }
        
        if (_minConfirmations != minConfirmations) {
            uint256 oldMinConfirmations = minConfirmations;
            minConfirmations = _minConfirmations;
            emit ConfigurationUpdated("minConfirmations", oldMinConfirmations, _minConfirmations);
        }
    }
    
    /**
     * @dev Receive function to accept ETH
     */
    receive() external payable {}
}
