// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/**
 * @title SecurityEnhancedExecutor
 * @notice Enhanced security version of arbitrage executor with comprehensive protections
 * @dev Implements multiple security layers including timelock, multi-sig, and emergency controls
 */
contract SecurityEnhancedExecutor is AccessControl, ReentrancyGuard, Pausable {
    using ECDSA for bytes32;

    // Enhanced Role Management
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant STRATEGY_ROLE = keccak256("STRATEGY_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");
    bytes32 public constant TIMELOCK_ADMIN_ROLE = keccak256("TIMELOCK_ADMIN_ROLE");
    
    // Security Constants
    uint256 public constant MIN_TIMELOCK_DELAY = 1 hours;
    uint256 public constant MAX_TIMELOCK_DELAY = 7 days;
    uint256 public constant EMERGENCY_TIMELOCK_DELAY = 15 minutes;
    uint256 public constant MAX_CONSECUTIVE_FAILURES = 5;
    uint256 public constant COOLING_OFF_PERIOD = 24 hours;
    
    // Security State
    uint256 public timelockDelay = 24 hours;
    uint256 public emergencyTimelockDelay = EMERGENCY_TIMELOCK_DELAY;
    bool public emergencyShutdown = false;
    uint256 public lastEmergencyAction;
    bool public emergencyStopped = false;
    
    // Circuit Breaker
    uint256 public consecutiveFailures;
    uint256 public lastFailureTime;
    bool public circuitBreakerActive = false;
    
    // Timelock Operations
    struct TimelockOperation {
        bytes32 operationHash;
        uint256 executionTime;
        bool executed;
        address proposer;
        bytes data;
    }
    
    mapping(bytes32 => TimelockOperation) public timelockOperations;
    mapping(address => uint256) public lastOperationTime;
    
    // Multi-signature Requirements
    struct MultiSigOperation {
        bytes32 operationHash;
        address[] signers;
        mapping(address => bool) signatures;
        uint256 requiredSignatures;
        uint256 currentSignatures;
        uint256 deadline;
        bool executed;
    }
    
    mapping(bytes32 => MultiSigOperation) public multiSigOperations;
    uint256 public defaultRequiredSignatures = 2;
    
    // Strategy Validation
    mapping(address => bool) public approvedStrategies;
    mapping(address => uint256) public strategyRiskScore;
    mapping(address => uint256) public strategyLastExecuted;
    uint256 public maxStrategyRiskScore = 70; // Out of 100
    
    // Gas Protection
    uint256 public maxGasPrice = 200 gwei;
    uint256 public maxGasLimit = 5000000;
    
    // Events
    event EmergencyShutdownActivated(address indexed activator, uint256 timestamp);
    event EmergencyShutdownDeactivated(address indexed deactivator, uint256 timestamp);
    event CircuitBreakerTriggered(uint256 consecutiveFailures, uint256 timestamp);
    event CircuitBreakerReset(address indexed resetter, uint256 timestamp);
    event TimelockOperationScheduled(bytes32 indexed operationId, uint256 executionTime, address proposer);
    event TimelockOperationExecuted(bytes32 indexed operationId, address executor);
    event TimelockOperationCancelled(bytes32 indexed operationId, address canceller);
    event MultiSigOperationCreated(bytes32 indexed operationId, uint256 requiredSignatures, uint256 deadline);
    event MultiSigOperationSigned(bytes32 indexed operationId, address signer);
    event MultiSigOperationExecuted(bytes32 indexed operationId);
    event StrategyApproved(address indexed strategy, uint256 riskScore);
    event StrategyRevoked(address indexed strategy, string reason);
    event SecurityParameterUpdated(string parameter, uint256 oldValue, uint256 newValue);
    event EmergencyStop(address indexed activator, uint256 timestamp);
    event OperationsResumed(address indexed activator, uint256 timestamp);
    
    // Custom Errors
    error UnauthorizedAccess(address caller, bytes32 requiredRole);
    error TimelockNotReady(bytes32 operationId, uint256 currentTime, uint256 executionTime);
    error TimelockExpired(bytes32 operationId, uint256 currentTime, uint256 deadline);
    error InsufficientSignatures(bytes32 operationId, uint256 current, uint256 required);
    error OperationAlreadyExecuted(bytes32 operationId);
    error EmergencyShutdownActive();
    error CircuitBreakerActive();
    error StrategyNotApproved(address strategy);
    error StrategyRiskTooHigh(address strategy, uint256 riskScore, uint256 maxAllowed);
    error GasPriceExceedsLimit(uint256 gasPrice, uint256 maxAllowed);
    error GasLimitExceedsLimit(uint256 gasLimit, uint256 maxAllowed);
    error CoolingOffPeriodActive(uint256 remainingTime);
    error InvalidSignature(address signer, bytes32 hash);
    error OperationNotFound(bytes32 operationId);
    
    modifier onlyRole(bytes32 role) override {
        if (!hasRole(role, msg.sender)) {
            revert UnauthorizedAccess(msg.sender, role);
        }
        _;
    }
    
    modifier notInEmergency() {
        if (emergencyShutdown) {
            revert EmergencyShutdownActive();
        }
        _;
    }
    
    modifier circuitBreakerCheck() {
        if (circuitBreakerActive) {
            revert CircuitBreakerActive();
        }
        _;
    }
    
    modifier gasProtection() {
        if (tx.gasprice > maxGasPrice) {
            revert GasPriceExceedsLimit(tx.gasprice, maxGasPrice);
        }
        if (gasleft() > maxGasLimit) {
            revert GasLimitExceedsLimit(gasleft(), maxGasLimit);
        }
        _;
    }
    
    modifier coolingOffCheck(address user) {
        uint256 timeSinceLastOperation = block.timestamp - lastOperationTime[user];
        if (timeSinceLastOperation < COOLING_OFF_PERIOD) {
            revert CoolingOffPeriodActive(COOLING_OFF_PERIOD - timeSinceLastOperation);
        }
        _;
    }
    
    modifier approvedStrategy(address strategy) {
        if (!approvedStrategies[strategy]) {
            revert StrategyNotApproved(strategy);
        }
        if (strategyRiskScore[strategy] > maxStrategyRiskScore) {
            revert StrategyRiskTooHigh(strategy, strategyRiskScore[strategy], maxStrategyRiskScore);
        }
        _;
    }
    
    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ADMIN_ROLE, admin);
        _grantRole(TIMELOCK_ADMIN_ROLE, admin);
        _grantRole(EMERGENCY_ROLE, admin);
    }
    
    /**
     * @notice Emergency shutdown - can be called by EMERGENCY_ROLE holders
     */
    function emergencyShutdown() external onlyRole(EMERGENCY_ROLE) {
        emergencyShutdown = true;
        lastEmergencyAction = block.timestamp;
        _pause();
        emit EmergencyShutdownActivated(msg.sender, block.timestamp);
    }
    
    /**
     * @notice Deactivate emergency shutdown with timelock
     */
    function deactivateEmergencyShutdown() 
        external 
        onlyRole(EMERGENCY_ROLE) 
    {
        require(
            block.timestamp >= lastEmergencyAction + emergencyTimelockDelay,
            "Emergency timelock not expired"
        );
        
        emergencyShutdown = false;
        _unpause();
        emit EmergencyShutdownDeactivated(msg.sender, block.timestamp);
    }
    
    /**
     * @notice Schedule a timelock operation
     */
    function scheduleTimelockOperation(
        bytes32 operationId,
        bytes calldata data,
        uint256 delay
    ) external onlyRole(TIMELOCK_ADMIN_ROLE) notInEmergency {
        require(delay >= MIN_TIMELOCK_DELAY && delay <= MAX_TIMELOCK_DELAY, "Invalid delay");
        require(timelockOperations[operationId].executionTime == 0, "Operation already scheduled");
        
        uint256 executionTime = block.timestamp + delay;
        
        timelockOperations[operationId] = TimelockOperation({
            operationHash: keccak256(data),
            executionTime: executionTime,
            executed: false,
            proposer: msg.sender,
            data: data
        });
        
        emit TimelockOperationScheduled(operationId, executionTime, msg.sender);
    }
    
    /**
     * @notice Execute a timelock operation
     */
    function executeTimelockOperation(bytes32 operationId)
        external
        onlyRole(ADMIN_ROLE)
        nonReentrant
        notInEmergency
    {
        TimelockOperation storage operation = timelockOperations[operationId];
        
        if (operation.executionTime == 0) {
            revert OperationNotFound(operationId);
        }
        
        if (block.timestamp < operation.executionTime) {
            revert TimelockNotReady(operationId, block.timestamp, operation.executionTime);
        }
        
        if (operation.executed) {
            revert OperationAlreadyExecuted(operationId);
        }
        
        // Mark as executed before external calls
        operation.executed = true;
        lastOperationTime[msg.sender] = block.timestamp;
        
        // Execute the operation
        (bool success, ) = address(this).call(operation.data);
        require(success, "Operation execution failed");
        
        emit TimelockOperationExecuted(operationId, msg.sender);
    }
    
    /**
     * @notice Cancel a timelock operation
     */
    function cancelTimelockOperation(bytes32 operationId)
        external
        onlyRole(EMERGENCY_ROLE)
    {
        TimelockOperation storage operation = timelockOperations[operationId];
        
        if (operation.executionTime == 0) {
            revert OperationNotFound(operationId);
        }
        
        if (operation.executed) {
            revert OperationAlreadyExecuted(operationId);
        }
        
        delete timelockOperations[operationId];
        
        emit TimelockOperationCancelled(operationId, msg.sender);
    }
    
    /**
     * @notice Create a multi-signature operation
     */
    function createMultiSigOperation(
        bytes32 operationId,
        address[] calldata signers,
        uint256 requiredSignatures,
        uint256 deadline,
        bytes calldata data
    ) external onlyRole(ADMIN_ROLE) notInEmergency {
        require(signers.length >= requiredSignatures, "Invalid signer configuration");
        require(deadline > block.timestamp, "Invalid deadline");
        require(multiSigOperations[operationId].deadline == 0, "Operation already exists");
        
        MultiSigOperation storage operation = multiSigOperations[operationId];
        operation.operationHash = keccak256(data);
        operation.signers = signers;
        operation.requiredSignatures = requiredSignatures;
        operation.deadline = deadline;
        operation.executed = false;
        
        emit MultiSigOperationCreated(operationId, requiredSignatures, deadline);
    }
    
    /**
     * @notice Sign a multi-signature operation
     */
    function signMultiSigOperation(
        bytes32 operationId,
        bytes calldata signature
    ) external notInEmergency {
        MultiSigOperation storage operation = multiSigOperations[operationId];
        
        require(operation.deadline > block.timestamp, "Operation expired");
        require(!operation.executed, "Operation already executed");
        require(!operation.signatures[msg.sender], "Already signed");
        
        // Verify signer is authorized
        bool authorized = false;
        for (uint256 i = 0; i < operation.signers.length; i++) {
            if (operation.signers[i] == msg.sender) {
                authorized = true;
                break;
            }
        }
        require(authorized, "Unauthorized signer");
        
        // Verify signature
        bytes32 hash = keccak256(abi.encodePacked(operationId, operation.operationHash));
        bytes32 ethSignedHash = hash.toEthSignedMessageHash();
        address recovered = ethSignedHash.recover(signature);
        
        if (recovered != msg.sender) {
            revert InvalidSignature(msg.sender, hash);
        }
        
        operation.signatures[msg.sender] = true;
        operation.currentSignatures++;
        
        emit MultiSigOperationSigned(operationId, msg.sender);
    }
    
    /**
     * @notice Execute a multi-signature operation
     */
    function executeMultiSigOperation(bytes32 operationId, bytes calldata data)
        external
        nonReentrant
        notInEmergency
    {
        MultiSigOperation storage operation = multiSigOperations[operationId];
        
        require(operation.deadline > block.timestamp, "Operation expired");
        require(!operation.executed, "Operation already executed");
        
        if (operation.currentSignatures < operation.requiredSignatures) {
            revert InsufficientSignatures(
                operationId,
                operation.currentSignatures,
                operation.requiredSignatures
            );
        }
        
        require(keccak256(data) == operation.operationHash, "Data hash mismatch");
        
        // Mark as executed before external calls
        operation.executed = true;
        
        // Execute the operation
        (bool success, ) = address(this).call(data);
        require(success, "Operation execution failed");
        
        emit MultiSigOperationExecuted(operationId);
    }
    
    /**
     * @notice Approve a strategy for execution
     */
    function approveStrategy(
        address strategy,
        uint256 riskScore
    ) external onlyRole(ADMIN_ROLE) notInEmergency {
        require(strategy != address(0), "Invalid strategy address");
        require(riskScore <= 100, "Invalid risk score");
        
        approvedStrategies[strategy] = true;
        strategyRiskScore[strategy] = riskScore;
        
        emit StrategyApproved(strategy, riskScore);
    }
    
    /**
     * @notice Revoke strategy approval
     */
    function revokeStrategy(address strategy, string calldata reason)
        external
        onlyRole(ADMIN_ROLE)
    {
        approvedStrategies[strategy] = false;
        emit StrategyRevoked(strategy, reason);
    }
    
    /**
     * @notice Update security parameters with timelock
     */
    function updateSecurityParameter(
        string calldata parameter,
        uint256 newValue
    ) external onlyRole(TIMELOCK_ADMIN_ROLE) notInEmergency {
        bytes32 paramHash = keccak256(bytes(parameter));
        uint256 oldValue;
        
        if (paramHash == keccak256("maxGasPrice")) {
            oldValue = maxGasPrice;
            require(newValue >= 10 gwei && newValue <= 1000 gwei, "Invalid gas price");
            maxGasPrice = newValue;
        } else if (paramHash == keccak256("maxGasLimit")) {
            oldValue = maxGasLimit;
            require(newValue >= 1000000 && newValue <= 10000000, "Invalid gas limit");
            maxGasLimit = newValue;
        } else if (paramHash == keccak256("maxStrategyRiskScore")) {
            oldValue = maxStrategyRiskScore;
            require(newValue <= 100, "Invalid risk score");
            maxStrategyRiskScore = newValue;
        } else if (paramHash == keccak256("timelockDelay")) {
            oldValue = timelockDelay;
            require(newValue >= MIN_TIMELOCK_DELAY && newValue <= MAX_TIMELOCK_DELAY, "Invalid delay");
            timelockDelay = newValue;
        } else {
            revert("Unknown parameter");
        }
        
        emit SecurityParameterUpdated(parameter, oldValue, newValue);
    }
    
    /**
     * @notice Trigger circuit breaker
     */
    function _triggerCircuitBreaker() internal {
        consecutiveFailures++;
        lastFailureTime = block.timestamp;
        
        if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
            circuitBreakerActive = true;
            emit CircuitBreakerTriggered(consecutiveFailures, block.timestamp);
        }
    }
    
    /**
     * @notice Reset circuit breaker
     */
    function resetCircuitBreaker()
        external
        onlyRole(EMERGENCY_ROLE)
        coolingOffCheck(msg.sender)
    {
        require(circuitBreakerActive, "Circuit breaker not active");
        require(
            block.timestamp >= lastFailureTime + COOLING_OFF_PERIOD,
            "Cooling off period not elapsed"
        );
        
        circuitBreakerActive = false;
        consecutiveFailures = 0;
        lastOperationTime[msg.sender] = block.timestamp;
        
        emit CircuitBreakerReset(msg.sender, block.timestamp);
    }
    
    /**
     * @notice Emergency stop function for circuit breaker
     * @dev Can only be called by emergency role or admin
     */
    function emergencyStop() external onlyRole(EMERGENCY_ROLE) {
        emergencyStopped = true;
        emit EmergencyStop(msg.sender, block.timestamp);
    }
    
    /**
     * @notice Resume operations after emergency stop
     * @dev Can only be called by admin role
     */
    function resumeOperations() external onlyRole(ADMIN_ROLE) {
        emergencyStopped = false;
        emit OperationsResumed(msg.sender, block.timestamp);
    }
    
    /**
     * @notice Get current security status
     */
    function getSecurityStatus() external view returns (
        bool emergencyShutdownStatus,
        bool circuitBreakerStatus,
        uint256 consecutiveFailureCount,
        uint256 currentTimelockDelay,
        uint256 maxAllowedGasPrice,
        uint256 maxAllowedGasLimit
    ) {
        return (
            emergencyShutdown,
            circuitBreakerActive,
            consecutiveFailures,
            timelockDelay,
            maxGasPrice,
            maxGasLimit
        );
    }
}
