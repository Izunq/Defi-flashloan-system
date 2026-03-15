// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";
import "./interfaces/IAavePool.sol";
import "./interfaces/IFlashLoanSimpleReceiver.sol";
import "./interfaces/IGenericStrategy.sol";
import "./interfaces/IStrategyExecutor.sol";

interface IArbitrageExecutorV33 {
    function executeFlashLoan(address asset, uint256 amount, bytes calldata params) external;
    function depositProfit(address token, uint256 amount) external payable;
}

/**
 * @title GenericStrategy
 * @notice Enhanced base strategy for arbitrage execution
 * @dev Includes improved security features and access controls
 */
contract GenericStrategy is AccessControl, IFlashLoanSimpleReceiver, IGenericStrategy, IStrategyExecutor, ReentrancyGuard, Pausable, Ownable {
    using SafeERC20 for IERC20;
    using Math for uint256;

    // Role definitions
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");

        bytes32 public constant STRATEGY_EXECUTOR_ROLE = keccak256("STRATEGY_EXECUTOR_ROLE");

// Core contracts
    address public immutable EXECUTOR;
    address public immutable AAVE_POOL;
    address public immutable WETH;
    
    // Strategy configuration
    address public tokenA;
    address public tokenB;
    uint256 public minProfit;
    
    // Execution statistics
    address public lastCaller;
    uint256 public lastProfit;
    uint256 public lastExecutionTimestamp;
    uint256 public totalExecutions;
    uint256 public successfulExecutions;
    uint256 public totalProfit;
    
    // Execution limits
    uint256 public maxSlippageBps = 300; // 3% default max slippage
    uint256 public maxGasUsage = 2000000; // Maximum gas for execution
    
    // Circuit breakers
    uint256 public maxExecutionsPerHour = 5;
    uint256 public maxExecutionsPerDay = 20;
    uint256 public maxLossPercentage = 500; // 5% max loss in basis points
    uint256 public consecutiveFailures = 0;
    uint256 public maxConsecutiveFailures = 3;
    uint256 public lastHourExecutions = 0;
    uint256 public lastHourTimestamp = 0;
    uint256 public lastDayExecutions = 0;
    uint256 public lastDayTimestamp = 0;
    uint256 public totalLoss = 0;
    
    // Market condition circuit breakers
    uint256 public maxPriceDeviationBps = 1000; // 10% max price deviation
    uint256 public baselinePrice = 0;
    uint256 public lastPriceUpdate = 0;
    uint256 public priceUpdateInterval = 1 hours;
    
    // Initialization state
    bool public initialized;
    
    // Timelock for critical operations
    uint256 public constant TIMELOCK_PERIOD = 24 hours;
    mapping(bytes32 => uint256) public timelockExpirations;

    // Events
    event ArbitrageExecuted(
        address indexed caller, 
        uint256 profit, 
        uint256 timestamp,
        uint256 gasUsed
    );
    event StrategyConfigured(
        address indexed tokenA, 
        address indexed tokenB, 
        uint256 minProfit,
        uint256 maxSlippageBps
    );
    event StrategyInitialized(
        address indexed executor, 
        address indexed owner
    );
    event TimelockInitiated(
        bytes32 indexed operationId, 
        string operation, 
        uint256 executeAfter
    );
    event TimelockExecuted(
        bytes32 indexed operationId, 
        string operation
    );
    event TimelockCancelled(
        bytes32 indexed operationId, 
        string operation
    );
    event EmergencyWithdrawal(
        address indexed token, 
        address indexed to, 
        uint256 amount
    );

    /**
     * @dev Modifier to check if the contract is initialized
     */
    modifier onlyInitialized() {
        require(initialized, "Strategy: Not initialized");
        _;
    }

    /**
     * @dev Constructor
     * @param _executor Address of the executor contract
     * @param _aavePool Address of the Aave lending pool
     * @param _weth Address of WETH
     * @param _admin Address of the admin
     */    constructor(
        address _executor, 
        address _aavePool, 
        address _weth,
        address _admin
    ) Ownable(_admin) {
        require(_executor != address(0), "Strategy: Zero executor address");
        require(_aavePool != address(0), "Strategy: Zero pool address");
        require(_weth != address(0), "Strategy: Zero WETH address");
        require(_admin != address(0), "Strategy: Zero admin address");
        
        EXECUTOR = _executor;
        AAVE_POOL = _aavePool;
        WETH = _weth;
          // Setup roles
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(OPERATOR_ROLE, _admin);
        _grantRole(EMERGENCY_ROLE, _admin);
        _grantRole(EXECUTOR_ROLE, _executor);
        
        emit StrategyInitialized(_executor, _admin);
    }

    /**
     * @dev Initialize strategy (called by factory)
     * @param _tokenA First token in the trading pair
     * @param _tokenB Second token in the trading pair
     * @param _minProfit Minimum profit threshold
     * @param _executor Address of the executor contract
     */
    function initialize(
        address _tokenA,
        address _tokenB,
        uint256 _minProfit,
        address _executor
    ) external override onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(!initialized, "Strategy: Already initialized");
        require(_executor == EXECUTOR, "Strategy: Invalid executor");
        require(_tokenA != address(0) && _tokenB != address(0), "Strategy: Zero token address");
        require(_minProfit > 0, "Strategy: Invalid min profit");
        
        tokenA = _tokenA;
        tokenB = _tokenB;
        minProfit = _minProfit;
        initialized = true;
        
        emit StrategyConfigured(_tokenA, _tokenB, _minProfit, maxSlippageBps);
    }

    /**
     * @dev Configure strategy parameters
     * @param _tokenA First token in the trading pair
     * @param _tokenB Second token in the trading pair
     * @param _minProfit Minimum profit threshold
     * @param _maxSlippageBps Maximum slippage in basis points
     */
    function configure(
        address _tokenA, 
        address _tokenB, 
        uint256 _minProfit,
        uint256 _maxSlippageBps
    ) external onlyRole(DEFAULT_ADMIN_ROLE) onlyInitialized whenNotPaused  nonReentrant{
        require(_tokenA != address(0) && _tokenB != address(0), "Strategy: Zero token address");
        require(_minProfit > 0, "Strategy: Invalid min profit");
        require(_maxSlippageBps <= 1000, "Strategy: Slippage too high"); // Max 10%
        
        tokenA = _tokenA;
        tokenB = _tokenB;
        minProfit = _minProfit;
        maxSlippageBps = _maxSlippageBps;
        
        emit StrategyConfigured(_tokenA, _tokenB, _minProfit, _maxSlippageBps);
    }

    /**
     * @dev Start arbitrage execution
     * @param _asset The asset to borrow
     * @param _amount The amount to borrow
     * @param _params Additional parameters for the strategy
     */
    function startArbitrage(
        address _asset, 
        uint256 _amount, 
        bytes calldata _params
    ) external onlyRole(OPERATOR_ROLE) onlyInitialized nonReentrant whenNotPaused {
        require(_asset != address(0), "Strategy: Zero asset address");
        require(_amount > 0, "Strategy: Invalid amount");
        
        IArbitrageExecutorV33(EXECUTOR).executeFlashLoan(_asset, _amount, _params);
    }

    /**
     * @dev Check circuit breakers before execution
     * @param currentPrice Current price for market condition check
     * @return True if all circuit breakers pass
     */
    function _checkCircuitBreakers(uint256 currentPrice) internal returns (bool) {
        // Check execution frequency limits
        if (lastHourTimestamp + 1 hours < block.timestamp) {
            lastHourTimestamp = block.timestamp;
            lastHourExecutions = 0;
        } else {
            require(lastHourExecutions < maxExecutionsPerHour, "Strategy: Hourly execution limit reached");
            lastHourExecutions++;
        }
        
        if (lastDayTimestamp + 1 days < block.timestamp) {
            lastDayTimestamp = block.timestamp;
            lastDayExecutions = 0;
        } else {
            require(lastDayExecutions < maxExecutionsPerDay, "Strategy: Daily execution limit reached");
            lastDayExecutions++;
        }
        
        // Check consecutive failures
        require(consecutiveFailures < maxConsecutiveFailures, "Strategy: Too many consecutive failures");
        
        // Check market conditions
        if (baselinePrice > 0) {
            uint256 deviation;
            if (currentPrice > baselinePrice) {
                deviation = ((currentPrice - baselinePrice) * 10000) / baselinePrice;
            } else {
                deviation = ((baselinePrice - currentPrice) * 10000) / baselinePrice;
            }
            require(deviation <= maxPriceDeviationBps, "Strategy: Price deviation too high");
        }
        
        // Update baseline price if needed
        if (lastPriceUpdate + priceUpdateInterval < block.timestamp) {
            baselinePrice = currentPrice;
            lastPriceUpdate = block.timestamp;
        }
        
        return true;
    }

    /**
     * @dev Execute strategy (called by ProofAwareExecutorV35)
     * @param asset The asset that was borrowed
     * @param amount The amount that was borrowed
     * @param premium The fee that needs to be paid
     * @param executionData The data for strategy execution
     * @return True if the execution is successful
     */
    function executeStrategy(
        address asset,
        uint256 amount,
        uint256 premium,
        bytes memory executionData
    ) external override onlyRole(EXECUTOR_ROLE) onlyInitialized nonReentrant whenNotPaused returns (bool) {
        // Record gas at start
        uint256 gasStart = gasleft();
        
        // Decode arbitrage parameters
        (uint256 maxSlippage, uint256 currentPrice, bytes memory arbitrageData) = 
            abi.decode(executionData, (uint256, uint256, bytes));
        
        // Check circuit breakers
        require(_checkCircuitBreakers(currentPrice), "Strategy: Circuit breaker triggered");
          // Use the lower of the two slippage values
        uint256 effectiveMaxSlippage = maxSlippage < maxSlippageBps ? maxSlippage : maxSlippageBps;
        
        // Perform arbitrage logic
        uint256 profit = _performArbitrage(asset, amount, tokenA, tokenB, effectiveMaxSlippage, arbitrageData);
        
        // Validate profit meets minimum threshold
        require(profit >= minProfit, "Strategy: Insufficient profit");
        
        // Calculate total repayment amount
        uint256 totalRepayment = amount + premium;
        
        // Ensure we have enough to repay the loan
        uint256 balance = IERC20(asset).balanceOf(address(this));
        require(balance >= totalRepayment, "Strategy: Insufficient balance for repayment");
        
        // Transfer repayment amount back to executor
        IERC20(asset).safeTransfer(msg.sender, totalRepayment);
          // Send remaining profit to executor
        uint256 remainingProfit = balance - totalRepayment;
        if (remainingProfit > 0) {
            IERC20(asset).safeTransfer(msg.sender, remainingProfit);
        }
        
        // Calculate gas used
        uint256 gasUsed = gasStart - gasleft();
        require(gasUsed <= maxGasUsage, "Strategy: Gas usage too high");
        
        // Update state
        lastCaller = msg.sender /* SECURITY FIX: Changed from tx.origin to prevent phishing attacks */;
        lastProfit = profit;
        lastExecutionTimestamp = block.timestamp;
        totalExecutions++;
        successfulExecutions++;
        totalProfit += profit;
        consecutiveFailures = 0; // Reset consecutive failures
        
        emit ArbitrageExecuted(msg.sender /* SECURITY FIX: Changed from tx.origin to prevent phishing attacks */, profit, block.timestamp, gasUsed);
        
        return true;
            revert("Strategy: Execution failed");
        }
    }

    /**
     * @dev Aave V3 flash loan callback
     * @param asset The asset that was borrowed
     * @param amount The amount that was borrowed
     * @param premium The fee that needs to be paid
     * @param initiator The address that initiated the flash loan
     * @param params The parameters for strategy execution
     * @return true if the execution is successful
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override onlyInitialized nonReentrant whenNotPaused returns (bool)  {
        // TODO: Add nonReentrant modifier
        require(msg.sender == AAVE_POOL, "Strategy: Not Aave pool");
        require(initiator == EXECUTOR, "Strategy: Invalid initiator");
        
        // Record gas at start
        uint256 gasStart = gasleft();
        
        // Decode arbitrage parameters
        (address _tokenA, address _tokenB, uint256 _minProfit, uint256 _maxSlippage, uint256 currentPrice, bytes memory arbitrageData) = 
            abi.decode(params, (address, address, uint256, uint256, uint256, bytes));
        
        // Check circuit breakers
        require(_checkCircuitBreakers(currentPrice), "Strategy: Circuit breaker triggered");
          // Use the lower of the two slippage values
        uint256 effectiveMaxSlippage = _maxSlippage < maxSlippageBps ? _maxSlippage : maxSlippageBps;
        
        // Perform arbitrage logic
        uint256 profit = _performArbitrage(asset, amount, _tokenA, _tokenB, effectiveMaxSlippage, arbitrageData);
            
            // Validate profit meets minimum threshold
            require(profit >= _minProfit, "Strategy: Insufficient profit");
            
            // Calculate total repayment amount
            uint256 totalRepayment = amount + premium;
            
            // Ensure we have enough to repay the loan
            uint256 balance = IERC20(asset).balanceOf(address(this));
            require(balance >= totalRepayment, "Strategy: Insufficient balance for repayment");
            
            // Approve the lending pool to pull the repayment amount        IERC20(asset).safeApprove(AAVE_POOL, totalRepayment);
        
        // Send profit to executor
        uint256 remainingProfit = balance - totalRepayment;
        if (remainingProfit > 0) {
            IERC20(asset).safeApprove(EXECUTOR, remainingProfit);
            IArbitrageExecutorV33(EXECUTOR).depositProfit(asset, remainingProfit);
        }
        
        // Calculate gas used
        uint256 gasUsed = gasStart - gasleft();
        require(gasUsed <= maxGasUsage, "Strategy: Gas usage too high");
        
        // Update state
        lastCaller = msg.sender /* SECURITY FIX: Changed from tx.origin to prevent phishing attacks */;
        lastProfit = profit;
        lastExecutionTimestamp = block.timestamp;
        totalExecutions++;
        successfulExecutions++;
        totalProfit += profit;
        consecutiveFailures = 0; // Reset consecutive failures
          emit ArbitrageExecuted(msg.sender /* SECURITY FIX: Changed from tx.origin to prevent phishing attacks */, profit, block.timestamp, gasUsed);
        
        return true;
    }

    /**
     * @dev Emergency pause function
     */
    function emergencyPause() external onlyRole(EMERGENCY_ROLE)  {
        // TODO: Add nonReentrant modifier
        _pause();
        emit EmergencyWithdrawal(address(0), msg.sender, 0); // Special event to indicate emergency pause
    }
    
    /**
     * @dev Emergency unpause function
     */
    function emergencyUnpause() external onlyRole(EMERGENCY_ROLE)  {
        // TODO: Add nonReentrant modifier
        _unpause();
    }
    
    /**
     * @dev Emergency withdrawal function
     * @param token Token to withdraw
     * @param to Address to send tokens to
     */
    function emergencyWithdraw(address token, address to) external onlyRole(EMERGENCY_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(to != address(0), "Strategy: Zero address");
        
        uint256 balance;
        if (token == address(0)) {
            // ETH withdrawal
            balance = address(this).balance;
            require(balance > 0, "Strategy: No ETH balance");
            
            (bool success, ) = to.call{value: balance}("");
            require(success, "Strategy: ETH transfer failed");
        } else {
            // ERC20 withdrawal
            balance = IERC20(token).balanceOf(address(this));
            require(balance > 0, "Strategy: No token balance");
            
            IERC20(token).safeTransfer(to, balance);
        }
        
        emit EmergencyWithdrawal(token, to, balance);
    }
    
    /**
     * @dev Update circuit breaker parameters
     * @param _maxExecutionsPerHour Maximum executions per hour
     * @param _maxExecutionsPerDay Maximum executions per day
     * @param _maxLossPercentage Maximum loss percentage in basis points
     * @param _maxConsecutiveFailures Maximum consecutive failures
     * @param _maxPriceDeviationBps Maximum price deviation in basis points
     */
    function updateCircuitBreakers(
        uint256 _maxExecutionsPerHour,
        uint256 _maxExecutionsPerDay,
        uint256 _maxLossPercentage,
        uint256 _maxConsecutiveFailures,
        uint256 _maxPriceDeviationBps
    ) external onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_maxExecutionsPerHour > 0, "Strategy: Invalid hourly limit");
        require(_maxExecutionsPerDay > 0, "Strategy: Invalid daily limit");
        require(_maxLossPercentage <= 1000, "Strategy: Loss percentage too high"); // Max 10%
        require(_maxConsecutiveFailures > 0, "Strategy: Invalid failure limit");
        require(_maxPriceDeviationBps <= 2000, "Strategy: Deviation too high"); // Max 20%
        
        maxExecutionsPerHour = _maxExecutionsPerHour;
        maxExecutionsPerDay = _maxExecutionsPerDay;
        maxLossPercentage = _maxLossPercentage;
        maxConsecutiveFailures = _maxConsecutiveFailures;
        maxPriceDeviationBps = _maxPriceDeviationBps;
    }

    /**
     * @dev Internal arbitrage logic
     * @param asset The asset that was borrowed
     * @param amount The amount that was borrowed
     * @param _tokenA First token in the trading pair
     * @param _tokenB Second token in the trading pair
     * @param _maxSlippageBps Maximum slippage in basis points
     * @param arbitrageData Additional data for arbitrage execution
     * @return profit The profit generated
     */
    function _performArbitrage(
        address asset,
        uint256 amount,
        address _tokenA,
        address _tokenB,
        uint256 _maxSlippageBps,
        bytes memory arbitrageData
    ) internal virtual returns (uint256 profit) {
        // This is a base implementation that should be overridden by specific strategies
        // In a real implementation, this would execute DEX trades
        
        // For demonstration, we simulate a profitable trade with slippage check
        uint256 expectedProfit = minProfit + (amount * 1) / 1000; // 0.1% mock profit
        
        // Apply simulated slippage
        uint256 slippage = (_maxSlippageBps * expectedProfit) / 10000;
        profit = expectedProfit - slippage;
        
        // In a real implementation, this would come from DEX trades
        // This is just for testing - remove in production
        return profit;
    }

    /**
     * @dev Initiate timelock for emergency withdrawal
     * @param _token The token to withdraw
     * @param _amount The amount to withdraw
     * @param _recipient The recipient address
     */
    function initiateEmergencyWithdrawal(
        address _token,
        uint256 _amount,
        address _recipient
    ) external onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_recipient != address(0), "Strategy: Zero recipient address");
        require(_amount > 0, "Strategy: Invalid amount");
        
        bytes32 operationId = keccak256(abi.encodePacked(
            "emergencyWithdraw",
            _token,
            _amount,
            _recipient
        ));
        
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, "emergencyWithdraw", timelockExpirations[operationId]);
    }
    
    /**
     * @dev Execute timelock for emergency withdrawal
     * @param _token The token to withdraw
     * @param _amount The amount to withdraw
     * @param _recipient The recipient address
     */
    function executeEmergencyWithdrawal(
        address _token,
        uint256 _amount,
        address _recipient
    ) external onlyRole(DEFAULT_ADMIN_ROLE) nonReentrant {
        bytes32 operationId = keccak256(abi.encodePacked(
            "emergencyWithdraw",
            _token,
            _amount,
            _recipient
        ));
        
        require(timelockExpirations[operationId] > 0, "Strategy: Timelock not initiated");
        require(block.timestamp >= timelockExpirations[operationId], "Strategy: Timelock not expired");
        
        if (_token == address(0)) {
            // Native ETH withdrawal
            require(address(this).balance >= _amount, "Strategy: Insufficient ETH balance");
            payable(_recipient).transfer(_amount);
        } else {
            // ERC20 token withdrawal
            require(IERC20(_token).balanceOf(address(this)) >= _amount, "Strategy: Insufficient token balance");
            IERC20(_token).safeTransfer(_recipient, _amount);
        }
        
        delete timelockExpirations[operationId];
        
        emit TimelockExecuted(operationId, "emergencyWithdraw");
        emit EmergencyWithdrawal(_token, _recipient, _amount);
    }
    
    /**
     * @dev Immediate emergency withdrawal (only when paused)
     * @param _token The token to withdraw
     * @param _recipient The recipient address
     */
    function immediateEmergencyWithdraw(
        address _token,
        address _recipient
    ) external onlyRole(EMERGENCY_ROLE) nonReentrant whenPaused {
        require(_recipient != address(0), "Strategy: Zero recipient address");
        
        uint256 balance;
        if (_token == address(0)) {
            // Native ETH withdrawal
            balance = address(this).balance;
            require(balance > 0, "Strategy: No ETH to withdraw");
            payable(_recipient).transfer(balance);
        } else {
            // ERC20 token withdrawal
            balance = IERC20(_token).balanceOf(address(this));
            require(balance > 0, "Strategy: No tokens to withdraw");
            IERC20(_token).safeTransfer(_recipient, balance);
        }
        
        emit EmergencyWithdrawal(_token, _recipient, balance);
    }
    
    /**
     * @dev Cancel a timelock operation
     * @param _operationId The operation ID to cancel
     */
    function cancelTimelock(bytes32 _operationId) external onlyRole(DEFAULT_ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(timelockExpirations[_operationId] > 0, "Strategy: Timelock not initiated");
        
        delete timelockExpirations[_operationId];
        
        emit TimelockCancelled(_operationId, "Operation cancelled");
    }
    
    /**
     * @dev Pause the contract
     */
    function pause() external onlyRole(EMERGENCY_ROLE) nonReentrant onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause the contract
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) nonReentrant onlyOwner {
        _unpause();
    }

    /**
     * @dev Get strategy configuration
     * @return First token in the trading pair
     * @return Second token in the trading pair
     * @return Minimum profit threshold
     * @return Address of the executor contract
     */
    function getConfiguration() external view override returns (
        address,
        address,
        uint256,
        address
    ) {
        return (tokenA, tokenB, minProfit, EXECUTOR);
    }

    /**
     * @dev Get last execution results
     * @return Last caller address
     * @return Last profit amount
     * @return Last execution timestamp
     */
    function getLastExecution() external view override returns (
        address,
        uint256,
        uint256
    ) {
        return (lastCaller, lastProfit, lastExecutionTimestamp);
    }

    /**
     * @dev Get strategy performance metrics
     * @return Total number of executions
     * @return Number of successful executions
     * @return Success rate in basis points
     * @return Total profit generated
     */
    function getPerformanceMetrics() external view returns (
        uint256,
        uint256,
        uint256,
        uint256
    ) {
        uint256 successRate = totalExecutions > 0 
            ? (successfulExecutions * 10000) / totalExecutions 
            : 0;
            
        return (
            totalExecutions,
            successfulExecutions,
            successRate,
            totalProfit
        );
    }

    /**
     * @dev Check if strategy is configured
     * @return True if the strategy is configured
     */    function isConfigured() external view override returns (bool)  {
        // TODO: Add nonReentrant modifier
        return initialized && tokenA != address(0) && tokenB != address(0) && minProfit > 0;
    }

    /**
     * @dev Receive ETH
     */
    receive() external payable {}
}
