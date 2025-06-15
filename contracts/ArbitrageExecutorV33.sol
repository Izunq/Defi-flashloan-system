// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "./interfaces/IFlashLoanSimpleReceiver.sol";
import "./interfaces/IAavePool.sol";
import "./interfaces/IStrategyExecutor.sol";
import "./interfaces/IGenericStrategy.sol";

/**
 * @title ArbitrageExecutorV33
 * @notice Advanced arbitrage executor with enhanced security features
 * @dev Implements flash loan receiver with comprehensive security controls
 */
contract ArbitrageExecutorV33 is AccessControl, ReentrancyGuard, Pausable, IFlashLoanSimpleReceiver {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;

    // Constants
    uint256 public constant MAX_SLIPPAGE_BPS = 100; // 1% max slippage
    uint256 public constant EXECUTION_TIMEOUT = 5 minutes;
    uint256 public constant EMERGENCY_TIMEOUT = 24 hours;
    uint256 public constant COOLING_OFF_PERIOD = 12 hours; // Mandatory cooling-off period

    // State variables
    IAavePool public immutable aavePool;
    address public immutable treasury;
    
    // Roles
    bytes32 public constant STRATEGY_EXECUTOR_ROLE = keccak256("STRATEGY_EXECUTOR_ROLE");
    bytes32 public constant EMERGENCY_ADMIN_ROLE = keccak256("EMERGENCY_ADMIN_ROLE");
    bytes32 public constant TREASURY_ADMIN_ROLE = keccak256("TREASURY_ADMIN_ROLE");
    
    // Execution tracking
    mapping(bytes32 => ExecutionDetails) public executionRegistry;
    mapping(address => bool) public approvedStrategies;
    
    // Circuit breaker
    uint256 public failedExecutionsCount;
    uint256 public lastResetTime;
    uint256 public circuitBreakerThreshold = 5;
    bool public circuitBroken = false;
    uint256 public circuitBreakerResetRequestTime = 0; // Timestamp of reset request
      // Slippage protection
    mapping(address => uint256) public minReturnAmounts;
    
    // MEV protection
    uint256 public maxGasPrice = 500 gwei;
    
    // Flash loan execution state tracking (additional reentrancy protection)
    bool private _flashLoanInProgress;
    mapping(bytes32 => bool) private _executionLocked;
    
    // Flash loan execution modifier for additional protection
    modifier flashLoanGuard() {
        require(!_flashLoanInProgress, "Flash loan already in progress");
        _flashLoanInProgress = true;
        _;
        _flashLoanInProgress = false;
    }
    
    // Execution details struct
    struct ExecutionDetails {
        address strategy;
        address initiator;
        uint256 startTime;
        uint256 endTime;
        bool successful;
        uint256 profit;
        bytes32 executionHash;
        ExecutionStatus status;
    }
    
    enum ExecutionStatus {
        NotStarted,
        InProgress,
        Completed,
        Failed,
        Timeout
    }
    
    // Events
    event ArbitrageExecuted(
        bytes32 indexed executionId,
        address indexed strategy,
        address[] assets,
        uint256[] amounts,
        uint256 profit,
        uint256 executionTime
    );
    event ExecutionFailed(
        bytes32 indexed executionId,
        address indexed strategy,
        string reason
    );
    event CircuitBroken(uint256 failedCount, uint256 timestamp);
    event CircuitRestored(uint256 timestamp);
    event CircuitBreakerResetRequested(address indexed requester, uint256 timestamp);
    event SlippageProtectionTriggered(
        bytes32 indexed executionId,
        address token,
        uint256 expected,
        uint256 actual
    );
    event StrategyApproved(address indexed strategy, bool approved);
    event EmergencyFundsRecovered(address token, uint256 amount);
    
    /**
     * @dev Constructor
     * @param _aavePool Address of the Aave pool for flash loans
     * @param _treasury Address of the treasury for profit collection
     */
    constructor(address _aavePool, address _treasury) {
        require(_aavePool != address(0), "Invalid Aave pool address");
        require(_treasury != address(0), "Invalid treasury address");
        
        aavePool = IAavePool(_aavePool);
        treasury = _treasury;
        
        // Setup roles
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(EMERGENCY_ADMIN_ROLE, msg.sender);
        _setupRole(TREASURY_ADMIN_ROLE, msg.sender);
        _setupRole(STRATEGY_EXECUTOR_ROLE, msg.sender);
        
        // Initialize circuit breaker
        lastResetTime = block.timestamp;
    }
    
    /**
     * @dev Modifier to check if a strategy is approved
     */
    modifier onlyApprovedStrategy(address strategy) {
        require(approvedStrategies[strategy], "Strategy not approved");
        _;
    }
    
    /**
     * @dev Modifier to check if circuit breaker is not triggered
     */
    modifier circuitNotBroken() {
        require(!circuitBroken, "Circuit breaker triggered");
        _;
    }
    
    /**
     * @dev Modifier to check gas price for MEV protection
     */
    modifier gasProtection() {
        require(tx.gasprice <= maxGasPrice, "Gas price too high");
        _;
    }
    
    /**
     * @dev Approve or revoke a strategy
     * @param strategy Address of the strategy
     * @param approved Approval status
     */
    function setStrategyApproval(address strategy, bool approved) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        require(strategy != address(0), "Invalid strategy address");
        approvedStrategies[strategy] = approved;
        emit StrategyApproved(strategy, approved);
    }
    
    /**
     * @dev Set minimum return amount for a token (slippage protection)
     * @param token Token address
     * @param minAmount Minimum return amount
     */
    function setMinReturnAmount(address token, uint256 minAmount) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        require(token != address(0), "Invalid token address");
        minReturnAmounts[token] = minAmount;
    }
    
    /**
     * @dev Set circuit breaker threshold
     * @param threshold New threshold
     */
    function setCircuitBreakerThreshold(uint256 threshold) 
        external 
        onlyRole(EMERGENCY_ADMIN_ROLE) 
    {
        require(threshold > 0, "Threshold must be greater than 0");
        circuitBreakerThreshold = threshold;
    }
    
    /**
     * @dev Request to reset circuit breaker - initiates cooling-off period
     */
    function requestCircuitBreakerReset() 
        external 
        onlyRole(EMERGENCY_ADMIN_ROLE) 
    {
        require(circuitBroken, "Circuit not broken");
        
        // Set the reset request time
        circuitBreakerResetRequestTime = block.timestamp;
        
        emit CircuitBreakerResetRequested(msg.sender, block.timestamp);
    }
    
    /**
     * @dev Reset circuit breaker after cooling-off period
     */
    function resetCircuitBreaker() 
        external 
        onlyRole(EMERGENCY_ADMIN_ROLE) 
    {
        require(circuitBroken, "Circuit not broken");
        
        // Check if a reset has been requested
        require(circuitBreakerResetRequestTime > 0, "Reset not requested");
        
        // Require both the emergency timeout AND the cooling-off period
        require(
            block.timestamp > lastResetTime + EMERGENCY_TIMEOUT,
            "Emergency timeout not elapsed"
        );
        
        require(
            block.timestamp > circuitBreakerResetRequestTime + COOLING_OFF_PERIOD,
            "Cooling-off period not elapsed"
        );
        
        circuitBroken = false;
        failedExecutionsCount = 0;
        lastResetTime = block.timestamp;
        circuitBreakerResetRequestTime = 0; // Reset the request time
        
        emit CircuitRestored(block.timestamp);
    }
    
    /**
     * @dev Set maximum gas price for MEV protection
     * @param newMaxGasPrice New maximum gas price
     */
    function setMaxGasPrice(uint256 newMaxGasPrice) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        require(newMaxGasPrice > 0, "Gas price must be greater than 0");
        maxGasPrice = newMaxGasPrice;
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
     * @dev Emergency fund recovery
     * @param token Token to recover
     */
    function emergencyFundRecovery(address token) 
        external 
        onlyRole(EMERGENCY_ADMIN_ROLE) 
        whenPaused 
    {
        require(token != address(0), "Invalid token address");
        
        uint256 balance = IERC20(token).balanceOf(address(this));
        require(balance > 0, "No balance to recover");
        
        IERC20(token).safeTransfer(treasury, balance);
        
        emit EmergencyFundsRecovered(token, balance);
    }
    
    /**
     * @dev Initiate a flash loan for arbitrage
     * @param strategy Strategy address to execute
     * @param asset Asset to borrow
     * @param amount Amount to borrow
     * @param params Additional parameters for the strategy
     * @return executionId Unique identifier for this execution
     */
    function initiateArbitrage(
        address strategy,
        address asset,
        uint256 amount,
        bytes calldata params
    ) 
        external 
        nonReentrant 
        whenNotPaused 
        circuitNotBroken
        gasProtection
        onlyRole(STRATEGY_EXECUTOR_ROLE)
        onlyApprovedStrategy(strategy)
        returns (bytes32 executionId)
    {
        require(strategy != address(0), "Invalid strategy address");
        require(asset != address(0), "Invalid asset address");
        require(amount > 0, "Amount must be greater than 0");
        
        // Generate execution ID
        executionId = keccak256(
            abi.encodePacked(
                strategy,
                asset,
                amount,
                block.timestamp,
                msg.sender
            )
        );
        
        // Check if execution ID already exists
        require(
            executionRegistry[executionId].status == ExecutionStatus.NotStarted,
            "Execution already exists"
        );
        
        // Register execution
        executionRegistry[executionId] = ExecutionDetails({
            strategy: strategy,
            initiator: msg.sender,
            startTime: block.timestamp,
            endTime: 0,
            successful: false,
            profit: 0,
            executionHash: keccak256(params),
            status: ExecutionStatus.InProgress
        });
        
        // Encode parameters for flash loan
        bytes memory flashLoanParams = abi.encode(
            executionId,
            strategy,
            params
        );
        
        // Initiate flash loan
        try aavePool.flashLoanSimple(
            address(this),
            asset,
            amount,
            flashLoanParams,
            0 // referralCode
        ) {
            // Flash loan initiated successfully
            return executionId;
        } catch Error(string memory reason) {
            // Update execution status
            executionRegistry[executionId].status = ExecutionStatus.Failed;
            executionRegistry[executionId].endTime = block.timestamp;
            
            // Increment failed executions count
            _incrementFailedExecutions();
            
            emit ExecutionFailed(executionId, strategy, reason);
            return executionId;
        } catch {
            // Update execution status
            executionRegistry[executionId].status = ExecutionStatus.Failed;
            executionRegistry[executionId].endTime = block.timestamp;
            
            // Increment failed executions count
            _incrementFailedExecutions();
            
            emit ExecutionFailed(executionId, strategy, "Unknown error");
            return executionId;
        }
    }
    
    /**
     * @dev Flash loan callback function
     * @param asset Asset borrowed
     * @param amount Amount borrowed
     * @param premium Premium to be paid
     * @param initiator Initiator of the flash loan
     * @param params Additional parameters
     * @return true if the execution is successful
     */    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) 
        external 
        override 
        nonReentrant 
        flashLoanGuard
        whenNotPaused 
        returns (bool)
    {
        // Verify caller is Aave pool
        require(msg.sender == address(aavePool), "Caller is not Aave pool");
        require(initiator == address(this), "Initiator is not this contract");
          // Decode parameters
        (
            bytes32 executionId,
            address strategy,
            bytes memory strategyParams
        ) = abi.decode(params, (bytes32, address, bytes));
        
        // SECURITY: Prevent duplicate execution attempts
        require(!_executionLocked[executionId], "Execution already locked");
        _executionLocked[executionId] = true;
        
        // Verify execution exists and is in progress
        ExecutionDetails storage execution = executionRegistry[executionId];
        require(
            execution.status == ExecutionStatus.InProgress,
            "Execution not in progress"
        );
        require(
            execution.strategy == strategy,
            "Strategy mismatch"
        );
        
        // Check execution timeout
        require(
            block.timestamp <= execution.startTime + EXECUTION_TIMEOUT,
            "Execution timeout"
        );
        
        // Record token balance before execution
        uint256 balanceBefore = IERC20(asset).balanceOf(address(this));
          // SECURITY CRITICAL: Prepare variables for execution result
        bool success = false;
        uint256 profit = 0;
        string memory errorReason = "";
        uint256 actualProfit = 0;
        uint256 totalRepayment = amount.add(premium);
        uint256 balanceAfter = 0;
        
        // SECURITY: Execute strategy with proper error handling and prevent reentrancy
        try IGenericStrategy(strategy).executeArbitrage(
            asset,
            amount,
            premium,
            strategyParams
        ) returns (uint256 _profit) {
            success = true;
            profit = _profit;
            
            // Check balance after execution
            balanceAfter = IERC20(asset).balanceOf(address(this));
            
            // Check if we have enough balance to repay and have profit
            require(
                balanceAfter >= totalRepayment,
                "Insufficient funds to repay flash loan"
            );
            
            // Calculate actual profit
            actualProfit = balanceAfter.sub(balanceBefore).sub(premium);
            
            // Verify profit meets minimum expectations
            require(
                actualProfit >= profit.mul(MAX_SLIPPAGE_BPS).div(10000),
                "Profit below minimum threshold"
            );
        } catch Error(string memory reason) {
            success = false;
            errorReason = reason;
        } catch {
            success = false;
            errorReason = "Unknown error";
        }
          // SECURITY CRITICAL: Update ALL state BEFORE any external interactions (CEI pattern)
        // This prevents reentrancy attacks by ensuring state changes are completed first
        if (success) {
            // Update execution details
            execution.endTime = block.timestamp;
            execution.successful = true;
            execution.profit = actualProfit;
            execution.status = ExecutionStatus.Completed;
        } else {
            // Update execution status for failed execution
            execution.status = ExecutionStatus.Failed;
            execution.endTime = block.timestamp;
            
            // Increment failed executions count
            _incrementFailedExecutions();
        }
        
        // EXTERNAL INTERACTIONS: Only after ALL state changes are complete
        if (success) {
            // Approve repayment first (required for flash loan)
            IERC20(asset).safeApprove(address(aavePool), totalRepayment);
            
            // Transfer profit to treasury
            if (actualProfit > 0) {
                IERC20(asset).safeTransfer(treasury, actualProfit);
            }
            
            // Emit success event (external interaction via logs)
            address[] memory assets = new address[](1);
            assets[0] = asset;
            uint256[] memory amounts = new uint256[](1);
            amounts[0] = amount;
            
            emit ArbitrageExecuted(
                executionId,
                strategy,
                assets,
                amounts,
                actualProfit,
                block.timestamp - execution.startTime
            );
        } else {
            // Approve repayment even for failed executions to prevent flash loan revert
            IERC20(asset).safeApprove(address(aavePool), totalRepayment);
              // Emit failure event
            emit ExecutionFailed(executionId, strategy, errorReason);
        }
        
        // SECURITY: Clean up execution lock
        _executionLocked[executionId] = false;
        
        return true; // Always return true to avoid reverting the flash loan
    }
    
    /**
     * @dev Get execution details
     * @param executionId Execution ID
     * @return Execution details
     */
    function getExecutionDetails(bytes32 executionId) 
        external 
        view 
        returns (ExecutionDetails memory) 
    {
        return executionRegistry[executionId];
    }
    
    /**
     * @dev Increment failed executions count and check circuit breaker
     */
    function _incrementFailedExecutions() internal {
        failedExecutionsCount++;
        
        // Check if circuit breaker should be triggered
        if (failedExecutionsCount >= circuitBreakerThreshold) {
            circuitBroken = true;
            emit CircuitBroken(failedExecutionsCount, block.timestamp);
        }
    }
}