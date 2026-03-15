// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "./CrossChainSecurityValidator.sol";
import "./InputValidator.sol";

/**
 * @title EnhancedInterChainCognitiveMesh
 * @notice Enhanced cross-chain operations coordinator with comprehensive security
 * @dev Integrates with CrossChainSecurityValidator for maximum security
 */
contract EnhancedInterChainCognitiveMesh is AccessControl, ReentrancyGuard {
    using ECDSA for bytes32;
    using InputValidator for uint256;
    using InputValidator for address;

    // Role definitions
    bytes32 public constant MESH_ADMIN_ROLE = keccak256("MESH_ADMIN_ROLE");
    bytes32 public constant BRIDGE_OPERATOR_ROLE = keccak256("BRIDGE_OPERATOR_ROLE");
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");

    // Enhanced chain information
    struct ChainInfo {
        uint256 chainId;
        string name;
        address meshEndpoint;
        bool isActive;
        uint256 lastSyncTimestamp;
        uint256 blockConfirmations;
        uint256 gasPrice;
        uint256 maxGasPrice;
        bool isPaused;
        mapping(bytes32 => bool) executedOperations;
    }

    // Operation status with additional security states
    enum OperationStatus {
        Pending,
        Validating,
        Validated,
        InProgress,
        Completed,
        Failed,
        Cancelled,
        Expired
    }

    // Enhanced cross-chain operation
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
        uint256 validatedAt;
        uint256 executedAt;
        bytes result;
        uint256 securityScore;
        bool requiresMultiSig;
    }

    // Security checkpoint
    struct SecurityCheckpoint {
        bytes32 operationId;
        uint256 timestamp;
        address validator;
        bool passed;
        string reason;
    }

    // Multi-signature requirement
    struct MultiSigRequirement {
        bytes32 operationId;
        address[] signers;
        mapping(address => bool) hasSigned;
        uint256 requiredSignatures;
        uint256 currentSignatures;
        bool isComplete;
    }

    // Emergency controls
    struct EmergencyControls {
        bool globalPause;
        bool crossChainPause;
        uint256 pausedUntil;
        address pausedBy;
        string reason;
    }

    // Contract references
    CrossChainSecurityValidator public immutable securityValidator;
    
    // State variables
    mapping(uint256 => ChainInfo) public chains;
    mapping(bytes32 => CrossChainOperation) public operations;
    mapping(bytes32 => SecurityCheckpoint[]) public securityCheckpoints;
    mapping(bytes32 => MultiSigRequirement) public multiSigRequirements;
    
    // Arrays for iteration
    uint256[] public chainIds;
    bytes32[] public pendingOperations;
    bytes32[] public validatingOperations;
    
    // Counters and configuration
    uint256 public chainCount;
    uint256 public operationCount;
    uint256 public operationTimeout = 1 hours;
    uint256 public maxGasPrice = 500 gwei;
    uint256 public minConfirmations = 12;
    uint256 public maxOperationsPerCleanup = 50;
    uint256 public cleanupGasLimit = 2000000;
    
    // Emergency controls
    EmergencyControls public emergencyControls;
    
    // Enhanced events
    event ChainRegistered(
        uint256 indexed chainId,
        string name,
        address meshEndpoint,
        uint256 blockConfirmations
    );
    
    event OperationCreated(
        bytes32 indexed operationId,
        uint256 indexed sourceChainId,
        uint256 indexed targetChainId,
        address initiator,
        uint256 value,
        uint256 deadline
    );
    
    event OperationValidated(
        bytes32 indexed operationId,
        uint256 securityScore,
        bool requiresMultiSig,
        uint256 timestamp
    );
    
    event SecurityCheckpointAdded(
        bytes32 indexed operationId,
        address validator,
        bool passed,
        string reason
    );
    
    event MultiSigSignatureAdded(
        bytes32 indexed operationId,
        address signer,
        uint256 currentSignatures,
        uint256 requiredSignatures
    );
    
    event EmergencyPauseActivated(
        address indexed activatedBy,
        string reason,
        uint256 pausedUntil
    );
    
    event SuspiciousActivityDetected(
        bytes32 indexed operationId,
        string activityType,
        address reporter,
        uint256 timestamp
    );

    // Custom errors
    error OperationNotFound(bytes32 operationId);
    error InvalidOperationStatus(OperationStatus current, OperationStatus required);
    error SecurityValidationFailed(string reason);
    error InsufficientMultiSigSignatures(uint256 current, uint256 required);
    error EmergencyPauseActive(string reason);
    error ChainPaused(uint256 chainId);
    error OperationExpired(bytes32 operationId, uint256 deadline);

    modifier whenNotPaused() {
        if (emergencyControls.globalPause || emergencyControls.crossChainPause) {
            if (block.timestamp < emergencyControls.pausedUntil) {
                revert EmergencyPauseActive(emergencyControls.reason);
            }
        }
        _;
    }

    modifier validChain(uint256 chainId) {
        require(chains[chainId].chainId != 0, "Chain not registered");
        if (chains[chainId].isPaused) {
            revert ChainPaused(chainId);
        }
        _;
    }

    modifier operationExists(bytes32 operationId) {
        if (operations[operationId].operationId == bytes32(0)) {
            revert OperationNotFound(operationId);
        }
        _;
    }

    constructor(address _securityValidator) {
        require(_securityValidator != address(0), "Invalid validator address");
        
        securityValidator = CrossChainSecurityValidator(_securityValidator);
        
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), msg.sender);
        _grantRole(MESH_ADMIN_ROLE, msg.sender);
        _grantRole(EMERGENCY_ROLE, msg.sender);
    }

    /**
     * @notice Register a new chain with enhanced security parameters
     * @param _chainId Chain ID
     * @param _name Chain name
     * @param _meshEndpoint Mesh endpoint address
     * @param _blockConfirmations Required block confirmations
     * @param _maxGasPrice Maximum gas price for the chain
     */
    function registerChain(
        uint256 _chainId,
        string memory _name,
        address _meshEndpoint,
        uint256 _blockConfirmations,
        uint256 _maxGasPrice
    ) external onlyRole(MESH_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        InputValidator.requireValidAddress(_meshEndpoint);
        InputValidator.requireInRange(_blockConfirmations, 1, 100);
        InputValidator.requireInRange(_maxGasPrice, 1 gwei, 2000 gwei);
        
        require(chains[_chainId].chainId == 0, "Chain already registered");
        require(bytes(_name).length > 0, "Chain name required");
        
        ChainInfo storage chain = chains[_chainId];
        chain.chainId = _chainId;
        chain.name = _name;
        chain.meshEndpoint = _meshEndpoint;
        chain.isActive = true;
        chain.blockConfirmations = _blockConfirmations;
        chain.maxGasPrice = _maxGasPrice;
        chain.isPaused = false;
        
        chainIds.push(_chainId);
        chainCount++;
        
        emit ChainRegistered(_chainId, _name, _meshEndpoint, _blockConfirmations);
    }

    /**
     * @notice Create a cross-chain operation with enhanced security validation
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
    ) external payable nonReentrant whenNotPaused validChain(_targetChainId) returns (bytes32 operationId)  {
        // TODO: Add nonReentrant modifier
        InputValidator.requireInRange(_gasLimit, 21000, 30000000);
        require(_deadline > block.timestamp, "Deadline must be in the future");
        require(_deadline <= block.timestamp + operationTimeout, "Deadline too far in future");
        
        operationId = keccak256(abi.encodePacked(
            block.chainid,
            _targetChainId,
            msg.sender,
            operationCount,
            block.timestamp,
            _payload
        ));
        
        // Initial security validation
        try securityValidator.validateCrossChainMessage(
            operationId,
            block.chainid,
            _targetChainId,
            msg.sender,
            _payload,
            msg.value,
            new CrossChainSecurityValidator.OracleSignature[](0) // Empty for initial validation
        ) returns (bool) {
            // Security validation passed
        } catch (bytes memory reason) {
            revert SecurityValidationFailed(string(reason));
        }
        
        // Determine if multi-sig is required
        bytes4 functionSelector = bytes4(_payload[:4]);
        bool requiresMultiSig = _checkMultiSigRequirement(functionSelector, msg.value);
        
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
            validatedAt: 0,
            executedAt: 0,
            result: new bytes(0),
            securityScore: 50, // Initial score
            requiresMultiSig: requiresMultiSig
        });
        
        if (requiresMultiSig) {
            _initializeMultiSig(operationId);
        }
        
        pendingOperations.push(operationId);
        operationCount++;
        
        emit OperationCreated(
            operationId,
            block.chainid,
            _targetChainId,
            msg.sender,
            msg.value,
            _deadline
        );
        
        return operationId;
    }

    /**
     * @notice Validate operation with oracle signatures
     * @param _operationId Operation ID
     * @param _signatures Array of oracle signatures
     */
    function validateOperation(
        bytes32 _operationId,
        CrossChainSecurityValidator.OracleSignature[] calldata _signatures
    ) external onlyRole(ORACLE_ROLE) operationExists(_operationId)  {
        // TODO: Add nonReentrant modifier
        CrossChainOperation storage operation = operations[_operationId];
        
        if (operation.status != OperationStatus.Pending) {
            revert InvalidOperationStatus(operation.status, OperationStatus.Pending);
        }
        
        if (block.timestamp > operation.deadline) {
            operation.status = OperationStatus.Expired;
            revert OperationExpired(_operationId, operation.deadline);
        }
        
        // Comprehensive security validation
        try securityValidator.validateCrossChainMessage(
            _operationId,
            operation.sourceChainId,
            operation.targetChainId,
            operation.initiator,
            operation.payload,
            operation.value,
            _signatures
        ) returns (bool) {
            operation.status = OperationStatus.Validated;
            operation.validatedAt = block.timestamp;
            operation.securityScore = _calculateSecurityScore(operation);
            
            // Add security checkpoint
            _addSecurityCheckpoint(_operationId, msg.sender, true, "Oracle validation passed");
            
            // Move to validating operations array
            _moveToValidating(_operationId);
            
            emit OperationValidated(
                _operationId,
                operation.securityScore,
                operation.requiresMultiSig,
                block.timestamp
            );
        } catch (bytes memory reason) {
            operation.status = OperationStatus.Failed;
            _addSecurityCheckpoint(_operationId, msg.sender, false, string(reason));
            revert SecurityValidationFailed(string(reason));
        }
    }

    /**
     * @notice Execute a validated cross-chain operation
     * @param _operationId Operation ID
     * @param _finalSignatures Final execution signatures
     */
    function executeOperation(
        bytes32 _operationId,
        bytes[] calldata _finalSignatures
    ) external onlyRole(EXECUTOR_ROLE) nonReentrant operationExists(_operationId) {
        CrossChainOperation storage operation = operations[_operationId];
        
        if (operation.status != OperationStatus.Validated) {
            revert InvalidOperationStatus(operation.status, OperationStatus.Validated);
        }
        
        if (block.timestamp > operation.deadline) {
            operation.status = OperationStatus.Expired;
            revert OperationExpired(_operationId, operation.deadline);
        }
        
        // Check multi-sig requirements if needed
        if (operation.requiresMultiSig) {
            _validateMultiSigComplete(_operationId);
        }
        
        // Final security checks
        require(securityValidator.isChainHealthy(operation.sourceChainId), "Source chain unhealthy");
        require(securityValidator.isChainHealthy(operation.targetChainId), "Target chain unhealthy");
        
        // Mark operation as in progress
        operation.status = OperationStatus.InProgress;
        
        // Execute the operation with enhanced error handling
        bool success;
        bytes memory result;
        
        try this.safeExecuteCall{value: operation.value}(operation.payload) returns (bytes memory _result) {
            success = true;
            result = _result;
        } catch Error(string memory reason) {
            success = false;
            result = bytes(reason);
        } catch (bytes memory lowLevelData) {
            success = false;
            result = lowLevelData;
        }
        
        // Update operation status
        operation.status = success ? OperationStatus.Completed : OperationStatus.Failed;
        operation.executedAt = block.timestamp;
        operation.result = result;
        
        // Mark as executed on source chain
        chains[operation.sourceChainId].executedOperations[_operationId] = true;
        
        // Remove from pending operations
        _removePendingOperation(_operationId);
        
        // Add final security checkpoint
        _addSecurityCheckpoint(
            _operationId,
            msg.sender,
            success,
            success ? "Execution completed" : "Execution failed"
        );
        
        emit OperationStatusChanged(_operationId, operation.status, block.timestamp);
        emit OperationExecuted(_operationId, block.chainid, success, result);
    }

    /**
     * @notice Add multi-sig signature for operation
     * @param _operationId Operation ID
     */
    function addMultiSigSignature(
        bytes32 _operationId
    ) external operationExists(_operationId)  {
        // TODO: Add nonReentrant modifier
        MultiSigRequirement storage multiSig = multiSigRequirements[_operationId];
        
        require(!multiSig.isComplete, "Multi-sig already complete");
        require(!multiSig.hasSigned[msg.sender], "Already signed");
        
        // Verify signer is authorized
        bool isAuthorized = false;
        for (uint256 i = 0; i < multiSig.signers.length; i++) {
            if (multiSig.signers[i] == msg.sender) {
                isAuthorized = true;
                break;
            }
        }
        require(isAuthorized, "Not authorized to sign");
        
        multiSig.hasSigned[msg.sender] = true;
        multiSig.currentSignatures++;
        
        if (multiSig.currentSignatures >= multiSig.requiredSignatures) {
            multiSig.isComplete = true;
        }
        
        emit MultiSigSignatureAdded(
            _operationId,
            msg.sender,
            multiSig.currentSignatures,
            multiSig.requiredSignatures
        );
    }

    /**
     * @notice Emergency pause all operations
     * @param _reason Reason for pause
     * @param _duration Duration of pause in seconds
     */
    function emergencyPause(
        string calldata _reason,
        uint256 _duration
    ) external onlyRole(EMERGENCY_ROLE)  {
        // TODO: Add nonReentrant modifier
        emergencyControls.globalPause = true;
        emergencyControls.crossChainPause = true;
        emergencyControls.pausedUntil = block.timestamp + _duration;
        emergencyControls.pausedBy = msg.sender;
        emergencyControls.reason = _reason;
        
        emit EmergencyPauseActivated(msg.sender, _reason, emergencyControls.pausedUntil);
    }

    /**
     * @notice Safe call execution with gas limits
     * @param _payload Call payload
     * @return result Call result
     */
    function safeExecuteCall(bytes calldata _payload) external payable returns (bytes memory result)  {
        // TODO: Add nonReentrant modifier
        require(msg.sender == address(this), "Only self-call allowed");
        
        (bool success, bytes memory returnData) = address(this).call{
            value: msg.value,
            gas: gasleft() * 63 / 64 // Leave 1/64 for return
        }(_payload);
        
        if (!success) {
            assembly {
                revert(add(returnData, 32), mload(returnData))
            }
        }
        
        return returnData;
    }

    // Internal helper functions
    
    function _checkMultiSigRequirement(bytes4 _selector, uint256 _value) internal pure returns (bool) {
        // High-value operations require multi-sig
        if (_value > 10 ether) return true;
        
        // Sensitive functions require multi-sig
        if (_selector == bytes4(keccak256("emergencyWithdraw(address,uint256)"))) return true;
        if (_selector == bytes4(keccak256("updateConfiguration(bytes)"))) return true;
        
        return false;
    }
    
    function _initializeMultiSig(bytes32 _operationId) internal {
        MultiSigRequirement storage multiSig = multiSigRequirements[_operationId];
        
        // Default signers (should be configurable)
        multiSig.signers = new address[](3);
        multiSig.signers[0] = 0x1234567890123456789012345678901234567890; // Placeholder
        multiSig.signers[1] = 0x2345678901234567890123456789012345678901; // Placeholder  
        multiSig.signers[2] = 0x3456789012345678901234567890123456789012; // Placeholder
        
        multiSig.requiredSignatures = 2; // 2 of 3
        multiSig.currentSignatures = 0;
        multiSig.isComplete = false;
    }
    
    function _validateMultiSigComplete(bytes32 _operationId) internal view {
        MultiSigRequirement storage multiSig = multiSigRequirements[_operationId];
        
        if (!multiSig.isComplete) {
            revert InsufficientMultiSigSignatures(
                multiSig.currentSignatures,
                multiSig.requiredSignatures
            );
        }
    }
    
    function _calculateSecurityScore(CrossChainOperation memory _operation) internal view returns (uint256) {
        uint256 score = 50; // Base score
        
        // Higher score for validated operations
        if (_operation.validatedAt > 0) score += 20;
        
        // Lower score for high-value operations
        if (_operation.value > 100 ether) score -= 10;
        
        // Higher score for known good initiators (placeholder logic)
        if (_operation.initiator != address(0)) score += 10;
        
        return score > 100 ? 100 : score;
    }
    
    function _addSecurityCheckpoint(
        bytes32 _operationId,
        address _validator,
        bool _passed,
        string memory _reason
    ) internal {
        securityCheckpoints[_operationId].push(SecurityCheckpoint({
            operationId: _operationId,
            timestamp: block.timestamp,
            validator: _validator,
            passed: _passed,
            reason: _reason
        }));
        
        emit SecurityCheckpointAdded(_operationId, _validator, _passed, _reason);
    }
    
    function _moveToValidating(bytes32 _operationId) internal {
        validatingOperations.push(_operationId);
        _removePendingOperation(_operationId);
    }
    
    function _removePendingOperation(bytes32 _operationId) internal {
        uint256 length = pendingOperations.length;
        for (uint256 i = 0; i < length; i++) {
            if (pendingOperations[i] == _operationId) {
                pendingOperations[i] = pendingOperations[length - 1];
                pendingOperations.pop();
                break;
            }
        }
    }

    // View functions for security monitoring
    
    function getOperationSecurityCheckpoints(bytes32 _operationId) 
        external 
        view 
        returns (SecurityCheckpoint[] memory) 
    {
        return securityCheckpoints[_operationId];
    }
    
    function getMultiSigStatus(bytes32 _operationId) 
        external 
        view 
        returns (address[] memory signers, uint256 current, uint256 required, bool complete) 
    {
        MultiSigRequirement storage multiSig = multiSigRequirements[_operationId];
        return (multiSig.signers, multiSig.currentSignatures, multiSig.requiredSignatures, multiSig.isComplete);
    }
    
    function getPendingOperations() external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        return pendingOperations;
    }
    
    function getValidatingOperations() external view returns (bytes32[] memory)  {
        // TODO: Add nonReentrant modifier
        return validatingOperations;
    }

    // Events for compatibility
    event OperationStatusChanged(bytes32 indexed operationId, OperationStatus status, uint256 timestamp);
    event OperationExecuted(bytes32 indexed operationId, uint256 chainId, bool success, bytes result);
}
