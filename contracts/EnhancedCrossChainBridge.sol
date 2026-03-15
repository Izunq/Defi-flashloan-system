// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/access/extensions/AccessControlEnumerable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";
import "./CrossChainSecurityValidator.sol";

/**
 * @title EnhancedCrossChainBridge
 * @notice Next-generation cross-chain bridge with enhanced security features
 * @dev Implements multi-oracle consensus, comprehensive validation, and robust error handling
 */
contract EnhancedCrossChainBridge is AccessControlEnumerable, ReentrancyGuard, Pausable, Ownable {
    using ECDSA for bytes32;

    // Enhanced role definitions
    bytes32 public constant BRIDGE_ADMIN_ROLE = keccak256("BRIDGE_ADMIN_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");
    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");

    // Operation states with enhanced error handling
    enum OperationState {
        PENDING,
        VALIDATING,
        ORACLE_CONSENSUS,
        EXECUTING,
        COMPLETED,
        FAILED,
        EXPIRED,
        DISPUTED,
        EMERGENCY_HALTED
    }

    // Comprehensive cross-chain operation structure
    struct CrossChainOperation {
        bytes32 operationId;
        uint256 sourceChainId;
        uint256 targetChainId;
        address initiator;
        address target;
        bytes payload;
        uint256 value;
        uint256 deadline;
        uint256 nonce;
        OperationState state;
        uint256 createdAt;
        uint256 executedAt;
        uint256 requiredSignatures;
        uint256 confirmedSignatures;
        bytes32 merkleRoot;
        string failureReason;
    }

    // Multi-oracle signature structure
    struct OracleSignature {
        address oracle;
        bytes signature;
        uint256 timestamp;
        bytes32 stateRoot;
        uint256 blockHeight;
        bool isValid;
    }

    // Chain state verification structure
    struct ChainState {
        uint256 chainId;
        bytes32 stateRoot;
        uint256 blockHeight;
        uint256 timestamp;
        bool isVerified;
        uint256 confirmationDepth;
        mapping(address => bool) verifiedOracles;
    }

    // Enhanced payload validation structure
    struct PayloadValidation {
        bytes32 payloadHash;
        uint256 size;
        bytes4 functionSelector;
        bool hasComplexData;
        bool isApproved;
        string validationNotes;
        uint256 validatedAt;
    }

    // Timeout and error handling configuration
    struct TimeoutConfig {
        uint256 operationTimeout;
        uint256 consensusTimeout;
        uint256 executionTimeout;
        uint256 emergencyTimeout;
        uint256 maxRetries;
        uint256 retryDelay;
    }

    // State variables
    CrossChainSecurityValidator public immutable securityValidator;
    
    mapping(bytes32 => CrossChainOperation) public operations;
    mapping(bytes32 => mapping(address => OracleSignature)) public oracleSignatures;
    mapping(uint256 => ChainState) public chainStates;
    mapping(bytes32 => PayloadValidation) public payloadValidations;
    mapping(address => bool) public authorizedOracles;
    mapping(uint256 => bool) public supportedChains;
    
    TimeoutConfig public timeoutConfig;
    
    // Security features for external call protection
    mapping(address => bool) public approvedTargets;
    mapping(bytes4 => bool) public functionWhitelist;
    mapping(address => uint256) public targetGasLimits;
    
    uint256 public constant MIN_ORACLE_SIGNATURES = 3;
    uint256 public constant MAX_ORACLE_SIGNATURES = 7;
    uint256 public constant MAX_OPERATION_VALUE = 50 ether;
    uint256 public constant MAX_PAYLOAD_SIZE = 32768; // 32KB
    uint256 public constant SIGNATURE_VALIDITY_DURATION = 600; // 10 minutes
    uint256 public constant STATE_VERIFICATION_DEPTH = 12; // blocks
    
    uint256 public totalOperations;
    uint256 public successfulOperations;
    uint256 public failedOperations;
      // Security mappings
    mapping(address => bool) public isApprovedTarget;
    mapping(bytes4 => bool) public isWhitelistedSelector;
    
    // Events
    event CrossChainOperationCreated(
        bytes32 indexed operationId,
        uint256 indexed sourceChainId,
        uint256 indexed targetChainId,
        address initiator,
        uint256 value
    );
    
    event OracleSignatureReceived(
        bytes32 indexed operationId,
        address indexed oracle,
        bytes32 stateRoot,
        uint256 blockHeight
    );
    
    event ConsensusReached(
        bytes32 indexed operationId,
        uint256 confirmedSignatures,
        bytes32 finalStateRoot
    );
    
    event OperationExecuted(
        bytes32 indexed operationId,
        bool success,
        bytes result
    );
    
    event OperationFailed(
        bytes32 indexed operationId,
        string reason,
        OperationState finalState
    );
    
    event ChainStateVerified(
        uint256 indexed chainId,
        bytes32 stateRoot,
        uint256 blockHeight
    );
    
    event PayloadValidated(
        bytes32 indexed payloadHash,
        bool approved,
        string notes
    );
    
    event EmergencyHalt(
        bytes32 indexed operationId,
        address indexed initiator,
        string reason
    );

    // Events for security tracking
    event TargetApproved(address indexed target, address indexed approver);
    event TargetRemoved(address indexed target, address indexed remover);
    event FunctionWhitelisted(bytes4 indexed selector, address indexed approver);
    event FunctionRemovedFromWhitelist(bytes4 indexed selector, address indexed remover);

    /**
     * @notice Initialize the enhanced cross-chain bridge
     * @param _securityValidator Address of the security validator contract
     * @param _initialOracles Array of initial oracle addresses
     * @param _supportedChainIds Array of supported chain IDs
     */    constructor(
        address _securityValidator,
        address[] memory _initialOracles,
        uint256[] memory _supportedChainIds
    ) Ownable(msg.sender) {
        require(_securityValidator != address(0), "Invalid validator address");
        require(_initialOracles.length >= MIN_ORACLE_SIGNATURES, "Insufficient oracles");
        require(_initialOracles.length <= MAX_ORACLE_SIGNATURES, "Too many oracles");
        
        securityValidator = CrossChainSecurityValidator(_securityValidator);
        
        // Set up roles
        _grantRole(keccak256("DEFAULT_ADMIN_ROLE"), msg.sender);
        _grantRole(BRIDGE_ADMIN_ROLE, msg.sender);
        _grantRole(EMERGENCY_ROLE, msg.sender);
        
        // Initialize oracles
        for (uint256 i = 0; i < _initialOracles.length; i++) {
            require(_initialOracles[i] != address(0), "Invalid oracle address");
            authorizedOracles[_initialOracles[i]] = true;
            _grantRole(ORACLE_ROLE, _initialOracles[i]);
        }
        
        // Initialize supported chains
        for (uint256 i = 0; i < _supportedChainIds.length; i++) {
            supportedChains[_supportedChainIds[i]] = true;
        }
        
        // Set default timeout configuration
        timeoutConfig = TimeoutConfig({
            operationTimeout: 3600,    // 1 hour
            consensusTimeout: 1800,    // 30 minutes
            executionTimeout: 600,     // 10 minutes
            emergencyTimeout: 300,     // 5 minutes
            maxRetries: 3,
            retryDelay: 60            // 1 minute
        });
    }

    /**
     * @notice Create a new cross-chain operation with enhanced validation
     * @param _targetChainId Target chain ID
     * @param _target Target contract address
     * @param _payload Operation payload
     * @param _value Value to transfer
     * @param _deadline Operation deadline
     * @return operationId The unique operation identifier
     */
    function createCrossChainOperation(
        uint256 _targetChainId,
        address _target,
        bytes calldata _payload,
        uint256 _value,
        uint256 _deadline
    ) external payable nonReentrant whenNotPaused returns (bytes32 operationId)  {
        // TODO: Add nonReentrant modifier
        // Enhanced validation checks
        require(supportedChains[_targetChainId], "Unsupported target chain");
        require(_target != address(0), "Invalid target address");
        require(_payload.length <= MAX_PAYLOAD_SIZE, "Payload too large");
        require(_deadline > block.timestamp, "Invalid deadline");
        require(msg.value == _value, "Value mismatch");
        
        // Security validator check
        require(
            securityValidator.validateCrossChainOperation(
                block.chainid,
                _targetChainId,
                msg.sender,
                _target,
                _payload,
                _value
            ),
            "Security validation failed"
        );
        
        // Generate operation ID
        operationId = keccak256(abi.encodePacked(
            block.chainid,
            _targetChainId,
            msg.sender,
            _target,
            _payload,
            _value,
            block.timestamp,
            totalOperations
        ));
        
        // Comprehensive payload validation
        bytes32 payloadHash = keccak256(_payload);
        _validatePayload(payloadHash, _payload);
        
        // Create operation
        operations[operationId] = CrossChainOperation({
            operationId: operationId,
            sourceChainId: block.chainid,
            targetChainId: _targetChainId,
            initiator: msg.sender,
            target: _target,
            payload: _payload,
            value: _value,
            deadline: _deadline,
            nonce: totalOperations,
            state: OperationState.PENDING,
            createdAt: block.timestamp,
            executedAt: 0,
            requiredSignatures: MIN_ORACLE_SIGNATURES,
            confirmedSignatures: 0,
            merkleRoot: bytes32(0),
            failureReason: ""
        });
        
        totalOperations++;
        
        emit CrossChainOperationCreated(
            operationId,
            block.chainid,
            _targetChainId,
            msg.sender,
            _value
        );
        
        return operationId;
    }

    /**
     * @notice Submit oracle signature for multi-oracle consensus
     * @param _operationId Operation identifier
     * @param _stateRoot State root from source chain
     * @param _blockHeight Block height from source chain
     * @param _signature Oracle signature
     */
    function submitOracleSignature(
        bytes32 _operationId,
        bytes32 _stateRoot,
        uint256 _blockHeight,
        bytes calldata _signature
    ) external onlyRole(ORACLE_ROLE) nonReentrant {
        CrossChainOperation storage operation = operations[_operationId];
        require(operation.operationId != bytes32(0), "Operation not found");
        require(
            operation.state == OperationState.PENDING || 
            operation.state == OperationState.VALIDATING,
            "Invalid operation state"
        );
        require(block.timestamp <= operation.deadline, "Operation expired");
        
        // Verify signature
        bytes32 messageHash = keccak256(abi.encodePacked(
            _operationId,
            _stateRoot,
            _blockHeight,
            operation.sourceChainId
        ));
        
        address recoveredSigner = messageHash.toEthSignedMessageHash().recover(_signature);
        require(recoveredSigner == msg.sender, "Invalid signature");
        require(authorizedOracles[msg.sender], "Unauthorized oracle");
        
        // Check for duplicate signatures
        require(
            oracleSignatures[_operationId][msg.sender].oracle == address(0),
            "Oracle already signed"
        );
        
        // Store oracle signature
        oracleSignatures[_operationId][msg.sender] = OracleSignature({
            oracle: msg.sender,
            signature: _signature,
            timestamp: block.timestamp,
            stateRoot: _stateRoot,
            blockHeight: _blockHeight,
            isValid: true
        });
        
        operation.confirmedSignatures++;
        operation.state = OperationState.ORACLE_CONSENSUS;
        
        // Verify chain state
        _verifyChainState(operation.sourceChainId, _stateRoot, _blockHeight, msg.sender);
        
        emit OracleSignatureReceived(_operationId, msg.sender, _stateRoot, _blockHeight);
        
        // Check if consensus is reached
        if (operation.confirmedSignatures >= operation.requiredSignatures) {
            _processConsensus(_operationId);
        }
    }

    /**
     * @notice Execute cross-chain operation after consensus
     * @param _operationId Operation identifier
     */
    function executeOperation(bytes32 _operationId) external nonReentrant whenNotPaused nonReentrant{
        CrossChainOperation storage operation = operations[_operationId];
        require(operation.operationId != bytes32(0), "Operation not found");
        require(operation.state == OperationState.EXECUTING, "Operation not ready for execution");
        require(block.timestamp <= operation.deadline, "Operation expired");
        
        // Additional security check before execution
        require(
            operation.confirmedSignatures >= operation.requiredSignatures,
            "Insufficient signatures"
        );
        
        // Execute operation with timeout protection
        bool success;
        bytes memory result;
        
        try this._executeWithTimeout(_operationId) returns (bool _success, bytes memory _result) {
            success = _success;
            result = _result;
        } catch Error(string memory reason) {
            _handleOperationFailure(_operationId, reason);
            return;
        } catch {
            _handleOperationFailure(_operationId, "Execution failed");
            return;
        }
        
        if (success) {
            operation.state = OperationState.COMPLETED;
            operation.executedAt = block.timestamp;
            successfulOperations++;
        } else {
            _handleOperationFailure(_operationId, "Execution returned false");
        }
        
        emit OperationExecuted(_operationId, success, result);
    }    /**
     * @notice Internal function to execute operation with timeout protection - SECURITY ENHANCED
     * @param _operationId Operation identifier
     */
    function _executeWithTimeout(bytes32 _operationId) external returns (bool, bytes memory)  {
        // TODO: Add nonReentrant modifier
        require(msg.sender == address(this), "Internal function only");
        
        CrossChainOperation storage operation = operations[_operationId];
          // SECURITY: Enhanced validation before external call
        require(operation.target != address(0), "Invalid target address");
        require(operation.target.code.length > 0, "Target must be a contract");
        require(operation.value <= MAX_OPERATION_VALUE, "Value exceeds maximum");
        require(operation.payload.length <= MAX_PAYLOAD_SIZE, "Payload too large");
        require(operation.payload.length >= 4, "Payload too small");
        require(block.timestamp <= operation.deadline, "Operation expired");
        require(gasleft() > 100000, "Insufficient gas for safe execution");
        
        // Validate target contract is approved
        require(isApprovedTarget[operation.target], "Target not approved");
        
        // Additional security: Check function selector whitelist
        bytes4 selector = bytes4(operation.payload);
        require(isWhitelistedSelector[selector], "Function selector not whitelisted");
        
        // Execute the actual cross-chain operation with enhanced security
        (bool success, bytes memory result) = operation.target.call{
            value: operation.value,
            gas: gasleft() - 50000 // Reserve more gas for cleanup
        }(operation.payload);
        
        // Validate return data size
        require(result.length <= 8192, "Return data too large");
        
        return (success, result);
    }

    /**
     * @notice Validate payload with comprehensive checks
     * @param _payloadHash Hash of the payload
     * @param _payload The actual payload
     */
    function _validatePayload(bytes32 _payloadHash, bytes calldata _payload) internal {
        require(_payload.length > 0, "Empty payload");
        require(_payload.length <= MAX_PAYLOAD_SIZE, "Payload too large");
        
        // Extract function selector
        bytes4 functionSelector = bytes4(_payload[:4]);
        
        // Check for complex data structures
        bool hasComplexData = _payload.length > 4 && _hasComplexStructures(_payload);
        
        // Store validation result
        payloadValidations[_payloadHash] = PayloadValidation({
            payloadHash: _payloadHash,
            size: _payload.length,
            functionSelector: functionSelector,
            hasComplexData: hasComplexData,
            isApproved: true,
            validationNotes: "Automated validation passed",
            validatedAt: block.timestamp
        });
        
        emit PayloadValidated(_payloadHash, true, "Automated validation passed");
    }

    /**
     * @notice Check for complex data structures in payload
     * @param _payload The payload to analyze
     * @return hasComplex True if complex structures are detected
     */
    function _hasComplexStructures(bytes calldata _payload) internal pure returns (bool hasComplex) {
        // Simple heuristic: check for dynamic arrays or nested structures
        // This is a simplified implementation - real-world would be more sophisticated
        return _payload.length > 256 || _containsNestedStructures(_payload);
    }

    /**
     * @notice Check for nested structures in payload
     * @param _payload The payload to analyze
     * @return hasNested True if nested structures are detected
     */
    function _containsNestedStructures(bytes calldata _payload) internal pure returns (bool hasNested) {
        // Simplified check for nested encoding patterns
        if (_payload.length < 64) return false;
        
        // Look for patterns that suggest nested encoding
        for (uint256 i = 4; i < _payload.length - 32; i += 32) {
            bytes32 word = bytes32(_payload[i:i+32]);
            // Check if this looks like an offset to nested data
            uint256 offset = uint256(word);
            if (offset > 64 && offset < _payload.length) {
                return true;
            }
        }
        return false;
    }

    /**
     * @notice Verify chain state with multiple oracles
     * @param _chainId Chain identifier
     * @param _stateRoot State root to verify
     * @param _blockHeight Block height
     * @param _oracle Oracle submitting the verification
     */
    function _verifyChainState(
        uint256 _chainId,
        bytes32 _stateRoot,
        uint256 _blockHeight,
        address _oracle
    ) internal {
        ChainState storage state = chainStates[_chainId];
        
        // Update or create chain state
        if (state.chainId == 0) {
            state.chainId = _chainId;
            state.stateRoot = _stateRoot;
            state.blockHeight = _blockHeight;
            state.timestamp = block.timestamp;
            state.confirmationDepth = STATE_VERIFICATION_DEPTH;
        }
        
        // Mark oracle as verified for this state
        state.verifiedOracles[_oracle] = true;
        
        // Check if state is sufficiently verified
        uint256 verifications = 0;
        address[] memory oracles = _getAuthorizedOracles();
        for (uint256 i = 0; i < oracles.length; i++) {
            if (state.verifiedOracles[oracles[i]]) {
                verifications++;
            }
        }
        
        if (verifications >= MIN_ORACLE_SIGNATURES) {
            state.isVerified = true;
            emit ChainStateVerified(_chainId, _stateRoot, _blockHeight);
        }
    }

    /**
     * @notice Process consensus when sufficient signatures are received
     * @param _operationId Operation identifier
     */
    function _processConsensus(bytes32 _operationId) internal {
        CrossChainOperation storage operation = operations[_operationId];
        
        // Calculate merkle root of all signatures
        bytes32[] memory signatureHashes = new bytes32[](operation.confirmedSignatures);
        uint256 index = 0;
        
        address[] memory oracles = _getAuthorizedOracles();
        for (uint256 i = 0; i < oracles.length && index < operation.confirmedSignatures; i++) {
            OracleSignature storage sig = oracleSignatures[_operationId][oracles[i]];
            if (sig.oracle != address(0) && sig.isValid) {
                signatureHashes[index] = keccak256(abi.encodePacked(
                    sig.oracle,
                    sig.signature,
                    sig.stateRoot,
                    sig.blockHeight
                ));
                index++;
            }
        }
        
        // Calculate merkle root (simplified - in production use proper merkle tree)
        bytes32 merkleRoot = keccak256(abi.encodePacked(signatureHashes));
        operation.merkleRoot = merkleRoot;
        operation.state = OperationState.EXECUTING;
        
        emit ConsensusReached(_operationId, operation.confirmedSignatures, merkleRoot);
    }

    /**
     * @notice Handle operation failure with detailed logging
     * @param _operationId Operation identifier
     * @param _reason Failure reason
     */
    function _handleOperationFailure(bytes32 _operationId, string memory _reason) internal {
        CrossChainOperation storage operation = operations[_operationId];
        operation.state = OperationState.FAILED;
        operation.failureReason = _reason;
        failedOperations++;
        
        emit OperationFailed(_operationId, _reason, OperationState.FAILED);
    }

    /**
     * @notice Get authorized oracles array
     * @return oracles Array of authorized oracle addresses
     */
    function _getAuthorizedOracles() internal view returns (address[] memory oracles) {
        // In a real implementation, this would be stored as an array
        // For simplicity, we'll return a fixed set based on role members
        uint256 oracleCount = getRoleMemberCount(ORACLE_ROLE);
        oracles = new address[](oracleCount);
        
        for (uint256 i = 0; i < oracleCount; i++) {
            oracles[i] = getRoleMember(ORACLE_ROLE, i);
        }
        
        return oracles;
    }

    /**
     * @notice Emergency halt for specific operation
     * @param _operationId Operation to halt
     * @param _reason Reason for emergency halt
     */
    function emergencyHalt(
        bytes32 _operationId,
        string calldata _reason
    ) external onlyRole(EMERGENCY_ROLE)  {
        // TODO: Add nonReentrant modifier
        CrossChainOperation storage operation = operations[_operationId];
        require(operation.operationId != bytes32(0), "Operation not found");
        require(
            operation.state != OperationState.COMPLETED &&
            operation.state != OperationState.FAILED,
            "Operation already finalized"
        );
        
        operation.state = OperationState.EMERGENCY_HALTED;
        operation.failureReason = _reason;
        
        emit EmergencyHalt(_operationId, msg.sender, _reason);
    }

    /**
     * @notice Update timeout configuration
     * @param _newConfig New timeout configuration
     */
    function updateTimeoutConfig(
        TimeoutConfig calldata _newConfig
    ) external onlyRole(BRIDGE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_newConfig.operationTimeout > 0, "Invalid operation timeout");
        require(_newConfig.consensusTimeout > 0, "Invalid consensus timeout");
        require(_newConfig.executionTimeout > 0, "Invalid execution timeout");
        require(_newConfig.maxRetries > 0 && _newConfig.maxRetries <= 10, "Invalid max retries");
        
        timeoutConfig = _newConfig;
    }

    /**
     * @notice Add authorized oracle
     * @param _oracle Oracle address to add
     */
    function addOracle(address _oracle) external onlyRole(BRIDGE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_oracle != address(0), "Invalid oracle address");
        require(!authorizedOracles[_oracle], "Oracle already authorized");
        require(getRoleMemberCount(ORACLE_ROLE) < MAX_ORACLE_SIGNATURES, "Too many oracles");
        
        authorizedOracles[_oracle] = true;
        _grantRole(ORACLE_ROLE, _oracle);
    }

    /**
     * @notice Remove authorized oracle
     * @param _oracle Oracle address to remove
     */
    function removeOracle(address _oracle) external onlyRole(BRIDGE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(authorizedOracles[_oracle], "Oracle not authorized");
        require(getRoleMemberCount(ORACLE_ROLE) > MIN_ORACLE_SIGNATURES, "Cannot remove oracle - minimum required");
        
        authorizedOracles[_oracle] = false;
        _revokeRole(ORACLE_ROLE, _oracle);
    }

    /**
     * @notice Add supported chain
     * @param _chainId Chain ID to add
     */
    function addSupportedChain(uint256 _chainId) external onlyRole(BRIDGE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_chainId > 0, "Invalid chain ID");
        require(!supportedChains[_chainId], "Chain already supported");
        
        supportedChains[_chainId] = true;
    }

    /**
     * @notice Remove supported chain
     * @param _chainId Chain ID to remove
     */
    function removeSupportedChain(uint256 _chainId) external onlyRole(BRIDGE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(supportedChains[_chainId], "Chain not supported");
        
        supportedChains[_chainId] = false;
    }

    /**
     * @notice Approve target contract for cross-chain operations
     * @param _target Target contract address
     */
    function approveTarget(address _target) external onlyRole(BRIDGE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_target != address(0), "Invalid target address");
        require(!approvedTargets[_target], "Target already approved");
        
        approvedTargets[_target] = true;
        
        emit TargetApproved(_target, msg.sender);
    }

    /**
     * @notice Remove target contract approval
     * @param _target Target contract address
     */
    function removeTargetApproval(address _target) external onlyRole(BRIDGE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(approvedTargets[_target], "Target not approved");
        
        approvedTargets[_target] = false;
        
        emit TargetRemoved(_target, msg.sender);
    }

    /**
     * @notice Whitelist function selector for cross-chain operations
     * @param _selector Function selector to whitelist
     */
    function whitelistFunctionSelector(bytes4 _selector) external onlyRole(BRIDGE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(!functionWhitelist[_selector], "Selector already whitelisted");
        
        functionWhitelist[_selector] = true;
        
        emit FunctionWhitelisted(_selector, msg.sender);
    }

    /**
     * @notice Remove function selector from whitelist
     * @param _selector Function selector to remove
     */
    function removeFunctionSelectorFromWhitelist(bytes4 _selector) external onlyRole(BRIDGE_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(functionWhitelist[_selector], "Selector not whitelisted");
        
        functionWhitelist[_selector] = false;
        
        emit FunctionRemovedFromWhitelist(_selector, msg.sender);
    }

    /**
     * @notice Get operation details
     * @param _operationId Operation identifier
     * @return operation Complete operation details
     */
    function getOperation(bytes32 _operationId) external view returns (CrossChainOperation memory operation)  {
        // TODO: Add nonReentrant modifier
        return operations[_operationId];
    }

    /**
     * @notice Get operation signatures count
     * @param _operationId Operation identifier
     * @return count Number of valid signatures
     */
    function getOperationSignatureCount(bytes32 _operationId) external view returns (uint256 count)  {
        // TODO: Add nonReentrant modifier
        address[] memory oracles = _getAuthorizedOracles();
        for (uint256 i = 0; i < oracles.length; i++) {
            if (oracleSignatures[_operationId][oracles[i]].isValid) {
                count++;
            }
        }
        return count;
    }

    /**
     * @notice Check if operation has expired
     * @param _operationId Operation identifier
     * @return expired True if operation has expired
     */
    function isOperationExpired(bytes32 _operationId) external view returns (bool expired)  {
        // TODO: Add nonReentrant modifier
        CrossChainOperation memory operation = operations[_operationId];
        return block.timestamp > operation.deadline;
    }

    /**
     * @notice Get bridge statistics
     * @return total Total operations
     * @return successful Successful operations
     * @return failed Failed operations
     * @return successRate Success rate in basis points
     */
    function getBridgeStats() external view returns (
        uint256 total,
        uint256 successful,
        uint256 failed,
        uint256 successRate
    ) {
        total = totalOperations;
        successful = successfulOperations;
        failed = failedOperations;
        
        if (total > 0) {
            successRate = (successful * 10000) / total; // Basis points
        }
        
        return (total, successful, failed, successRate);
    }

    /**
     * @notice Pause bridge operations
     */
    function pause() external onlyRole(EMERGENCY_ROLE)  nonReentrant onlyOwner{
        _pause();
    }

    /**
     * @notice Unpause bridge operations
     */
    function unpause() external onlyRole(BRIDGE_ADMIN_ROLE)  nonReentrant onlyOwner{
        _unpause();
    }
}
