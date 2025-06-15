// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

// --- INTERFACES ---

// Aave V3 Pool Interface for Flash Loans
interface IPool {
    function flashLoan(
        address receiverAddress,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata interestRateModes,
        address onBehalfOf,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

// Interface for our Incubator contract
interface IStrategyIncubator {
    // V20 UPDATE: Define structs to match StrategyIncubatorV20.getStrategy return type
    struct StrategyGenome { // Definition from StrategyIncubatorV20
        string topology;
        string[] dexTypes;
        string volatilityTolerance;
        string gasTolerance;
    }

    struct BacktestReport { // Definition from StrategyIncubatorV20
        bytes32 reportHash;
        uint256 generatedAt;
        int256 simulatedPnl;
        uint256 aiConfidenceScore;
    }

    // StrategyStatus enum from StrategyIncubatorV20 is uint8 compatible (Proposed=0, Backtested=1, etc.)
    struct IncubatedStrategy { // Definition from StrategyIncubatorV20, using uint8 for status
        address strategyAddress;
        address proposer;
        uint8 status; // Represents StrategyStatus enum
        StrategyGenome genome;
        BacktestReport backtest;
        uint256 totalLiveProfit;
    }

    function recordLiveTestProfit(uint256 _strategyId, uint256 _profit) external;
    // V20 UPDATE: Ensure getStrategy returns the full IncubatedStrategy struct
    function getStrategy(uint256 _strategyId) external view returns (IncubatedStrategy memory);
}

// A generic interface for any arbitrage strategy we deploy.
interface IArbitrageStrategy {
    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}

// --- LIBRARIES ---

// OpenZeppelin's SafeERC20 library is already imported above

// --- CONTRACTS ---

contract MyArbitrageContract is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;

    IPool public immutable AAVE_POOL;
    IStrategyIncubator public immutable STRATEGY_INCUBATOR;

    // Define the roles
    bytes32 public constant STRATEGY_PROPOSER_ROLE = keccak256("STRATEGY_PROPOSER_ROLE");
    bytes32 public constant STRATEGY_EXECUTOR_ROLE = keccak256("STRATEGY_EXECUTOR_ROLE");
    bytes32 public constant EMERGENCY_ADMIN_ROLE = keccak256("EMERGENCY_ADMIN_ROLE");

    // Constants for slippage protection
    uint256 public constant MAX_SLIPPAGE_BPS = 100; // 1% max slippage
    uint256 public constant EXECUTION_TIMEOUT = 5 minutes;    // MEV protection
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

    // Circuit breaker
    uint256 public failedExecutionsCount;
    uint256 public lastResetTime;
    uint256 public circuitBreakerThreshold = 5;
    bool public circuitBroken = false;

    // Execution tracking
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

    mapping(bytes32 => ExecutionDetails) public executionRegistry;

    // Events
    event ArbitrageExecuted(uint256 strategyId, address[] assets, uint256[] amounts, uint256 profit);
    event EmergencyPaused(address admin);
    event EmergencyUnpaused(address admin);
    event StrategyProposed(uint256 strategyId, address proposer);
    event ExecutionFailed(bytes32 indexed executionId, address indexed strategy, string reason);
    event CircuitBroken(uint256 failedCount, uint256 timestamp);
    event CircuitRestored(uint256 timestamp);
    event SlippageProtectionTriggered(bytes32 indexed executionId, address token, uint256 expected, uint256 actual);

    // Modifiers
    modifier validStrategy(uint256 strategyId) {
        IStrategyIncubator.IncubatedStrategy memory strategyData = STRATEGY_INCUBATOR.getStrategy(strategyId);
        require(strategyData.strategyAddress != address(0), "Invalid strategy");
        require(strategyData.status > 0, "Strategy not active"); // Status 0 is Proposed
        _;
    }

    modifier circuitNotBroken() {
        require(!circuitBroken, "Circuit breaker triggered");
        _;
    }
    
    modifier gasProtection() {
        require(tx.gasprice <= maxGasPrice, "Gas price too high");
        _;
    }

    constructor(address _aavePool, address _strategyIncubator) {
        require(_aavePool != address(0), "Invalid Aave pool address");
        require(_strategyIncubator != address(0), "Invalid strategy incubator address");
        
        AAVE_POOL = IPool(_aavePool);
        STRATEGY_INCUBATOR = IStrategyIncubator(_strategyIncubator);

        // Grant the contract deployer the default admin role: it can grant and revoke any role
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(EMERGENCY_ADMIN_ROLE, msg.sender);
        
        // Initialize circuit breaker
        lastResetTime = block.timestamp;
    }

    // Emergency pause/unpause functions
    function emergencyPause() external onlyRole(EMERGENCY_ADMIN_ROLE) {
        _pause();
        emit EmergencyPaused(msg.sender);
    }

    function emergencyUnpause() external onlyRole(EMERGENCY_ADMIN_ROLE) {
        _unpause();
        emit EmergencyUnpaused(msg.sender);
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
     * @dev Reset circuit breaker
     */
    function resetCircuitBreaker() 
        external 
        onlyRole(EMERGENCY_ADMIN_ROLE) 
    {
        require(circuitBroken, "Circuit not broken");
        
        circuitBroken = false;
        failedExecutionsCount = 0;
        lastResetTime = block.timestamp;
        
        emit CircuitRestored(block.timestamp);
    }

    // Allow admin to grant/revoke roles as needed
    function _grantRole(bytes32 role, address account) internal override {
        super._grantRole(role, account);
    }

    function _revokeRole(bytes32 role, address account) internal override {
        super._revokeRole(role, account);
    }

    // Example function to propose a new strategy
    function proposeStrategy(
        string memory topology,
        string[] memory dexTypes,
        string memory volatilityTolerance,
        string memory gasTolerance
    ) external onlyRole(STRATEGY_PROPOSER_ROLE) whenNotPaused {
        // ...implementation...
        emit StrategyProposed(/* strategyId */, msg.sender);
    }    // Function to execute an arbitrage operation - this is the callback from the flash loan    function executeArbitrage(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external onlyRole(STRATEGY_EXECUTOR_ROLE) nonReentrant flashLoanGuard whenNotPaused returns (bool) {
        // Security checks: ensure the caller is the Aave Pool and this contract initiated it
        require(msg.sender == address(AAVE_POOL), "Caller is not the Aave Pool");
        require(initiator == address(this), "Initiator is not this contract");        // Decode parameters
        (bytes32 executionId, uint256 strategyId) = abi.decode(params, (bytes32, uint256));
        
        // SECURITY: Prevent duplicate execution attempts
        require(!_executionLocked[executionId], "Execution already locked");
        _executionLocked[executionId] = true;
        
        // Verify execution exists and is in progress
        ExecutionDetails storage execution = executionRegistry[executionId];
        require(
            execution.status == ExecutionStatus.InProgress,
            "Execution not in progress"
        );
        
        // Check execution timeout
        require(
            block.timestamp <= execution.startTime + EXECUTION_TIMEOUT,
            "Execution timeout"
        );

        // Get the strategy address from the incubator
        // V20 UPDATE: Correctly call getStrategy and access strategyAddress from the struct
        IStrategyIncubator.IncubatedStrategy memory strategyData = STRATEGY_INCUBATOR.getStrategy(strategyId);
        address strategyAddress = strategyData.strategyAddress;
        require(strategyAddress != address(0), "Invalid strategy address");
        require(strategyAddress == execution.strategy, "Strategy mismatch");        // Record token balance before execution for slippage protection
        uint256 balanceBefore = IERC20(assets[0]).balanceOf(address(this));
        
        // SECURITY CRITICAL: Prepare variables for execution result
        bool success;
        string memory errorReason = "";
        uint256 actualProfit = 0;
        uint256 totalRepayment = amounts[0].add(premiums[0]);
        
        // Execute the strategy
        try IArbitrageStrategy(strategyAddress).executeOperation(
            assets,
            amounts,
            premiums,
            initiator,
            params
        ) returns (bool _success) {
            success = _success;
            require(success, "Strategy execution failed");
            
            // Check balance after execution
            uint256 balanceAfter = IERC20(assets[0]).balanceOf(address(this));
            
            // Check if we have enough balance to repay and have profit
            require(
                balanceAfter >= totalRepayment,
                "Insufficient funds to repay flash loan"
            );
            
            // Calculate actual profit
            actualProfit = balanceAfter.sub(balanceBefore).sub(premiums[0]);
            
        } catch Error(string memory reason) {
            success = false;
            errorReason = reason;
        } catch {
            success = false;
            errorReason = "Unknown error";        }
        
        // SECURITY CRITICAL: Update ALL state BEFORE any external interactions (CEI pattern)
        // This prevents reentrancy attacks by ensuring state changes are completed first
        if (success) {
            // Update execution details
            execution.endTime = block.timestamp;
            execution.successful = true;
            execution.profit = actualProfit;
            execution.status = ExecutionStatus.Completed;
        } else {
            // Update execution status
            execution.status = ExecutionStatus.Failed;
            execution.endTime = block.timestamp;
            
            // Increment failed executions count
            _incrementFailedExecutions();
        }
        
        // EXTERNAL INTERACTIONS: Only after ALL state changes are complete
        if (success) {
            // Approve repayment first (required for flash loan)
            IERC20(assets[0]).safeApprove(address(AAVE_POOL), totalRepayment);
            
            // Record profit in the incubator (external call)
            STRATEGY_INCUBATOR.recordLiveTestProfit(strategyId, actualProfit);
            
            // Emit success event (external interaction via logs)
            emit ArbitrageExecuted(strategyId, assets, amounts, actualProfit);
        } else {
            // Approve repayment even for failed executions to prevent flash loan revert
            IERC20(assets[0]).safeApprove(address(AAVE_POOL), totalRepayment);
              // Emit failure event
            emit ExecutionFailed(executionId, strategyAddress, errorReason);
        }
        
        // SECURITY: Clean up execution lock
        _executionLocked[executionId] = false;
        
        return true; // Always return true to avoid reverting the flash loan
    }

    // Function to initiate a flash loan
    function initiateFlashLoan(
        uint256 strategyId,
        address asset,
        uint256 amount
    ) external onlyRole(STRATEGY_EXECUTOR_ROLE) nonReentrant whenNotPaused circuitNotBroken gasProtection validStrategy(strategyId) {
        // Get strategy data
        IStrategyIncubator.IncubatedStrategy memory strategyData = STRATEGY_INCUBATOR.getStrategy(strategyId);
        address strategyAddress = strategyData.strategyAddress;
        
        // Generate execution ID
        bytes32 executionId = keccak256(
            abi.encodePacked(
                strategyAddress,
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
            strategy: strategyAddress,
            initiator: msg.sender,
            startTime: block.timestamp,
            endTime: 0,
            successful: false,
            profit: 0,
            executionHash: keccak256(abi.encodePacked(strategyId, asset, amount)),
            status: ExecutionStatus.InProgress
        });
        
        // Create arrays for flash loan parameters
        address[] memory assets = new address[](1);
        assets[0] = asset;
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        
        uint256[] memory modes = new uint256[](1);
        modes[0] = 0; // 0 = no debt, 1 = stable, 2 = variable
        
        // Encode strategy ID and execution ID as parameters
        bytes memory params = abi.encode(executionId, strategyId);
        
        // Initiate flash loan
        try AAVE_POOL.flashLoan(
            address(this),
            assets,
            amounts,
            modes,
            address(this),
            params,
            0 // referral code
        ) {
            // Flash loan initiated successfully
        } catch Error(string memory reason) {
            // Update execution status
            executionRegistry[executionId].status = ExecutionStatus.Failed;
            executionRegistry[executionId].endTime = block.timestamp;
            
            // Increment failed executions count
            _incrementFailedExecutions();
            
            emit ExecutionFailed(executionId, strategyAddress, reason);
        } catch {
            // Update execution status
            executionRegistry[executionId].status = ExecutionStatus.Failed;
            executionRegistry[executionId].endTime = block.timestamp;
            
            // Increment failed executions count
            _incrementFailedExecutions();
            
            emit ExecutionFailed(executionId, strategyAddress, "Unknown error");
        }
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
        
        // Check if circuit breaker threshold is reached
        if (failedExecutionsCount >= circuitBreakerThreshold) {
            circuitBroken = true;
            emit CircuitBroken(failedExecutionsCount, block.timestamp);
        }
    }

    // Fallback function to receive ETH
    receive() external payable {}
}