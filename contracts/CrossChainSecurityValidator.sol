// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "./InputValidator.sol";

/**
 * @title CrossChainSecurityValidator
 * @notice Enhanced security validator for cross-chain operations
 * @dev Provides comprehensive validation for cross-chain messages and operations
 */
contract CrossChainSecurityValidator is AccessControl, ReentrancyGuard {
    using ECDSA for bytes32;
    using InputValidator for uint256;
    using InputValidator for address;

    // Role definitions
    bytes32 public constant VALIDATOR_ADMIN_ROLE = keccak256("VALIDATOR_ADMIN_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant BRIDGE_OPERATOR_ROLE = keccak256("BRIDGE_OPERATOR_ROLE");

    // Cross-chain message validation
    struct MessageInfo {
        bytes32 messageHash;
        uint256 sourceChainId;
        uint256 targetChainId;
        address initiator;
        uint256 timestamp;
        uint256 value;
        bytes4 functionSelector;
        bool isValidated;
        uint256 confirmations;
    }

    // Function validation rules
    struct FunctionRule {
        bytes4 selector;
        uint256 maxValue;
        uint256 minConfirmations;
        bool requiresMultiSig;
        bool isActive;
        uint256 dailyLimit;
        uint256 hourlyLimit;
    }

    // Oracle signature tracking
    struct OracleSignature {
        address oracle;
        uint256 timestamp;
        bytes signature;
        bool isValid;
    }

    // Chain health monitoring
    struct ChainHealth {
        uint256 lastBlockHeight;
        uint256 lastUpdateTime;
        uint256 avgBlockTime;
        uint256 confirmationDepth;
        bool isHealthy;
        bool isPaused;
    }

    // Transfer limits tracking
    struct TransferLimits {
        uint256 maxPerOperation;
        uint256 maxPerHour;
        uint256 maxDaily;
        uint256 hourlyUsed;
        uint256 dailyUsed;
        uint256 lastHourlyReset;
        uint256 lastDailyReset;
    }

    // State variables
    mapping(bytes32 => MessageInfo) public messages;
    mapping(bytes4 => FunctionRule) public functionRules;
    mapping(uint256 => ChainHealth) public chainHealth;
    mapping(uint256 => mapping(uint256 => TransferLimits)) public transferLimits;
    mapping(address => mapping(uint256 => uint256)) public operatorNonces;
    mapping(bytes32 => mapping(address => bool)) public messageConfirmations;
    
    uint256 public constant MIN_ORACLE_CONFIRMATIONS = 3;
    uint256 public constant MAX_SIGNATURE_AGE = 300; // 5 minutes
    uint256 public constant MAX_PAYLOAD_SIZE = 10240; // 10KB
    uint256 public constant CHAIN_HEALTH_TIMEOUT = 600; // 10 minutes

    // Events
    event MessageValidated(
        bytes32 indexed messageHash,
        uint256 indexed sourceChainId,
        uint256 indexed targetChainId,
        address initiator
    );

    event FunctionRuleUpdated(
        bytes4 indexed selector,
        uint256 maxValue,
        uint256 minConfirmations,
        bool requiresMultiSig
    );

    event ChainHealthUpdated(
        uint256 indexed chainId,
        bool isHealthy,
        uint256 blockHeight,
        uint256 timestamp
    );

    event SuspiciousActivityDetected(
        bytes32 indexed messageHash,
        string reason,
        address reporter,
        uint256 timestamp
    );

    event TransferLimitExceeded(
        uint256 indexed sourceChain,
        uint256 indexed targetChain,
        uint256 attempted,
        uint256 limit,
        string limitType
    );

    // Custom errors
    error InvalidPayloadSize(uint256 size, uint256 maxSize);
    error FunctionNotAllowed(bytes4 selector);
    error InsufficientConfirmations(uint256 received, uint256 required);
    error ChainUnhealthy(uint256 chainId);
    error TransferLimitExceeded(uint256 amount, uint256 limit);
    error InvalidSignatureAge(uint256 age, uint256 maxAge);
    error ReplayAttackDetected(address operator, uint256 nonce);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(VALIDATOR_ADMIN_ROLE, msg.sender);
        
        // Initialize default function rules
        _initializeDefaultRules();
    }

    /**
     * @notice Validate a cross-chain message
     * @param messageHash Hash of the message
     * @param sourceChainId Source chain ID
     * @param targetChainId Target chain ID
     * @param initiator Message initiator
     * @param payload Message payload
     * @param value Transfer value
     * @param signatures Array of oracle signatures
     * @return isValid Whether the message is valid
     */
    function validateCrossChainMessage(
        bytes32 messageHash,
        uint256 sourceChainId,
        uint256 targetChainId,
        address initiator,
        bytes calldata payload,
        uint256 value,
        OracleSignature[] calldata signatures
    ) external returns (bool isValid) {
        // Basic payload validation
        _validatePayload(payload, value);
        
        // Chain health validation
        _requireHealthyChain(sourceChainId);
        _requireHealthyChain(targetChainId);
        
        // Transfer limits validation
        _validateTransferLimits(sourceChainId, targetChainId, value);
        
        // Function-specific validation
        bytes4 selector = bytes4(payload[:4]);
        _validateFunctionCall(selector, value);
        
        // Signature validation
        uint256 validSignatures = _validateSignatures(messageHash, signatures);
        FunctionRule memory rule = functionRules[selector];
        
        if (validSignatures < rule.minConfirmations) {
            revert InsufficientConfirmations(validSignatures, rule.minConfirmations);
        }
        
        // Store message info
        messages[messageHash] = MessageInfo({
            messageHash: messageHash,
            sourceChainId: sourceChainId,
            targetChainId: targetChainId,
            initiator: initiator,
            timestamp: block.timestamp,
            value: value,
            functionSelector: selector,
            isValidated: true,
            confirmations: validSignatures
        });
        
        // Update transfer limits
        _updateTransferLimits(sourceChainId, targetChainId, value);
        
        emit MessageValidated(messageHash, sourceChainId, targetChainId, initiator);
        
        return true;
    }

    /**
     * @notice Update chain health status
     * @param chainId Chain ID
     * @param blockHeight Current block height
     * @param avgBlockTime Average block time
     * @param isHealthy Health status
     */
    function updateChainHealth(
        uint256 chainId,
        uint256 blockHeight,
        uint256 avgBlockTime,
        bool isHealthy
    ) external onlyRole(ORACLE_ROLE) {
        ChainHealth storage health = chainHealth[chainId];
        
        health.lastBlockHeight = blockHeight;
        health.lastUpdateTime = block.timestamp;
        health.avgBlockTime = avgBlockTime;
        health.isHealthy = isHealthy;
        
        // Auto-pause if unhealthy
        if (!isHealthy) {
            health.isPaused = true;
        }
        
        emit ChainHealthUpdated(chainId, isHealthy, blockHeight, block.timestamp);
    }

    /**
     * @notice Configure function rule
     * @param selector Function selector
     * @param maxValue Maximum value allowed
     * @param minConfirmations Minimum oracle confirmations required
     * @param requiresMultiSig Whether multi-sig is required
     * @param dailyLimit Daily transfer limit
     * @param hourlyLimit Hourly transfer limit
     */
    function configureFunctionRule(
        bytes4 selector,
        uint256 maxValue,
        uint256 minConfirmations,
        bool requiresMultiSig,
        uint256 dailyLimit,
        uint256 hourlyLimit
    ) external onlyRole(VALIDATOR_ADMIN_ROLE) {
        InputValidator.requireInRange(minConfirmations, 1, 10);
        InputValidator.requireInRange(maxValue, 0, type(uint128).max);
        
        functionRules[selector] = FunctionRule({
            selector: selector,
            maxValue: maxValue,
            minConfirmations: minConfirmations,
            requiresMultiSig: requiresMultiSig,
            isActive: true,
            dailyLimit: dailyLimit,
            hourlyLimit: hourlyLimit
        });
        
        emit FunctionRuleUpdated(selector, maxValue, minConfirmations, requiresMultiSig);
    }

    /**
     * @notice Emergency pause chain operations
     * @param chainId Chain ID to pause
     */
    function emergencyPauseChain(uint256 chainId) external onlyRole(VALIDATOR_ADMIN_ROLE) {
        chainHealth[chainId].isPaused = true;
        chainHealth[chainId].isHealthy = false;
        
        emit ChainHealthUpdated(chainId, false, 0, block.timestamp);
    }

    /**
     * @notice Get message validation status
     * @param messageHash Message hash
     * @return info Message information
     */
    function getMessageInfo(bytes32 messageHash) external view returns (MessageInfo memory info) {
        return messages[messageHash];
    }

    /**
     * @notice Check if chain is healthy and operational
     * @param chainId Chain ID
     * @return isHealthy Whether chain is healthy
     */
    function isChainHealthy(uint256 chainId) external view returns (bool isHealthy) {
        ChainHealth memory health = chainHealth[chainId];
        
        return health.isHealthy && 
               !health.isPaused && 
               (block.timestamp - health.lastUpdateTime) < CHAIN_HEALTH_TIMEOUT;
    }

    /**
     * @notice Validate payload structure and size
     * @param payload Message payload
     * @param value Transfer value
     */
    function _validatePayload(bytes calldata payload, uint256 value) internal pure {
        if (payload.length > MAX_PAYLOAD_SIZE) {
            revert InvalidPayloadSize(payload.length, MAX_PAYLOAD_SIZE);
        }
        
        require(payload.length >= 4, "Payload too short");
        
        // Additional payload structure validation can be added here
        // For example, ABI decoding validation
    }

    /**
     * @notice Validate function call permissions
     * @param selector Function selector
     * @param value Transfer value
     */
    function _validateFunctionCall(bytes4 selector, uint256 value) internal view {
        FunctionRule memory rule = functionRules[selector];
        
        if (!rule.isActive) {
            revert FunctionNotAllowed(selector);
        }
        
        if (value > rule.maxValue) {
            revert TransferLimitExceeded(value, rule.maxValue);
        }
    }

    /**
     * @notice Validate oracle signatures
     * @param messageHash Message hash
     * @param signatures Array of signatures
     * @return validCount Number of valid signatures
     */
    function _validateSignatures(
        bytes32 messageHash,
        OracleSignature[] calldata signatures
    ) internal view returns (uint256 validCount) {
        bytes32 ethSignedMessageHash = messageHash.toEthSignedMessageHash();
        
        for (uint256 i = 0; i < signatures.length; i++) {
            if (_validateSingleSignature(ethSignedMessageHash, signatures[i])) {
                validCount++;
            }
        }
        
        return validCount;
    }

    /**
     * @notice Validate individual oracle signature
     * @param messageHash Signed message hash
     * @param signature Oracle signature
     * @return isValid Whether signature is valid
     */
    function _validateSingleSignature(
        bytes32 messageHash,
        OracleSignature calldata signature
    ) internal view returns (bool isValid) {
        // Check signature age
        if (block.timestamp - signature.timestamp > MAX_SIGNATURE_AGE) {
            return false;
        }
        
        // Verify oracle role
        if (!hasRole(ORACLE_ROLE, signature.oracle)) {
            return false;
        }
        
        // Recover and verify signature
        address signer = messageHash.recover(signature.signature);
        return signer == signature.oracle;
    }

    /**
     * @notice Require chain to be healthy
     * @param chainId Chain ID
     */
    function _requireHealthyChain(uint256 chainId) internal view {
        ChainHealth memory health = chainHealth[chainId];
        
        if (!health.isHealthy || health.isPaused) {
            revert ChainUnhealthy(chainId);
        }
        
        // Check if health data is stale
        if (block.timestamp - health.lastUpdateTime > CHAIN_HEALTH_TIMEOUT) {
            revert ChainUnhealthy(chainId);
        }
    }

    /**
     * @notice Validate transfer limits
     * @param sourceChain Source chain ID
     * @param targetChain Target chain ID
     * @param amount Transfer amount
     */
    function _validateTransferLimits(
        uint256 sourceChain,
        uint256 targetChain,
        uint256 amount
    ) internal view {
        TransferLimits memory limits = transferLimits[sourceChain][targetChain];
        
        // Check per-operation limit
        if (amount > limits.maxPerOperation) {
            revert TransferLimitExceeded(amount, limits.maxPerOperation);
        }
        
        // Check hourly limit
        if (limits.hourlyUsed + amount > limits.maxPerHour) {
            revert TransferLimitExceeded(limits.hourlyUsed + amount, limits.maxPerHour);
        }
        
        // Check daily limit
        if (limits.dailyUsed + amount > limits.maxDaily) {
            revert TransferLimitExceeded(limits.dailyUsed + amount, limits.maxDaily);
        }
    }

    /**
     * @notice Update transfer limits after successful operation
     * @param sourceChain Source chain ID
     * @param targetChain Target chain ID
     * @param amount Transfer amount
     */
    function _updateTransferLimits(
        uint256 sourceChain,
        uint256 targetChain,
        uint256 amount
    ) internal {
        TransferLimits storage limits = transferLimits[sourceChain][targetChain];
        
        // Reset counters if needed
        if (block.timestamp - limits.lastHourlyReset > 1 hours) {
            limits.hourlyUsed = 0;
            limits.lastHourlyReset = block.timestamp;
        }
        
        if (block.timestamp - limits.lastDailyReset > 1 days) {
            limits.dailyUsed = 0;
            limits.lastDailyReset = block.timestamp;
        }
        
        // Update usage
        limits.hourlyUsed += amount;
        limits.dailyUsed += amount;
    }

    /**
     * @notice Initialize default function rules
     */
    function _initializeDefaultRules() internal {
        // Default rules for common functions
        bytes4[] memory selectors = new bytes4[](3);
        selectors[0] = bytes4(keccak256("executeArbitrage(address,uint256,bytes)"));
        selectors[1] = bytes4(keccak256("updatePrice(address,uint256)"));
        selectors[2] = bytes4(keccak256("emergencyWithdraw(address,uint256)"));
        
        for (uint256 i = 0; i < selectors.length; i++) {
            functionRules[selectors[i]] = FunctionRule({
                selector: selectors[i],
                maxValue: 100 ether,
                minConfirmations: MIN_ORACLE_CONFIRMATIONS,
                requiresMultiSig: true,
                isActive: true,
                dailyLimit: 1000 ether,
                hourlyLimit: 100 ether
            });
        }
    }
}
