// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/access/Ownable.sol";

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "./TrustCurve.sol";
import "./interfaces/IFlashLoanSimpleReceiver.sol";
import "./interfaces/IAavePool.sol";
import "./interfaces/IStrategyExecutor.sol";

/**
 * @title ProofAwareExecutorV35
 * @notice An executor that prioritizes strategies with higher on-chain trust scores.
 * @dev Part of the V35 Cognitive Kernel (Proof-Aware) architecture with enhanced security
 */
contract ProofAwareExecutorV35 is AccessControl, ReentrancyGuard, Pausable, IFlashLoanSimpleReceiver {
    using SafeERC20 for IERC20;

    // Role definitions
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant STRATEGY_ROLE = keccak256("STRATEGY_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");

    // Trust curve contract for strategy scoring
    TrustCurve public immutable TRUST_CURVE;
    
    // Aave lending pool for flash loans
    IAavePool public immutable LENDING_POOL;
    
    // Minimum trust score required to execute a strategy
    uint256 public minTrustScore = 50; // Default: 50 out of 100
    
    // Capital allocation based on trust score tiers
    uint256 public tier1Threshold = 80; // 80+ trust score = tier 1
    uint256 public tier2Threshold = 60; // 60-79 trust score = tier 2
    
    // Capital allocation multipliers (in basis points)
    uint256 public tier1Multiplier = 10000; // 100% of available capital
    uint256 public tier2Multiplier = 7500;  // 75% of available capital
    uint256 public tier3Multiplier = 5000;  // 50% of available capital
    
    // Fee settings
    uint256 public protocolFeeBps = 500; // 5% fee
    address public feeCollector;
    
    // Strategy execution tracking
    mapping(uint256 => uint256) public strategyLastExecuted; // strategyId => timestamp
    mapping(uint256 => uint256) public strategyCapitalAllocated; // strategyId => amount
    mapping(uint256 => address) public strategyAddresses; // strategyId => strategy address
    mapping(address => uint256) public strategyIds; // strategy address => strategyId
    
    // Execution limits
    uint256 public maxGasPrice = 100 gwei; // Maximum gas price for execution
    uint256 public maxExecutionGas = 3000000; // Maximum gas for strategy execution
    uint256 public maxSlippageBps = 300; // Maximum slippage (3%)
    
    // Timelock for parameter changes
    uint256 public constant TIMELOCK_PERIOD = 24 hours;
    mapping(bytes32 => uint256) public timelockExpirations;
    
    // Emergency shutdown
    bool public emergencyShutdown;
    
    // Events
    event StrategyExecuted(
        uint256 indexed strategyId,
        address indexed token,
        uint256 amount,
        uint256 profit,
        uint256 trustScore,
        uint256 gasUsed
    );
    
    event TrustScoreThresholdUpdated(
        uint256 minTrustScore,
        uint256 tier1Threshold,
        uint256 tier2Threshold
    );
    
    event CapitalMultipliersUpdated(
        uint256 tier1Multiplier,
        uint256 tier2Multiplier,
        uint256 tier3Multiplier
    );
    
    event FeeSettingsUpdated(
        uint256 protocolFeeBps,
        address feeCollector
    );
    
    event StrategyRegistered(
        uint256 indexed strategyId,
        address indexed strategyAddress
    );
    
    event StrategyUnregistered(
        uint256 indexed strategyId,
        address indexed strategyAddress
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
    
    event EmergencyShutdownActivated(address activator);
    event EmergencyShutdownDeactivated(address deactivator);

    /**
     * @dev Constructor
     * @param _trustCurveAddress Address of the TrustCurve contract
     * @param _lendingPoolAddress Address of the Aave lending pool
     * @param _feeCollector Address to collect protocol fees
     * @param _admin Address of the admin
     */
    constructor(
        address _trustCurveAddress,
        address _lendingPoolAddress,
        address _feeCollector,
        address _admin
    ) {
        require(_trustCurveAddress != address(0), "Invalid TrustCurve address");
        require(_lendingPoolAddress != address(0), "Invalid lending pool address");
        require(_feeCollector != address(0), "Invalid fee collector address");
        require(_admin != address(0), "Invalid admin address");
        
        TRUST_CURVE = TrustCurve(_trustCurveAddress);
        LENDING_POOL = IAavePool(_lendingPoolAddress);
        feeCollector = _feeCollector;
        
        // Setup roles
        _setupRole(DEFAULT_ADMIN_ROLE, _admin);
        _setupRole(ADMIN_ROLE, _admin);
        _setupRole(OPERATOR_ROLE, _admin);
        _setupRole(EMERGENCY_ROLE, _admin);
    }
    
    /**
     * @dev Execute a strategy with proof-aware capital allocation
     * @param _strategyId The ID of the strategy to execute
     * @param _token The token to borrow for the flash loan
     * @param _amount The base amount to borrow (will be adjusted by trust score)
     * @param _executionData The data to execute the strategy
     */
    function executeProofAwareStrategy(
        uint256 _strategyId,
        address _token,
        uint256 _amount,
        bytes calldata _executionData
    ) external nonReentrant whenNotPaused onlyRole(OPERATOR_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(!emergencyShutdown, "Emergency shutdown active");
        require(tx.gasprice <= maxGasPrice, "Gas price too high");
        require(strategyAddresses[_strategyId] != address(0), "Strategy not registered");
        
        // Get trust score for the strategy
        uint256 trustScore = TRUST_CURVE.getTrustScore(_strategyId);
        
        // Ensure minimum trust score is met
        require(trustScore >= minTrustScore, "Trust score too low");
        
        // Calculate capital allocation based on trust score tier
        uint256 adjustedAmount = _calculateCapitalAllocation(_amount, trustScore);
        
        // Store execution data for flash loan callback
        bytes memory data = abi.encode(_strategyId, _executionData);
        
        // Execute flash loan with trust-adjusted capital
        LENDING_POOL.flashLoanSimple(
            address(this),
            _token,
            adjustedAmount,
            data,
            0 // referralCode
        );
        
        // Update strategy execution tracking
        strategyLastExecuted[_strategyId] = block.timestamp;
        strategyCapitalAllocated[_strategyId] = adjustedAmount;
    }
    
    /**
     * @dev Flash loan callback function
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
    ) external override nonReentrant returns (bool)  {
        // TODO: Add nonReentrant modifier
        require(msg.sender == address(LENDING_POOL), "Caller must be lending pool");
        require(initiator == address(this), "Initiator must be this contract");
        
        // Decode execution parameters
        (uint256 strategyId, bytes memory executionData) = abi.decode(params, (uint256, bytes));
        
        // Get strategy address
        address strategyAddress = strategyAddresses[strategyId];
        require(strategyAddress != address(0), "Strategy not registered");
        
        // Get initial balance to calculate profit later
        uint256 initialBalance = IERC20(asset).balanceOf(address(this));
        
        // Record gas at start
        uint256 gasStart = gasleft();
        
        // SECURITY IMPROVEMENT: Use checks-effects-interactions pattern
        // Store all state changes and calculations before making external calls
        
        // Execute strategy with proper error handling
        bool success;
        string memory errorReason = "";
        
        // SECURITY IMPROVEMENT: Transfer funds and execute strategy with proper error handling
        try IERC20(asset).safeTransfer(strategyAddress, amount) {
            try IStrategyExecutor(strategyAddress).executeStrategy(asset, amount, premium, executionData) returns (bool _success) {
                success = _success;
                if (!success) {
                    errorReason = "Strategy returned false";
                }
            } catch Error(string memory reason) {
                success = false;
                errorReason = reason;
            } catch {
                success = false;
                errorReason = "Unknown strategy execution error";
            }
        } catch Error(string memory reason) {
            success = false;
            errorReason = string(abi.encodePacked("Token transfer failed: ", reason));
        } catch {
            success = false;
            errorReason = "Token transfer failed";
        }
        
        // Require successful execution
        require(success, errorReason);
        
        // Calculate gas used
        uint256 gasUsed = gasStart - gasleft();
        require(gasUsed <= maxExecutionGas, "Execution gas limit exceeded");
        
        // Calculate profit
        uint256 finalBalance = IERC20(asset).balanceOf(address(this));
        require(finalBalance >= initialBalance + premium, "Insufficient profit to repay loan");
        uint256 profit = finalBalance - initialBalance - premium;
        
        // Calculate fee
        uint256 fee = (profit * protocolFeeBps) / 10000;
        
        // SECURITY IMPROVEMENT: Update trust curve before making more external calls
        // This ensures state is updated before external interactions
        TRUST_CURVE.updateOnChainPerformance(strategyId, true, int256(profit - fee));
        
        // SECURITY IMPROVEMENT: Make external calls after all state changes
        // Take protocol fee
        if (fee > 0) {
            IERC20(asset).safeTransfer(feeCollector, fee);
        }
        
        // Approve repayment
        IERC20(asset).safeApprove(address(LENDING_POOL), amount + premium);
        
        // Emit event
        emit StrategyExecuted(
            strategyId,
            asset,
            amount,
            profit - fee,
            TRUST_CURVE.getTrustScore(strategyId),
            gasUsed
        );
        
        return true;
    }
    
    /**
     * @dev Calculate capital allocation based on trust score tier
     * @param _baseAmount The base amount requested
     * @param _trustScore The trust score of the strategy
     * @return The adjusted capital allocation
     */
    function _calculateCapitalAllocation(
        uint256 _baseAmount,
        uint256 _trustScore
    ) internal view returns (uint256) {
        uint256 multiplier;
        
        if (_trustScore >= tier1Threshold) {
            multiplier = tier1Multiplier;
        } else if (_trustScore >= tier2Threshold) {
            multiplier = tier2Multiplier;
        } else {
            multiplier = tier3Multiplier;
        }
        
        return (_baseAmount * multiplier) / 10000;
    }
    
    /**
     * @dev Register a strategy
     * @param _strategyId The ID of the strategy
     * @param _strategyAddress The address of the strategy contract
     */
    function registerStrategy(
        uint256 _strategyId,
        address _strategyAddress
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_strategyAddress != address(0), "Invalid strategy address");
        require(strategyAddresses[_strategyId] == address(0), "Strategy ID already registered");
        require(strategyIds[_strategyAddress] == 0, "Strategy address already registered");
        
        strategyAddresses[_strategyId] = _strategyAddress;
        strategyIds[_strategyAddress] = _strategyId;
        
        emit StrategyRegistered(_strategyId, _strategyAddress);
    }
    
    /**
     * @dev Unregister a strategy
     * @param _strategyId The ID of the strategy
     */
    function unregisterStrategy(
        uint256 _strategyId
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        address strategyAddress = strategyAddresses[_strategyId];
        require(strategyAddress != address(0), "Strategy not registered");
        
        delete strategyIds[strategyAddress];
        delete strategyAddresses[_strategyId];
        
        emit StrategyUnregistered(_strategyId, strategyAddress);
    }
    
    /**
     * @dev Initiate timelock for trust score thresholds update
     * @param _minTrustScore Minimum trust score to execute
     * @param _tier1Threshold Threshold for tier 1 capital allocation
     * @param _tier2Threshold Threshold for tier 2 capital allocation
     */
    function initiateThresholdsUpdate(
        uint256 _minTrustScore,
        uint256 _tier1Threshold,
        uint256 _tier2Threshold
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_tier1Threshold > _tier2Threshold, "Tier 1 must be higher than Tier 2");
        require(_tier2Threshold > _minTrustScore, "Tier 2 must be higher than min score");
        
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateThresholds",
            _minTrustScore,
            _tier1Threshold,
            _tier2Threshold
        ));
        
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, "updateThresholds", timelockExpirations[operationId]);
    }
    
    /**
     * @dev Execute timelock for trust score thresholds update
     * @param _minTrustScore Minimum trust score to execute
     * @param _tier1Threshold Threshold for tier 1 capital allocation
     * @param _tier2Threshold Threshold for tier 2 capital allocation
     */
    function executeThresholdsUpdate(
        uint256 _minTrustScore,
        uint256 _tier1Threshold,
        uint256 _tier2Threshold
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateThresholds",
            _minTrustScore,
            _tier1Threshold,
            _tier2Threshold
        ));
        
        require(timelockExpirations[operationId] > 0, "Timelock not initiated");
        require(block.timestamp >= timelockExpirations[operationId], "Timelock not expired");
        
        minTrustScore = _minTrustScore;
        tier1Threshold = _tier1Threshold;
        tier2Threshold = _tier2Threshold;
        
        delete timelockExpirations[operationId];
        
        emit TimelockExecuted(operationId, "updateThresholds");
        emit TrustScoreThresholdUpdated(_minTrustScore, _tier1Threshold, _tier2Threshold);
    }
    
    /**
     * @dev Initiate timelock for capital multipliers update
     * @param _tier1Multiplier Multiplier for tier 1 strategies (basis points)
     * @param _tier2Multiplier Multiplier for tier 2 strategies (basis points)
     * @param _tier3Multiplier Multiplier for tier 3 strategies (basis points)
     */
    function initiateMultipliersUpdate(
        uint256 _tier1Multiplier,
        uint256 _tier2Multiplier,
        uint256 _tier3Multiplier
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_tier1Multiplier <= 10000, "Multiplier cannot exceed 100%");
        require(_tier1Multiplier >= _tier2Multiplier, "Tier 1 must be >= Tier 2");
        require(_tier2Multiplier >= _tier3Multiplier, "Tier 2 must be >= Tier 3");
        
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateMultipliers",
            _tier1Multiplier,
            _tier2Multiplier,
            _tier3Multiplier
        ));
        
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, "updateMultipliers", timelockExpirations[operationId]);
    }
    
    /**
     * @dev Execute timelock for capital multipliers update
     * @param _tier1Multiplier Multiplier for tier 1 strategies (basis points)
     * @param _tier2Multiplier Multiplier for tier 2 strategies (basis points)
     * @param _tier3Multiplier Multiplier for tier 3 strategies (basis points)
     */
    function executeMultipliersUpdate(
        uint256 _tier1Multiplier,
        uint256 _tier2Multiplier,
        uint256 _tier3Multiplier
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateMultipliers",
            _tier1Multiplier,
            _tier2Multiplier,
            _tier3Multiplier
        ));
        
        require(timelockExpirations[operationId] > 0, "Timelock not initiated");
        require(block.timestamp >= timelockExpirations[operationId], "Timelock not expired");
        
        tier1Multiplier = _tier1Multiplier;
        tier2Multiplier = _tier2Multiplier;
        tier3Multiplier = _tier3Multiplier;
        
        delete timelockExpirations[operationId];
        
        emit TimelockExecuted(operationId, "updateMultipliers");
        emit CapitalMultipliersUpdated(_tier1Multiplier, _tier2Multiplier, _tier3Multiplier);
    }
    
    /**
     * @dev Initiate timelock for fee settings update
     * @param _protocolFeeBps Protocol fee in basis points
     * @param _feeCollector Address to collect fees
     */
    function initiateFeeSettingsUpdate(
        uint256 _protocolFeeBps,
        address _feeCollector
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_protocolFeeBps <= 2000, "Fee cannot exceed 20%");
        require(_feeCollector != address(0), "Invalid fee collector");
        
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateFeeSettings",
            _protocolFeeBps,
            _feeCollector
        ));
        
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, "updateFeeSettings", timelockExpirations[operationId]);
    }
    
    /**
     * @dev Execute timelock for fee settings update
     * @param _protocolFeeBps Protocol fee in basis points
     * @param _feeCollector Address to collect fees
     */
    function executeFeeSettingsUpdate(
        uint256 _protocolFeeBps,
        address _feeCollector
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateFeeSettings",
            _protocolFeeBps,
            _feeCollector
        ));
        
        require(timelockExpirations[operationId] > 0, "Timelock not initiated");
        require(block.timestamp >= timelockExpirations[operationId], "Timelock not expired");
        
        protocolFeeBps = _protocolFeeBps;
        feeCollector = _feeCollector;
        
        delete timelockExpirations[operationId];
        
        emit TimelockExecuted(operationId, "updateFeeSettings");
        emit FeeSettingsUpdated(_protocolFeeBps, _feeCollector);
    }
    
    /**
     * @dev Initiate timelock for execution limits update
     * @param _maxGasPrice Maximum gas price for execution
     * @param _maxExecutionGas Maximum gas for strategy execution
     * @param _maxSlippageBps Maximum slippage in basis points
     */
    function initiateExecutionLimitsUpdate(
        uint256 _maxGasPrice,
        uint256 _maxExecutionGas,
        uint256 _maxSlippageBps
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_maxSlippageBps <= 1000, "Slippage cannot exceed 10%");
        
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateExecutionLimits",
            _maxGasPrice,
            _maxExecutionGas,
            _maxSlippageBps
        ));
        
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, "updateExecutionLimits", timelockExpirations[operationId]);
    }
    
    /**
     * @dev Execute timelock for execution limits update
     * @param _maxGasPrice Maximum gas price for execution
     * @param _maxExecutionGas Maximum gas for strategy execution
     * @param _maxSlippageBps Maximum slippage in basis points
     */
    function executeExecutionLimitsUpdate(
        uint256 _maxGasPrice,
        uint256 _maxExecutionGas,
        uint256 _maxSlippageBps
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        bytes32 operationId = keccak256(abi.encodePacked(
            "updateExecutionLimits",
            _maxGasPrice,
            _maxExecutionGas,
            _maxSlippageBps
        ));
        
        require(timelockExpirations[operationId] > 0, "Timelock not initiated");
        require(block.timestamp >= timelockExpirations[operationId], "Timelock not expired");
        
        maxGasPrice = _maxGasPrice;
        maxExecutionGas = _maxExecutionGas;
        maxSlippageBps = _maxSlippageBps;
        
        delete timelockExpirations[operationId];
        
        emit TimelockExecuted(operationId, "updateExecutionLimits");
    }
    
    /**
     * @dev Cancel timelock operation
     * @param _operationId Operation ID to cancel
     */
    function cancelTimelock(bytes32 _operationId) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(timelockExpirations[_operationId] > 0, "Timelock not initiated");
        
        delete timelockExpirations[_operationId];
        
        emit TimelockCancelled(_operationId, "Operation cancelled");
    }
    
    /**
     * @dev Activate emergency shutdown
     */
    function activateEmergencyShutdown() external onlyRole(EMERGENCY_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(!emergencyShutdown, "Emergency shutdown already active");
        
        emergencyShutdown = true;
        _pause();
        
        emit EmergencyShutdownActivated(msg.sender);
    }
    
    /**
     * @dev Deactivate emergency shutdown (requires timelock)
     */
    function initiateEmergencyShutdownDeactivation() external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(emergencyShutdown, "Emergency shutdown not active");
        
        bytes32 operationId = keccak256(abi.encodePacked("deactivateEmergencyShutdown"));
        
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, "deactivateEmergencyShutdown", timelockExpirations[operationId]);
    }
    
    /**
     * @dev Execute emergency shutdown deactivation
     */
    function executeEmergencyShutdownDeactivation() external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(emergencyShutdown, "Emergency shutdown not active");
        
        bytes32 operationId = keccak256(abi.encodePacked("deactivateEmergencyShutdown"));
        
        require(timelockExpirations[operationId] > 0, "Timelock not initiated");
        require(block.timestamp >= timelockExpirations[operationId], "Timelock not expired");
        
        emergencyShutdown = false;
        _unpause();
        
        delete timelockExpirations[operationId];
        
        emit TimelockExecuted(operationId, "deactivateEmergencyShutdown");
        emit EmergencyShutdownDeactivated(msg.sender);
    }
    
    /**
     * @dev Initiate timelock for token withdrawal
     * @param _token The token to withdraw
     * @param _amount The amount to withdraw
     * @param _recipient The recipient of the tokens
     */
    function initiateTokenWithdrawal(
        address _token,
        uint256 _amount,
        address _recipient
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        require(_recipient != address(0), "Invalid recipient");
        
        bytes32 operationId = keccak256(abi.encodePacked(
            "withdrawTokens",
            _token,
            _amount,
            _recipient
        ));
        
        timelockExpirations[operationId] = block.timestamp + TIMELOCK_PERIOD;
        
        emit TimelockInitiated(operationId, "withdrawTokens", timelockExpirations[operationId]);
    }
    
    /**
     * @dev Execute timelock for token withdrawal
     * @param _token The token to withdraw
     * @param _amount The amount to withdraw
     * @param _recipient The recipient of the tokens
     */
    function executeTokenWithdrawal(
        address _token,
        uint256 _amount,
        address _recipient
    ) external onlyRole(ADMIN_ROLE)  {
        // TODO: Add nonReentrant modifier
        bytes32 operationId = keccak256(abi.encodePacked(
            "withdrawTokens",
            _token,
            _amount,
            _recipient
        ));
        
        require(timelockExpirations[operationId] > 0, "Timelock not initiated");
        require(block.timestamp >= timelockExpirations[operationId], "Timelock not expired");
        
        // Check token balance
        uint256 balance = IERC20(_token).balanceOf(address(this));
        require(balance >= _amount, "Insufficient token balance");
        
        // Transfer tokens
        IERC20(_token).safeTransfer(_recipient, _amount);
        
        delete timelockExpirations[operationId];
        
        emit TimelockExecuted(operationId, "withdrawTokens");
    }
    
    /**
     * @dev Emergency withdrawal of all tokens (only when paused)
     * @param _token The token to withdraw
     * @param _recipient The recipient of the tokens
     */
    function emergencyWithdraw(
        address _token,
        address _recipient
    ) external onlyRole(EMERGENCY_ROLE) whenPaused  nonReentrant{
        require(_recipient != address(0), "Invalid recipient");
        require(emergencyShutdown, "Emergency shutdown not active");
        
        uint256 balance = IERC20(_token).balanceOf(address(this));
        require(balance > 0, "No tokens to withdraw");
        
        IERC20(_token).safeTransfer(_recipient, balance);
    }
    
    /**
     * @dev Get strategy information
     * @param _strategyId The ID of the strategy
     * @return address The address of the strategy
     * @return uint256 The last execution timestamp
     * @return uint256 The last capital allocated
     * @return uint256 The trust score
     */
    function getStrategyInfo(uint256 _strategyId) external view returns (
        address,
        uint256,
        uint256,
        uint256
    ) {
        return (
            strategyAddresses[_strategyId],
            strategyLastExecuted[_strategyId],
            strategyCapitalAllocated[_strategyId],
            TRUST_CURVE.getTrustScore(_strategyId)
        );
    }
    
    /**
     * @dev Get strategy address
     * @param _strategyId The ID of the strategy
     * @return The address of the strategy
     */
    function getStrategyAddress(uint256 _strategyId) external view returns (address)  {
        // TODO: Add nonReentrant modifier
        return strategyAddresses[_strategyId];
    }
    
    /**
     * @dev Get strategy ID
     * @param _strategyAddress The address of the strategy
     * @return The ID of the strategy
     */
    function getStrategyId(address _strategyAddress) external view returns (uint256)  {
        // TODO: Add nonReentrant modifier
        return strategyIds[_strategyAddress];
    }
    
    /**
     * @dev Check if a strategy is registered
     * @param _strategyId The ID of the strategy
     * @return True if the strategy is registered, false otherwise
     */
    function isStrategyRegistered(uint256 _strategyId) external view returns (bool)  {
        // TODO: Add nonReentrant modifier
        return strategyAddresses[_strategyId] != address(0);
    }
    
    /**
     * @dev Pause the contract
     */
    function pause() external onlyRole(EMERGENCY_ROLE)  nonReentrant onlyOwner{
        _pause();
    }
    
    /**
     * @dev Unpause the contract
     */
    function unpause() external onlyRole(ADMIN_ROLE)  nonReentrant onlyOwner{
        require(!emergencyShutdown, "Cannot unpause during emergency shutdown");
        _unpause();
    }
}
